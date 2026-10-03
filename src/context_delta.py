#!/usr/bin/env python3
"""
Context Broker — Delta-Packet Logic
Licensed under the MIT License
Copyright (c) Don Michael Feeney Jr.
"""

from collections.abc import Mapping
from typing import Any, Dict
import copy

_REQUIRED_FIELDS = (
    "schema_version", "context_id", "intent", "scope", "source", "actor",
    "payload", "created_at", "ttl", "expires_at",
)

def generate_delta(base_packet: Dict[str, Any], current_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a Delta-Packet containing only changed fields (excluding core/required fields)
    to save bandwidth, while maintaining the same context_id and refreshing expires_at.
    """
    if not isinstance(base_packet, Mapping) or not isinstance(current_state, Mapping):
        raise TypeError("base_packet and current_state must be mappings")

    base_id = base_packet.get("context_id")
    current_id = current_state.get("context_id")
    if not base_id or not current_id:
        raise ValueError("context_id must be present in both packets")
    if base_id != current_id:
        raise ValueError("base_packet and current_state must have the same context_id")

    schema_version = current_state.get("schema_version") or base_packet.get("schema_version")
    if not schema_version:
        raise ValueError("schema_version must be present in base_packet or current_state")

    resolved = {
        "schema_version": schema_version,
        "context_id": base_id,
    }
    for field in _REQUIRED_FIELDS[2:]:
        if field in current_state:
            resolved[field] = current_state[field]
        elif field in base_packet:
            resolved[field] = base_packet[field]
        else:
            raise ValueError(f"required field is missing from both packets: {field}")
    if any(resolved[field] is None for field in _REQUIRED_FIELDS):
        missing = next(field for field in _REQUIRED_FIELDS if resolved[field] is None)
        raise ValueError(f"required field must not be null: {missing}")

    delta_packet = copy.deepcopy(resolved)

    # We compare payload and other optional fields.
    if "permissions" in current_state and current_state["permissions"] != base_packet.get("permissions"):
        delta_packet["permissions"] = copy.deepcopy(current_state["permissions"])
    elif "permissions" not in current_state and "permissions" in base_packet:
        delta_packet["permissions"] = copy.deepcopy(base_packet["permissions"])

    if "annotations" in current_state and current_state["annotations"] != base_packet.get("annotations"):
        delta_packet["annotations"] = copy.deepcopy(current_state["annotations"])
    elif "annotations" not in current_state and "annotations" in base_packet:
        delta_packet["annotations"] = copy.deepcopy(base_packet["annotations"])

    # Note: signature and public_key_id are intentionally excluded from the delta.
    # The signature from current_state was computed over current_state's canonical JSON,
    # which differs from delta_packet's canonical JSON. The caller must re-sign the
    # delta_packet after generation if a signature is required.

    return delta_packet
