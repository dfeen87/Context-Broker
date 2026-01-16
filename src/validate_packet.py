#!/usr/bin/env python3
"""
Context Broker — Packet Validator (Reference)
Production-hardened validator for ContextPacket v1.0.0

- Validates JSON against the canonical schema
- Enforces time constraints (created_at, ttl, expires_at)
- Rejects expired packets (with optional clock-skew tolerance)
- Emits machine-readable JSON output (good for CI)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from jsonschema import Draft7Validator, FormatChecker


# ---------- Logging ----------

LOG = logging.getLogger("context-broker.validator")


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )


# ---------- Errors / Result Model ----------

@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: str = ""


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    schema_version: Optional[str]
    issues: Tuple[ValidationIssue, ...]


# ---------- Helpers ----------

_DURATION_RE = re.compile(r"^\s*(\d+)\s*([smhd])\s*$", re.IGNORECASE)


def parse_duration(duration: str) -> timedelta:
    """
    Parse simple TTL strings like: '30m', '2h', '15s', '7d'
    """
    m = _DURATION_RE.match(duration or "")
    if not m:
        raise ValueError("ttl must match <int><s|m|h|d> (e.g., '30m', '2h')")
    value = int(m.group(1))
    unit = m.group(2).lower()

    if value <= 0:
        raise ValueError("ttl must be positive")

    if unit == "s":
        return timedelta(seconds=value)
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)

    # unreachable due to regex
    raise ValueError("unsupported ttl unit")


def parse_rfc3339(dt_str: str) -> datetime:
    """
    Parse ISO 8601 date-time. Requires timezone offset or Z.
    """
    if not isinstance(dt_str, str) or not dt_str.strip():
        raise ValueError("datetime must be a non-empty string")

    s = dt_str.strip()

    # Accept trailing Z
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        raise ValueError(f"invalid date-time format: {e}") from e

    if dt.tzinfo is None:
        raise ValueError("date-time must include timezone (e.g., 'Z' or '+00:00')")

    return dt.astimezone(timezone.utc)


def load_json(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(f"failed to read packet file: {e}") from e

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"invalid JSON: {e}") from e

    if not isinstance(data, dict):
        raise RuntimeError("packet JSON must be an object")

    return data


def load_schema(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(f"failed to read schema file: {e}") from e

    try:
        schema = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"invalid schema JSON: {e}") from e

    if not isinstance(schema, dict):
        raise RuntimeError("schema JSON must be an object")

    return schema


def _json_path(err) -> str:
    """
    Convert jsonschema error paths to a readable dotted path.
    """
    parts = []
    for p in list(err.absolute_path):
        if isinstance(p, int):
            parts.append(f"[{p}]")
        else:
            parts.append(str(p))
    # join with dots, but keep [idx] glued
    out = ""
    for part in parts:
        if part.startswith("["):
            out += part
        else:
            out += ("." if out else "") + part
    return out


# ---------- Core Validation ----------

def validate_packet(
    packet: Dict[str, Any],
    schema: Dict[str, Any],
    *,
    now_utc: datetime,
    clock_skew: timedelta,
    allow_future_created_at: timedelta,
) -> ValidationResult:
    issues = []

    # 1) Schema validation (structure, required fields, types, formats)
    validator = Draft7Validator(schema, format_checker=FormatChecker())
    schema_errors = sorted(validator.iter_errors(packet), key=lambda e: str(e.path))

    for err in schema_errors:
        issues.append(
            ValidationIssue(
                code="SCHEMA_VIOLATION",
                message=err.message,
                path=_json_path(err),
            )
        )

    schema_version = packet.get("schema_version") if isinstance(packet.get("schema_version"), str) else None

    # If schema errors exist, we still try some semantic checks only if required fields exist.
    # This helps CI users see all actionable problems at once.
    def has_fields(*keys: str) -> bool:
        return all(k in packet for k in keys)

    # 2) Time semantics
    if has_fields("created_at", "ttl", "expires_at"):
        try:
            created_at = parse_rfc3339(packet["created_at"])
        except Exception as e:
            issues.append(ValidationIssue(code="TIME_INVALID_CREATED_AT", message=str(e), path="created_at"))
            created_at = None

        try:
            ttl_td = parse_duration(packet["ttl"])
        except Exception as e:
            issues.append(ValidationIssue(code="TIME_INVALID_TTL", message=str(e), path="ttl"))
            ttl_td = None

        try:
            expires_at = parse_rfc3339(packet["expires_at"])
        except Exception as e:
            issues.append(ValidationIssue(code="TIME_INVALID_EXPIRES_AT", message=str(e), path="expires_at"))
            expires_at = None

        # Only proceed if all parsed
        if created_at and ttl_td and expires_at:
            # 2a) expires_at must equal created_at + ttl (within skew)
            expected = created_at + ttl_td
            delta = abs((expires_at - expected).total_seconds())
            if delta > max(clock_skew.total_seconds(), 1.0):
                issues.append(
                    ValidationIssue(
                        code="TIME_MISMATCH",
                        message=(
                            "expires_at does not match created_at + ttl within allowed tolerance "
                            f"(expected={expected.isoformat().replace('+00:00','Z')}, "
                            f"got={expires_at.isoformat().replace('+00:00','Z')}, "
                            f"tolerance={clock_skew})"
                        ),
                        path="expires_at",
                    )
                )

            # 2b) created_at should not be unreasonably in the future (allow small skew)
            if created_at - now_utc > allow_future_created_at:
                issues.append(
                    ValidationIssue(
                        code="TIME_CREATED_AT_IN_FUTURE",
                        message=(
                            "created_at is too far in the future "
                            f"(created_at={created_at.isoformat().replace('+00:00','Z')}, "
                            f"now={now_utc.isoformat().replace('+00:00','Z')}, "
                            f"allowance={allow_future_created_at})"
                        ),
                        path="created_at",
                    )
                )

            # 2c) reject expired context (with skew)
            if now_utc - expires_at > clock_skew:
                issues.append(
                    ValidationIssue(
                        code="TIME_EXPIRED",
                        message=(
                            "context packet is expired "
                            f"(expires_at={expires_at.isoformat().replace('+00:00','Z')}, "
                            f"now={now_utc.isoformat().replace('+00:00','Z')}, "
                            f"skew={clock_skew})"
                        ),
                        path="expires_at",
                    )
                )
    else:
        # If missing fields, schema validation will already have flagged it.
        pass

    ok = len(issues) == 0
    return ValidationResult(ok=ok, schema_version=schema_version, issues=tuple(issues))


# ---------- CLI ----------

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="context-broker-validate",
        description="Validate a Context Broker ContextPacket against schema and time semantics.",
    )
    parser.add_argument("packet", type=str, help="Path to a context packet JSON file.")
    parser.add_argument(
        "--schema",
        type=str,
        default=str(Path("schemas") / "context_packet.schema.v1.0.0.json"),
        help="Path to the JSON Schema file (default: schemas/context_packet.schema.v1.0.0.json).",
    )
    parser.add_argument(
        "--clock-skew",
        type=str,
        default="60s",
        help="Allowed clock skew tolerance (default: 60s).",
    )
    parser.add_argument(
        "--allow-future-created-at",
        type=str,
        default="5m",
        help="Allowed future offset for created_at (default: 5m).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="json",
        choices=["json", "text"],
        help="Output format (default: json).",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")

    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    packet_path = Path(args.packet)
    schema_path = Path(args.schema)

    try:
        clock_skew = parse_duration(args.clock_skew)
        allow_future = parse_duration(args.allow_future_created_at)
    except Exception as e:
        print(json.dumps({"ok": False, "issues": [{"code": "ARG_INVALID", "message": str(e), "path": ""}]}))
        return 2

    try:
        packet = load_json(packet_path)
        schema = load_schema(schema_path)
    except Exception as e:
        out = {"ok": False, "issues": [{"code": "IO_ERROR", "message": str(e), "path": ""}]}
        print(json.dumps(out, indent=2))
        return 2

    now_utc = datetime.now(timezone.utc)

    result = validate_packet(
        packet,
        schema,
        now_utc=now_utc,
        clock_skew=clock_skew,
        allow_future_created_at=allow_future,
    )

    if args.output == "json":
        out = {
            "ok": result.ok,
            "schema_version": result.schema_version,
            "issues": [
                {"code": i.code, "message": i.message, "path": i.path} for i in result.issues
            ],
        }
        print(json.dumps(out, indent=2))
    else:
        if result.ok:
            print("OK: packet is valid")
        else:
            print("FAIL: packet is invalid")
            for i in result.issues:
                loc = f" ({i.path})" if i.path else ""
                print(f"- {i.code}{loc}: {i.message}")

    # Exit codes:
    # 0 = valid
    # 1 = invalid (schema/semantic)
    # 2 = tooling error (args/io)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
