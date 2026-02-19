# Contributing to ESChatch

Thank you for your interest in contributing to ESChatch! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/ESChatch.git`
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Create a branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Running from Source

```bash
python eschatch.py -e zsh
```

### Running Tests

```bash
pytest
```

### Code Style

We use `black` for formatting and `ruff` for linting:

```bash
black .
ruff check .
```

## Project Structure

```
ESChatch/
├── eschatch.py          # Main application (refactored)
├── config.py            # Configuration management
├── context.py           # I/O context management
├── llm_client.py        # LLM provider abstraction
├── pyproject.toml       # Package configuration
├── config.example.toml  # Example config file
├── install.sh           # Installation script
└── README.md            # Documentation
```

## Architecture

ESChatch consists of several key components:

1. **PTY Handler** - Manages the pseudo-terminal fork and I/O multiplexing
2. **Context Manager** - Handles sliding window of input/output logs
3. **LLM Client** - Abstracts multiple LLM providers
4. **Escape Handler** - Detects escape key and manages overlay prompt
5. **Config System** - TOML-based configuration with environment overrides

## Making Changes

### Bug Fixes

1. Describe the bug in the issue or PR
2. Provide steps to reproduce
3. Fix the bug
4. Add a test if applicable
5. Reference the issue in your PR

### New Features

1. Open an issue to discuss the feature first
2. Implement the feature
3. Add tests
4. Update documentation
5. Update `config.example.toml` if adding new config options

### Documentation

Improvements to documentation are always welcome! This includes:
- README.md updates
- Code comments
- Example configurations
- Troubleshooting guides

## Pull Request Guidelines

### PR Title

Use conventional commits format:
- `feat: add multi-line chat mode`
- `fix: handle ANSI escape codes in context`
- `docs: update installation instructions`
- `refactor: extract LLM client to separate module`

### PR Description

Include:
- What changes were made
- Why the changes were made
- How to test the changes
- Any breaking changes

### Code Review

- Be respectful and constructive
- Explain the reasoning behind suggestions
- Accept feedback gracefully

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR** - Breaking changes
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes (backward compatible)

### Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md
- [ ] Run all tests
- [ ] Update documentation
- [ ] Create git tag
- [ ] Publish to PyPI

## Reporting Issues

### Bug Reports

Include:
- ESChatch version
- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Logs (run with `--verbose`)

### Feature Requests

Include:
- What problem the feature solves
- How you envision the feature working
- Any alternative solutions you've considered

## Questions?

Open an issue for questions or discussions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
