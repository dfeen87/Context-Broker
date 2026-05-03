"""
Unit tests for context_delta.py
"""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from context_delta import generate_delta


def _now_utc():
    return datetime.now(timezone.utc)


def _make_base(overrides=None):
    now = _now_utc()
    packet = {
        "schema_version": "1.0.0",
        "context_id": "ctx_test_001",
        "intent": "testing",
        "scope": "unit-tests",
        "source": "pytest",
        "actor": "tester@example.com",
        "payload": {"message": "original"},
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "ttl": "1h",
        "expires_at": (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        "permissions": ["read"],
    }
    if overrides:
        packet.update(overrides)
    return packet


class TestGenerateDeltaBasic(unittest.TestCase):
    def test_required_fields_always_present(self):
        base = _make_base()
        delta = generate_delta(base, base.copy())
        for field in ("schema_version", "context_id", "intent", "scope", "source", "actor",
                      "created_at", "ttl", "expires_at"):
            self.assertIn(field, delta)

    def test_context_id_mismatch_raises(self):
        base = _make_base()
        current = _make_base({"context_id": "ctx_different"})
        with self.assertRaises(ValueError):
            generate_delta(base, current)

    def test_schema_version_from_current_state(self):
        base = _make_base({"schema_version": "1.0.0"})
        current = _make_base({"schema_version": "1.5.0"})
        delta = generate_delta(base, current)
        self.assertEqual(delta["schema_version"], "1.5.0")

    def test_schema_version_from_base_when_not_in_current(self):
        base = _make_base({"schema_version": "1.0.0"})
        current = _make_base()
        del current["schema_version"]
        delta = generate_delta(base, current)
        self.assertEqual(delta["schema_version"], "1.0.0")

    def test_missing_schema_version_raises(self):
        base = _make_base()
        del base["schema_version"]
        current = _make_base()
        del current["schema_version"]
        with self.assertRaises(ValueError):
            generate_delta(base, current)


class TestGenerateDeltaPayload(unittest.TestCase):
    def test_changed_payload_included(self):
        base = _make_base()
        current = _make_base({"payload": {"message": "updated"}})
        delta = generate_delta(base, current)
        self.assertEqual(delta["payload"]["message"], "updated")

    def test_unchanged_payload_inherited_from_base(self):
        base = _make_base({"payload": {"message": "original"}})
        current = _make_base()
        del current["payload"]
        delta = generate_delta(base, current)
        self.assertEqual(delta["payload"]["message"], "original")


class TestGenerateDeltaPermissions(unittest.TestCase):
    def test_changed_permissions_included(self):
        base = _make_base({"permissions": ["read"]})
        current = _make_base({"permissions": ["read", "write"]})
        delta = generate_delta(base, current)
        self.assertEqual(delta["permissions"], ["read", "write"])

    def test_permissions_inherited_from_base_when_absent_in_current(self):
        """When current_state doesn't specify permissions, base permissions are preserved."""
        base = _make_base({"permissions": ["read", "summarize"]})
        current = _make_base()
        del current["permissions"]
        delta = generate_delta(base, current)
        self.assertEqual(delta["permissions"], ["read", "summarize"])

    def test_unchanged_permissions_not_duplicated(self):
        """When permissions are identical in both packets, they are not included (delta optimisation)."""
        base = _make_base({"permissions": ["read"]})
        current = _make_base({"permissions": ["read"]})
        delta = generate_delta(base, current)
        # permissions unchanged and current_state has them explicitly → not included
        self.assertNotIn("permissions", delta)


class TestGenerateDeltaAnnotations(unittest.TestCase):
    def test_changed_annotations_included(self):
        base = _make_base({"annotations": {"tag": "old"}})
        current = _make_base({"annotations": {"tag": "new"}})
        delta = generate_delta(base, current)
        self.assertEqual(delta["annotations"]["tag"], "new")

    def test_annotations_inherited_from_base_when_absent_in_current(self):
        base = _make_base({"annotations": {"note": "keep this"}})
        current = _make_base()
        delta = generate_delta(base, current)
        self.assertEqual(delta["annotations"]["note"], "keep this")


class TestGenerateDeltaSignature(unittest.TestCase):
    def test_signature_not_propagated(self):
        """Signatures from current_state must never be copied into the delta packet
        because they were computed over current_state's canonical JSON, not delta_packet's."""
        base = _make_base()
        current = _make_base()
        current["signature"] = "fakesig=="
        current["public_key_id"] = "fakepubkey=="
        delta = generate_delta(base, current)
        self.assertNotIn("signature", delta)
        self.assertNotIn("public_key_id", delta)

    def test_public_key_id_not_propagated(self):
        base = _make_base()
        current = _make_base()
        current["public_key_id"] = "fakepubkey=="
        delta = generate_delta(base, current)
        self.assertNotIn("public_key_id", delta)


class TestGenerateDeltaDeepCopy(unittest.TestCase):
    def test_payload_is_deep_copied(self):
        base = _make_base()
        current = _make_base({"payload": {"data": [1, 2, 3]}})
        delta = generate_delta(base, current)
        current["payload"]["data"].append(4)
        self.assertEqual(delta["payload"]["data"], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
