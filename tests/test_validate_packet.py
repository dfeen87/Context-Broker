"""
Unit tests for validate_packet.py
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validate_packet import (
    MAX_PACKET_BYTES,
    MAX_TTL,
    ValidationIssue,
    ValidationResult,
    load_json,
    parse_duration,
    parse_rfc3339,
    validate_packet,
)

from jsonschema import Draft7Validator, FormatChecker

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "context_packet.schema.v1.0.0.json"
_FORMAT_CHECKER = FormatChecker()


def _load_schema():
    with _SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _make_validator():
    schema = _load_schema()
    return Draft7Validator(schema, format_checker=_FORMAT_CHECKER)


def _now_utc():
    return datetime.now(timezone.utc)


def _make_packet(**overrides):
    now = _now_utc()
    packet = {
        "schema_version": "1.0.0",
        "context_id": "ctx_test_001",
        "intent": "testing",
        "scope": "unit-tests",
        "source": "pytest",
        "actor": "tester@example.com",
        "payload": {"message": "test"},
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "ttl": "1h",
        "expires_at": (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        "permissions": ["read"],
    }
    packet.update(overrides)
    return packet


def _validate(packet, now_utc=None):
    validator = _make_validator()
    return validate_packet(
        packet,
        validator=validator,
        now_utc=now_utc or _now_utc(),
        clock_skew=timedelta(seconds=60),
        allow_future_created_at=timedelta(minutes=5),
    )


class TestParseDuration(unittest.TestCase):
    def test_valid_minutes(self):
        self.assertEqual(parse_duration("30m"), timedelta(minutes=30))

    def test_valid_hours(self):
        self.assertEqual(parse_duration("2h"), timedelta(hours=2))

    def test_valid_seconds(self):
        self.assertEqual(parse_duration("15s"), timedelta(seconds=15))

    def test_valid_days(self):
        self.assertEqual(parse_duration("7d"), timedelta(days=7))

    def test_case_insensitive(self):
        self.assertEqual(parse_duration("1H"), timedelta(hours=1))

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_zero_value(self):
        with self.assertRaises(ValueError):
            parse_duration("0s")

    def test_invalid_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("10x")

    def test_non_numeric(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")


class TestParseRfc3339(unittest.TestCase):
    def test_valid_z_suffix(self):
        dt = parse_rfc3339("2024-01-01T00:00:00Z")
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_valid_offset(self):
        dt = parse_rfc3339("2024-01-01T00:00:00+00:00")
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_missing_timezone(self):
        with self.assertRaises(ValueError):
            parse_rfc3339("2024-01-01T00:00:00")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_rfc3339("")

    def test_non_string(self):
        with self.assertRaises(ValueError):
            parse_rfc3339(None)


class TestValidPacket(unittest.TestCase):
    def test_valid_packet_passes(self):
        result = _validate(_make_packet())
        self.assertTrue(result.ok)
        self.assertEqual(len(result.issues), 0)

    def test_schema_version_returned(self):
        result = _validate(_make_packet())
        self.assertEqual(result.schema_version, "1.0.0")


class TestExpiredPacket(unittest.TestCase):
    def test_expired_packet_fails(self):
        past = datetime(2000, 1, 1, tzinfo=timezone.utc)
        packet = {
            "schema_version": "1.0.0",
            "context_id": "ctx_expired",
            "intent": "testing",
            "scope": "unit-tests",
            "source": "pytest",
            "actor": "tester@example.com",
            "payload": {"msg": "x"},
            "created_at": "2000-01-01T00:00:00Z",
            "ttl": "1h",
            "expires_at": "2000-01-01T01:00:00Z",
            "permissions": [],
        }
        result = _validate(packet)
        codes = [i.code for i in result.issues]
        self.assertIn("TIME_EXPIRED", codes)
        self.assertFalse(result.ok)


class TestMissingRequiredFields(unittest.TestCase):
    def test_missing_actor_produces_schema_violation(self):
        packet = _make_packet()
        del packet["actor"]
        result = _validate(packet)
        codes = [i.code for i in result.issues]
        self.assertIn("SCHEMA_VIOLATION", codes)
        self.assertFalse(result.ok)

    def test_empty_actor_produces_schema_violation(self):
        packet = _make_packet(actor="")
        result = _validate(packet)
        codes = [i.code for i in result.issues]
        self.assertIn("SCHEMA_VIOLATION", codes)
        self.assertFalse(result.ok)

    def test_empty_context_id_produces_schema_violation(self):
        packet = _make_packet(context_id="")
        result = _validate(packet)
        codes = [i.code for i in result.issues]
        self.assertIn("SCHEMA_VIOLATION", codes)
        self.assertFalse(result.ok)


class TestTimeMismatch(unittest.TestCase):
    def test_ttl_expires_at_mismatch(self):
        now = _now_utc()
        packet = _make_packet(
            created_at=now.isoformat().replace("+00:00", "Z"),
            ttl="1h",
            # expires_at is 2h after created_at, but ttl says 1h
            expires_at=(now + timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
        )
        result = _validate(packet)
        codes = [i.code for i in result.issues]
        self.assertIn("TIME_MISMATCH", codes)


class TestFutureCreatedAt(unittest.TestCase):
    def test_future_created_at(self):
        future = _now_utc() + timedelta(hours=2)
        packet = _make_packet(
            created_at=future.isoformat().replace("+00:00", "Z"),
            expires_at=(future + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        )
        result = _validate(packet)
        codes = [i.code for i in result.issues]
        self.assertIn("TIME_CREATED_AT_IN_FUTURE", codes)


class TestTtlTooLong(unittest.TestCase):
    def test_ttl_exceeds_max(self):
        now = _now_utc()
        # 366 days > MAX_TTL (365 days)
        expires = now + timedelta(days=366)
        packet = _make_packet(
            created_at=now.isoformat().replace("+00:00", "Z"),
            ttl="366d",
            expires_at=expires.isoformat().replace("+00:00", "Z"),
        )
        result = _validate(packet)
        codes = [i.code for i in result.issues]
        self.assertIn("TTL_TOO_LONG", codes)

    def test_ttl_at_max_is_ok(self):
        now = _now_utc()
        expires = now + timedelta(days=365)
        packet = _make_packet(
            created_at=now.isoformat().replace("+00:00", "Z"),
            ttl="365d",
            expires_at=expires.isoformat().replace("+00:00", "Z"),
        )
        result = _validate(packet)
        codes = [i.code for i in result.issues]
        self.assertNotIn("TTL_TOO_LONG", codes)


class TestFileSizeGuard(unittest.TestCase):
    def test_oversized_file_raises(self):
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".json", delete=False
        ) as f:
            # Write a file larger than MAX_PACKET_BYTES
            f.write(b"x" * (MAX_PACKET_BYTES + 1))
            tmp_path = Path(f.name)
        try:
            with self.assertRaises(RuntimeError) as ctx:
                load_json(tmp_path)
            self.assertIn("exceeds maximum size", str(ctx.exception))
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_valid_size_file_loads(self):
        now = _now_utc()
        packet = _make_packet(
            created_at=now.isoformat().replace("+00:00", "Z"),
            expires_at=(now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(packet, f)
            tmp_path = Path(f.name)
        try:
            loaded = load_json(tmp_path)
            self.assertEqual(loaded["context_id"], packet["context_id"])
        finally:
            tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
