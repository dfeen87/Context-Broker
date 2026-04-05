# Changelog

All notable changes to Context Broker are documented in this file.

## [1.4.1] — 2026-04-05

### Fixed
- Example valid packet: update `created_at`/`ttl`/`expires_at` so the packet is not expired at install time (was 2024-01-01 with 2h TTL; now 2026-04-05 with 365d TTL)
- CONTRIBUTING: fix incorrect test filename reference (`tests/test_validator.py` → `tests/test_validate_packet.py`)

### Changed
- README: clarify intro description ("non-commercial-licensed" → "non-commercial")
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
