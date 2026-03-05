# Changelog

All notable changes to Context Broker are documented in this file.

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
