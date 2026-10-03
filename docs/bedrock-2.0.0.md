# Context Broker 2.0.0 — BEDROCK Engineering Report

## Release rationale and preserved architecture

Version 2.0.0 establishes a hardened trust-boundary baseline. The existing
architecture remains intact: immutable versioned JSON Schemas define packets,
the Python validator remains the reference implementation, the Go validator
remains a portable peer, and delta generation remains a small stateless helper.
The major version is warranted by stricter malformed-input, configuration, and
schema behavior—not by a redesign.

Context Broker follows Semantic Versioning for its packet schema. Schema 2.0.0
is intentionally incompatible only where previous inputs were ambiguous or
violated existing integrity intent. Published 0.1, 1.0.0, 1.5.0, and 1.6.0
schemas remain unchanged and addressable through the schema registry.

## Invariant map and confirmed defects

| Behavior | Required invariant | Previous enforcement/test | 2.0.0 guarantee |
|---|---|---|---|
| JSON ingestion | One finite, unambiguous JSON object of bounded size | Python accepted duplicate keys and `NaN`; Go had no size bound | Both reject duplicates; Python rejects non-standard constants; packet reads are bounded |
| Time validation API | Clock is timezone-aware and tolerances are non-negative | Assumed; naive clocks crashed and negative values could weaken checks | Deterministic `CONFIG_INVALID` result before packet evaluation |
| Integrity fields | Signature and public key are paired and non-empty | Runtime-only and partially tested | Schema and runtime fail closed |
| Delta generation | Both identities exist and match; every required field resolves | Missing data leaked `KeyError`/`AttributeError` | Deterministic `TypeError`/`ValueError` before a candidate is returned |
| Delta ownership | Returned candidate cannot alias mutable input state | Payload paths were tested indirectly | Entire resolved candidate is deep-copied and regression-tested |
| Expiration CI | An expired packet must make validation fail | Shell expression always succeeded | Negative smoke step fails if expired input is accepted |
| Go implementation | Checked-in implementation remains buildable and tested | No tracked module metadata or Go CI | Module metadata, unit tests, and required CI execution |

The untested invariants discovered were strict JSON lexical handling, nested
duplicate detection, validation-configuration safety, missing delta identity,
missing inherited fields, and actual execution of Go tests. Regression tests
now cover each of these boundaries, including trailing JSON and inherited
payload ownership.

## Failure, state, and trust semantics

Loading is now read-then-validate: no parsed object is returned until the byte
limit, UTF-8, JSON grammar, duplicate-key, and top-level-object checks pass.
Validation rejects invalid clock configuration before semantic comparisons, so
failure produces a stable result rather than a partial issue list or exception.
Delta construction resolves a candidate, verifies required values, deep-copies
it, and only then returns it. These functions do not persist state, so there is
no database rollback boundary; atomic candidate publication is the relevant
state guarantee.

Schema 2.0.0 makes integrity-field pairing explicit, rejects empty integrity
values, and rejects duplicate or empty permissions. Unsigned packets remain
valid by design: signatures are optional provenance evidence, not an
authorization system. When evidence is supplied, malformed evidence fails
closed. Context Broker still does not implement routing authorization or policy.

## Cross-component and CI contracts

Python and Go now share the one-object, no-duplicate-keys, one-megabyte packet
boundary. CI compiles all Python files, runs all Python tests, runs all Go tests,
validates a current-schema packet, and proves an expired packet is rejected.
This closes the prior gap where registered tests could be bypassed and the
negative smoke command could never fail the job.

No external related repository or live broker is required by this repository,
and none was available or needed for this audit. The only runtime integrations
are `jsonschema`, `cryptography`, and the Go JSON Schema module; unavailable
dependencies fail installation/build rather than silently reducing validation.

## Compatibility and rejected behavior

Version 2.0.0 rejects duplicate JSON names, Python-only `NaN`/infinity tokens,
multiple JSON documents, invalid clock configuration, duplicate/empty
permissions, unpaired/empty integrity fields, and incomplete delta inputs.
These are deliberate behavioral-contract changes because accepting ambiguity at
an auditable context boundary contradicts deterministic validation. Consumers
that need the old packet shape may continue selecting an immutable v1 schema,
but strict loader and safe configuration behavior apply to the validator itself.

## Risks investigated, limitations, and external validation

- Ed25519 verification is tested for malformed, incomplete, and tampered
  evidence. However, `public_key_id` currently carries raw public-key bytes; no
  key registry, revocation, identity binding, or authorization policy exists.
- Python and Go use their standard sorted JSON encoders for signatures. Numeric
  spellings can canonicalize differently across languages, so cross-language
  signatures require a future explicitly standardized canonicalization profile.
- File size is bounded, but deeply nested JSON may still consume significant
  parser resources. Deployments should also enforce process and request limits.
- Delta generation constructs packets; callers must validate and re-sign the
  result before routing. It is not persistence or conflict-resolution logic.
- Tests establish software behavior only. Production adopters still need
  integration tests for clocks, key custody, storage, routing policy, deployment
  resource limits, and incident/audit procedures. This release is not security
  certification or approval for any high-consequence environment.
