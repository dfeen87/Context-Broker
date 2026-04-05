# Context Broker

[![CI](https://github.com/dfeen87/Context-Broker/actions/workflows/ci.yml/badge.svg)](https://github.com/dfeen87/Context-Broker/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**Context Broker** is a minimal, non-commercial reference implementation for mediating context safely between devices, applications, and AI systems.

It treats context as a **time-bound, attributable artifact**, not an ambient data stream.

---

## Table of Contents

- [The Problem](#the-problem)
- [What Context Broker Is](#what-context-broker-is)
- [What Context Broker Is Not](#what-context-broker-is-not)
- [Quick Start](#quick-start)
- [Core Principles](#core-principles)
- [How Context Broker Fits in Larger Systems](#how-context-broker-fits-in-larger-systems)
- [Illustrative Example](#illustrative-example-conceptual)
- [Use Cases](#use-cases)
- [Design Goals](#design-goals)
- [Project Status](#project-status)
- [Documentation](#documentation)
- [Continuous Integration](#continuous-integration)
- [Philosophy](#philosophy)
- [Community](#community)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Closing Note](#closing-note)

---

## The Problem

Modern AI workflows are fragmented across:

- 🌐 **Browsers** (ChatGPT web, Claude, Perplexity)
- 💻 **IDEs** (VS Code, Cursor, JetBrains)
- 📱 **Mobile devices** (iOS, Android)
- 🔧 **Internal tools** (Slack, Notion, custom dashboards)
- 🤖 **Multiple AI systems** (proprietary and open-source)

**Context is constantly:**
- ❌ Lost during transitions
- ❌ Duplicated across tools
- ❌ Inferred without consent
- ❌ Silently persisted beyond its useful life

### Where Failures Actually Happen

Most interoperability failures do **not** occur at the AI model layer.

They occur at the **context boundary**—the moment when context moves between systems.

**Context Broker exists to stabilize that boundary.**

---

## What Context Broker Is

Context Broker provides a **disciplined substrate for context exchange**:

### Core Capabilities

✅ **Explicit context promotion** — no silent harvesting  
✅ **ALCOA-compliant integrity** — attributable, legible, contemporaneous, original, accurate  
✅ **Mandatory time bounds** — every context packet expires automatically  
✅ **Human-legible packets** — inspect and audit all context flow  
✅ **Vendor-neutral design** — works with any AI system

### Design Philosophy

Context Broker is designed to be:

- 🎯 **Neutral** — no vendor lock-in
- 🔮 **Predictable** — deterministic routing and expiration
- 🔍 **Inspectable** — full visibility into context flow
- 🛡️ **Safe by construction** — explicit constraints prevent misuse

---

## What Context Broker Is Not

Context Broker intentionally does **not** implement:

| What It Doesn't Do | Why |
|-------------------|-----|
| ❌ AI model orchestration | Belongs up-stack |
| ❌ Autonomous agents | Separate concern |
| ❌ Multi-model synthesis | Policy layer responsibility |
| ❌ Vendor-specific integrations | Stays neutral |
| ❌ Behavioral inference | No surveillance patterns |

> **Those concerns belong up-stack.**

Context Broker remains valuable by **staying small and focused**.

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/dfeen87/Context-Broker.git
cd Context-Broker

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

**Validate a context packet:**

```bash
# Validate a valid packet
python src/validate_packet.py examples/packet.valid.json

# Check an expired packet
python src/validate_packet.py examples/packet.expired.json

# Get help
python src/validate_packet.py --help
```

**Example output (valid packet):**

```bash
python src/validate_packet.py examples/packet.valid.json --output text
# Output: OK: packet is valid
```

**Example output (expired packet):**

```bash
python src/validate_packet.py examples/packet.expired.json --output text
# Output: FAIL: packet is invalid
# - TIME_EXPIRED (expires_at): context packet is expired...
```

### Project Structure

```
Context-Broker/
├── src/                          # Validator implementations
│   ├── validate_packet.py        # Python validator (reference)
│   └── validate_packet.go        # Go validator
├── schemas/                      # JSON Schema definitions
│   ├── context_packet.schema.v1.0.0.json  # Current schema
│   └── context_packet.schema.v0.1.json    # Legacy schema
├── examples/                     # Sample context packets
│   ├── packet.valid.json         # Valid packet example
│   └── packet.expired.json       # Expired packet example
├── docs/                         # Design documentation
│   ├── alcoa-and-time.md         # ALCOA principles and time semantics
│   ├── interoperability-notes.md # Multi-vendor integration guidance
│   └── rfc-0001-context-packet-evolution.md
└── README.md                     # This file
```

---

## Core Principles

Context Broker enforces two non-negotiable constraints:

### 1. ALCOA Integrity

Context packets must be:

| Principle | What It Means |
|-----------|---------------|
| **A**ttributable | Clear source and actor—no anonymous context |
| **L**egible | Human-readable and inspectable—no opaque formats |
| **C**ontemporaneous | Created at the time of relevance—no retroactive context |
| **O**riginal | Immutable, append-only—no silent mutations |
| **A**ccurate | No silent merging or cross-contamination |

📖 **Learn more:** [`docs/alcoa-and-time.md`](docs/alcoa-and-time.md)

---

### 2. Time as a First-Class Constraint

Every context packet includes:

```json
{
  "created_at": "2025-12-17T23:41:00Z",
  "ttl": "2h",
  "expires_at": "2025-12-18T01:41:00Z"
}
```

**Routing Rules:**
- ⏱️ Expired context is **rejected** (not downranked)
- ⏱️ No TTL → no routing
- ⏱️ Automatic purging prevents stale context accumulation

> **Time is not metadata—it is control.**

---

## How Context Broker Fits in Larger Systems

Context Broker is a **foundational layer**, not a complete platform.

### Typical System Architecture

```
┌─────────────────────────────────────┐
│  AI Orchestration / Synthesis       │  ← LangChain, AutoGPT, custom logic
├─────────────────────────────────────┤
│  Policy Engines / Model Routers     │  ← Business rules, cost optimization
├─────────────────────────────────────┤
│  Context Broker                     │  ← THIS LAYER
│  (ALCOA + Time-Bound Context)       │
├─────────────────────────────────────┤
│  Devices / Applications             │  ← Browsers, IDEs, chat apps
└─────────────────────────────────────┘
```

**Key Insight:** Context Broker **stabilizes** higher-level orchestration without competing with it.

📖 **Learn more:** [`docs/interoperability-notes.md`](docs/interoperability-notes.md)

---

## Illustrative Example (Conceptual)

> **Note:** The following examples are illustrative and not tied to a production API. They demonstrate the design principles, not a stable implementation.

### Example: Promoting Context

```javascript
// Conceptual example of context promotion
const packet = {
  intent: "research",
  scope: "project_x",
  source: "browser",
  actor: "user@example.com",
  payload: {
    url: "https://example.com/article",
    selection: "Relevant text the user highlighted",
    timestamp: "2025-12-17T23:41:00Z"
  },
  ttl: "2h",  // Expires in 2 hours
  permissions: ["summarize", "compare"]
};

// Routing logic would validate TTL, check permissions, and forward
```

### Example: A Context Packet

```json
{
  "context_id": "ctx_abc123",
  "intent": "research",
  "scope": "project_x",
  "source": "atlas_browser_v1.2",
  "actor": "user@example.com",
  "payload": {
    "content": "User is debugging a React component",
    "file": "src/App.jsx",
    "line": 42,
    "error": "Cannot read property 'map' of undefined"
  },
  "created_at": "2025-12-17T23:41:00Z",
  "ttl": "2h",
  "expires_at": "2025-12-18T01:41:00Z",
  "permissions": ["debug", "suggest_fix"]
}
```

**What Happens:**
1. ✅ Context is promoted **explicitly** by the browser
2. ✅ Packet includes full **attribution** (source, actor, timestamp)
3. ✅ AI system receives **only valid context** (checks expiration)
4. ⏱️ After 2 hours, context **automatically expires**
5. 🔍 Full **audit trail** is available for review

---

## Use Cases

### 1. Cross-Application AI Workflows

**Problem:** User switches between browser, IDE, and terminal—context is lost.

**Solution:** Each application promotes context to Context Broker. AI systems receive unified, time-valid context regardless of which app initiated the request.

```
Browser (debugging) ──┐
                      ├──→ Context Broker ──→ AI System
VS Code (editing)   ──┤                        (unified context)
Terminal (testing)  ──┘
```

---

### 2. Regulated Environments

**Problem:** Healthcare/finance requires full audit trails and time-bounded data retention.

**Solution:** Context Broker provides complete provenance tracking (who, what, when), automatic expiration (no indefinite persistence), and human-legible audit logs (compliance-friendly).

---

## Design Goals

| Goal | Why It Matters |
|------|----------------|
| 🎯 **Minimal surface area** | Easier to audit, harder to misuse |
| 🔍 **Explicit over implicit** | No hidden behavior, no surprises |
| 🔮 **Deterministic behavior** | Same input → same output |
| 📋 **Easy to audit** | Full visibility for security teams |
| 🔧 **Easy to fork** | Adapt to your specific needs |
| 🔓 **No vendor lock-in** | Works with any AI system |

---

## Project Status

> **This repository is a reference implementation and design nucleus.**

### What This Means

- ✅ **Intentionally small** — focuses on core primitives
- ✅ **Intentionally incomplete** — not a batteries-included platform
- ✅ **Intended to be adapted** — fork and customize for your needs

### Future Directions

Future work may include additional reference implementations, integration stubs, and security analysis. These are intentionally left open to allow adaptation to local requirements.

**Want to contribute?** See [`CONTRIBUTING.md`](CONTRIBUTING.md)

---

## Documentation

| Document | Description |
|----------|-------------|
| 📖 [ALCOA Principles](docs/alcoa-and-time.md) | Deep dive into quality framework and time constraints |
| 🔗 [Interoperability Notes](docs/interoperability-notes.md) | How Context Broker fits in multi-vendor AI ecosystems |
| 📄 [RFC-0001: Context Packet Evolution](docs/rfc-0001-context-packet-evolution.md) | Design decisions and packet format evolution |
| 🤝 [Contributing Guide](CONTRIBUTING.md) | How to extend and improve Context Broker |
| 🎓 [Example Packets](examples/) | Valid and expired context packet samples |

---

## Continuous Integration

Context Broker runs a lightweight GitHub Actions CI workflow on every push and pull request. It focuses on fast, deterministic checks that validate core behavior without requiring external services.

**What CI checks:**
- ✅ Python dependency installation (`pip install -r requirements.txt`)
- ✅ Syntax validation via `py_compile` on the reference validator
- ✅ Unit tests (when `tests/` directory exists — currently optional)
- ✅ Smoke test: validates a dynamically-generated context packet against schema and time rules

**What CI intentionally does not check:**
- ❌ Full end-to-end runtime with external brokers or databases
- ❌ Environment-specific integrations or vendor services

**Reproduce CI checks locally:**

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Verify Python syntax
python -m py_compile src/validate_packet.py

# Run unit tests (only if tests/ directory exists)
python -m unittest discover -s tests 2>/dev/null || echo "No tests directory found"

# Run smoke test: validate a fresh context packet
python - <<'PY'
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

now = datetime.now(timezone.utc)
packet = {
    "schema_version": "1.0.0",
    "context_id": "ctx_local_smoke",
    "intent": "ci_smoke",
    "scope": "ci",
    "source": "local",
    "actor": "developer",
    "payload": {"message": "smoke test"},
    "created_at": now.isoformat().replace("+00:00", "Z"),
    "ttl": "1h",
    "expires_at": (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
    "permissions": ["read"],
}
tmp = Path(tempfile.gettempdir()) / "ci_packet.json"
tmp.write_text(json.dumps(packet), encoding="utf-8")
print(f"Created test packet: {tmp}")
PY

# Validate the generated packet
# Note: Use the path shown in the output above. On Unix/Linux/macOS this is typically
# /tmp/ci_packet.json, on Windows it's usually C:\Users\<username>\AppData\Local\Temp\ci_packet.json
python src/validate_packet.py /tmp/ci_packet.json --output text  # Unix/Linux/macOS
# OR on Windows:
# python src/validate_packet.py %TEMP%\ci_packet.json --output text
```

**Expected output:**
```
Created test packet: /tmp/ci_packet.json
OK: packet is valid
```

*Note: The exact path may vary by system (e.g., `C:\Users\...\Temp\` on Windows).*

---

## Philosophy

### The Core Insight

> **Interoperable systems do not begin with shared intelligence.**  
> **They begin with shared discipline.**

Context Broker defines that discipline at the boundary where humans, software, and AI systems meet.

### Why Constraints Are Features

Context Broker could allow:
- Infinite context persistence
- Silent background harvesting
- Cross-session context blending
- Behavioral inference

**We intentionally prohibit these patterns** because they lead to:
- ❌ Unpredictable AI behavior
- ❌ Privacy concerns
- ❌ Difficult debugging
- ❌ Regulatory risk

By **constraining** the system, we make it:
- ✅ Safe by construction
- ✅ Auditable by default
- ✅ Predictable in production

Context Broker draws inspiration from:

- **ALCOA principles** from pharmaceutical quality control
- **Event sourcing** patterns from distributed systems
- **Zero-knowledge architecture** from privacy engineering
- **Time-series database design** from observability systems

---

## Community

- 💬 **[Discussions](https://github.com/dfeen87/Context-Broker/discussions)** — Ask questions, share ideas
- 🐛 **[Issues](https://github.com/dfeen87/Context-Broker/issues)** — Report bugs, request features
- 🤝 **[Contributing](CONTRIBUTING.md)** — Submit PRs, improve docs

---

## License

This project is available for **non‑commercial use only** under the terms of the included LICENSE file.  
Commercial use requires a separate paid license.

---

## Acknowledgments

This project was developed with a combination of original ideas, hands‑on coding, and support from advanced AI systems. I would like to acknowledge **Microsoft Copilot**, **Anthropic Claude**, and **OpenAI ChatGPT** for their meaningful assistance in refining concepts, improving clarity, and strengthening the overall quality of this work.

---

## Closing Note

Modern AI systems are powerful but fragmented.

**Context Broker doesn't make AI systems smarter.**

**It makes them work together safely.**

By treating context as a **time-bound, attributable artifact**—not an ambient data stream—we enable:
- 🔐 Privacy-preserving AI workflows
- 🔍 Auditable decision-making
- 🤝 Vendor-neutral interoperability
- ⏱️ Predictable, time-aware behavior

**Start with the context boundary. Everything else follows.**

---

**Context Broker** — *Disciplined context for the distributed AI era.*
