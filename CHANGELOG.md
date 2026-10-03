# Changelog

All notable changes to Context Broker are documented in this file.

## [2.0.0] - 2026-10-03

### Security
- Reject duplicate JSON object keys and non-standard numeric constants at the
  Python trust boundary; reject duplicate keys and oversized packets in Go.
- Fail closed when library callers provide naive clocks or negative tolerances.
- Require paired integrity fields and non-empty, bounded permission and
  integrity strings in the immutable v2.0.0 schema.

### Fixed
- Convert malformed delta inputs and missing required state into deterministic
  exceptions rather than incidental `AttributeError` or `KeyError` failures.
- Deep-copy the complete resolved delta candidate before returning it.
- Make the expired-packet CI check capable of failing the workflow.

### Added
- Published `schemas/context_packet.schema.v2.0.0.json` while retaining all
  earlier immutable schemas for compatibility.
- Added Go module metadata and executable Go regression tests.
- Added the BEDROCK 2.0 engineering report and explicit validation contract.

### Changed
- CI now requires the Python and Go test suites and compiles all Python source.
- Version 2.0.0 is a strict-SemVer release: malformed JSON formerly accepted
  by the Python loader, unsafe validation configuration, duplicate permissions,
  and unpaired integrity fields are now rejected.

## [1.6.0] - 2026-05-03

### Added
- Created `schemas/context_packet.schema.v1.6.0.json` schema version 1.6.0.

### Changed
- Updated validator and context delta references to schema version 1.6.0.
- Updated CITATION.cff version to 1.6.0 and date-released to 2026-05-03.
- Updated README documentation and unit test suite for version 1.6.0.

## [1.5.0] - 2026-05-03

### Added
- Semantic Schema Registry to support multiple schema versions dynamically.
- Cryptographic Provenance (Integrity) using Ed25519 signatures.
- Delta-Packet & Persistence Logic to generate context deltas minimizing bandwidth overhead.
- Extensive Edge-Case & Fuzz testing logic for time bounds and cryptographic aspects.

## [1.4.1] — 2026-04-05

### Fixed
- Example valid packet: update `created_at`/`ttl`/`expires_at` so the packet is not expired at install time (was 2024-01-01 with 2h TTL; now 2026-04-05 with 365d TTL)
- CONTRIBUTING: fix incorrect test filename reference (`tests/test_validator.py` → `tests/test_validate_packet.py`)

### Changed
- README: clarify intro description (licensed under the MIT License)
- README: fix TOC entry "Acknowledgements" → "Acknowledgments" to match section header
- README: fix TOC entry "Closing note" → "Closing Note" to match section header
- CITATION.cff: update version and date-released to 1.4.1 / 2026-04-05

## [1.4.0] — 2026-03-05

### Security
- Schema: enforce `minLength` on all required string fields; add `maxLength` bounds
- Schema: add `pattern` constraint to `ttl` field
- Validator: enforce maximum TTL ceiling (365 days)
- Validator: add file-size guard before JSON parsing

### Fixed
- Python validator: fix truthiness check on parsed time values (use explicit `is not None`)
- Go validator: fix variable shadowing in `fail()` function
- Python validator: remove unused `schema` parameter from `validate_packet()`
- Python validator: normalize JSON output indentation across all error paths
- Fix license references in CITATION.cff, CONTRIBUTING.md, and docs to match actual LICENSE
- Fix example valid packet to use realistic TTL (was 55 years; now 2 hours)

### Added
- Unit test suite (`tests/test_validate_packet.py`)
- This changelog

### Changed
- Go validator success output now includes `schema_version` for cross-implementation parity
- CI workflows use dynamic packet paths instead of hardcoded `/tmp/` paths
- Updated CITATION.cff version to 1.4.0

## [1.2.0] — 2026-02-08

- Initial tracked release with schema v1.0.0 and reference validators
