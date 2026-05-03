#!/usr/bin/env python3
"""
Context Broker — Delta-Packet Logic
License: MIT
"""

from typing import Any, Dict
from datetime import datetime, timezone
import copy

def generate_delta(base_packet: Dict[str, Any], current_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a Delta-Packet containing only changed fields (excluding core/required fields)
    to save bandwidth, while maintaining the same context_id and refreshing expires_at.
    """
    if base_packet.get("context_id") != current_state.get("context_id"):
        raise ValueError("base_packet and current_state must have the same context_id")

    schema_version = current_state.get("schema_version") or base_packet.get("schema_version")
    if not schema_version:
        raise ValueError("schema_version must be present in base_packet or current_state")

    delta_packet = {
        "schema_version": schema_version,
        "context_id": base_packet["context_id"],
        "intent": current_state.get("intent", base_packet["intent"]),
        "scope": current_state.get("scope", base_packet["scope"]),
        "source": current_state.get("source", base_packet["source"]),
        "actor": current_state.get("actor", base_packet["actor"]),
        "created_at": current_state.get("created_at", base_packet["created_at"]),
        "ttl": current_state.get("ttl", base_packet["ttl"])
    }

    # Recalculate expires_at (if parsing and computing isn't strictly requested,
    # we just take the current state's expires_at, but we'll assume it's refreshed in current_state)
    delta_packet["expires_at"] = current_state.get("expires_at", base_packet["expires_at"])

    # We compare payload and other optional fields.
    if "payload" in current_state and current_state["payload"] != base_packet.get("payload"):
        delta_packet["payload"] = copy.deepcopy(current_state["payload"])
    elif "payload" in base_packet:
        # Keep base payload if no change and it is required by schema,
        # Schema v1.5.0 requires 'payload'.
        delta_packet["payload"] = copy.deepcopy(base_packet["payload"])

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
