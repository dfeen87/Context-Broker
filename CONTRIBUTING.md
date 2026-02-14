# Contributing to Context Broker

Thank you for your interest in contributing to Context Broker! This document provides guidelines for contributing to the project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)

---

## Code of Conduct

This project follows a code of conduct based on mutual respect and professionalism. By participating, you agree to:

- Be respectful and constructive in all interactions
- Focus on what is best for the community
- Show empathy towards other community members

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected vs. actual behavior**
- **Environment details** (Python version, OS, etc.)
- **Sample context packets** that demonstrate the issue

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** explaining why this enhancement would be useful
- **Proposed implementation** (if you have ideas)
- **Backward compatibility** considerations

### Pull Requests

Pull requests are welcome! To submit a PR:

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes following the style guidelines
4. Add or update tests as needed
5. Update documentation to reflect your changes
6. Ensure CI checks pass
7. Submit the pull request

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git

### Setup Steps

```bash
# Clone your fork (replace YOUR-USERNAME with your GitHub username)
git clone https://github.com/YOUR-USERNAME/Context-Broker.git
cd Context-Broker

# Install dependencies
pip install -r requirements.txt

# Verify installation
python src/validate_packet.py --help
```

### Running Validation

```bash
# Validate example packets
python src/validate_packet.py examples/packet.valid.json
python src/validate_packet.py examples/packet.expired.json

# Run with different output formats
python src/validate_packet.py examples/packet.valid.json --output json
python src/validate_packet.py examples/packet.valid.json --output text
```

---

## Submitting Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-validator`
- `fix/time-parsing-edge-case`
- `docs/improve-readme`

### Commit Messages

Write clear, descriptive commit messages:

```
Fix time parsing for edge case with leap seconds

- Handle leap second boundary conditions
- Add test cases for 23:59:60Z timestamps
- Update documentation with leap second behavior
```

**Format:**
- First line: brief summary (50 chars or less)
- Blank line
- Detailed description (wrap at 72 chars)

### Pull Request Process

1. **Update documentation** if you're changing functionality
2. **Add tests** for new features or bug fixes
3. **Ensure CI passes** before requesting review
4. **Request review** from maintainers
5. **Address feedback** promptly and professionally

---

## Style Guidelines

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints where appropriate
- Write docstrings for public functions and classes
- Keep functions focused and single-purpose

**Example:**

```python
def parse_duration(duration: str, label: str = "ttl") -> timedelta:
    """
    Parse simple TTL strings like: '30m', '2h', '15s', '7d'
    
    Args:
        duration: Duration string in format <int><s|m|h|d>
        label: Label for error messages (default: "ttl")
    
    Returns:
        timedelta object representing the duration
    
    Raises:
        ValueError: If duration format is invalid
    """
    # Implementation...
```

### JSON Schema Style

- Use JSON Schema Draft 7
- Include descriptions for all properties
- Define clear examples
- Specify required fields explicitly

### Documentation Style

- Use Markdown for all documentation
- Include code examples where helpful
- Keep language clear and concise
- Use tables for structured comparisons

---

## Testing

### Running Tests

```bash
# Run all tests (when tests/ directory exists)
python -m unittest discover -s tests

# Run specific test file
python -m unittest tests/test_validator.py
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names
- Include both positive and negative test cases
- Test edge cases and boundary conditions

**Example:**

```python
import unittest
from datetime import datetime, timezone

class TestPacketValidation(unittest.TestCase):
    def test_valid_packet_passes(self):
        """Valid packet should pass all validation checks"""
        # Test implementation...
    
    def test_expired_packet_fails(self):
        """Expired packet should fail with TIME_EXPIRED error"""
        # Test implementation...
```

---

## Design Philosophy

When contributing, keep these core principles in mind:

1. **Minimal Surface Area** — Don't add features that expand scope unnecessarily
2. **Explicit Over Implicit** — Prefer clear, obvious behavior
3. **Time-Bound by Default** — All context must have expiration
4. **ALCOA Compliant** — Maintain attribution, legibility, contemporaneous recording, originality, accuracy
5. **Vendor Neutral** — Don't introduce vendor-specific dependencies

---

## Questions?

- **Discussions:** Use [GitHub Discussions](https://github.com/dfeen87/Context-Broker/discussions) for questions
- **Issues:** Use [GitHub Issues](https://github.com/dfeen87/Context-Broker/issues) for bugs and feature requests

---

## License

By contributing to Context Broker, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Context Broker!** 🎉
