# RFC-0001: Context Packet Schema Evolution

## Status
Proposed

## Abstract
This document defines how the Context Broker ContextPacket schema evolves over time without compromising auditability, safety, or interoperability.

## Motivation
Context packets are integrity-critical artifacts. Silent or ad-hoc evolution introduces ambiguity, breaks audit trails, and undermines trust.

Schema evolution must therefore be:
- Explicit
- Versioned
- Backward-aware

## Versioning Rules

- Schema versions follow `MAJOR.MINOR.PATCH`
- Current version: **1.0.0**

### PATCH changes MAY:
- Fix typos or clarify wording
- Add non-authoritative metadata
- Tighten validation rules (non-breaking)

### MINOR changes MAY:
- Add optional fields
- Add non-authoritative metadata

### MAJOR changes MUST:
- Change required fields
- Change semantic meaning of fields
- Alter ALCOA or time guarantees

MAJOR changes require:
- New schema file
- Migration notes
- Explicit incompatibility statement

## Immutability Principle

Published schema versions are immutable.

A schema file MUST NOT be modified once released.
Corrections require a new version.

## ALCOA Preservation

No evolution may:
- Remove attribution requirements
- Permit timeless context
- Allow silent mutation of payload
- Introduce implicit inference

ALCOA is considered **foundational**, not optional.

## Non-Goals

This RFC explicitly does not define:
- AI orchestration semantics
- Policy engines
- Routing logic
- Enforcement mechanisms beyond validation

Those concerns are out of scope.

## Rationale

This evolution model mirrors successful infrastructure standards:
- TCP/IP
- JSON Schema
- OpenTelemetry

Stability at the boundary enables innovation above it.

## Conclusion

Context Broker evolves cautiously by design.
Safety, auditability, and predictability take precedence over feature velocity.
