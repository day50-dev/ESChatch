# Changelog

All notable changes to ESChatch will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-18

### Added
- **Configuration system** - TOML-based config at `~/.config/eschatch/config.toml`
- **Multiple LLM providers** - Support for OpenAI, Ollama, vLLM, litellm proxy, simonw/llm
- **Configurable escape keys** - Support for Ctrl+X, Ctrl+Space, Ctrl+C, Escape, etc.
- **Configurable session directories** - Logs stored in `~/.eschatch/sessions/`
- **Sliding window context** - Configurable context size with intelligent history capture
- **Safety rails** - Preview mode and destructive command detection
- **Chat mode** - Multi-turn conversations with `/chat` command
- **Special commands**:
  - `/chat` - Enable conversation mode
  - `/explain` - Explain current terminal state
  - `/debug` - Analyze errors and suggest fixes
  - `/clear` - Clear conversation history
  - `/help` - Show available commands
- **Environment variable overrides** - `ESCHATCH_MODEL`, `ESCHATCH_BASE_URL`, `ESCHATCH_API_KEY`
- **Installation script** - `install.sh` for one-line installation
- **Package structure** - Proper `pyproject.toml` with console script entry point
- **Verbose logging** - `--verbose` flag for debugging

### Changed
- **Improved escape mode UX** - Clean overlay prompt with `[ESChatch] Task:` indicator
- **Refactored codebase** - Split into modular components (`config.py`, `context.py`, `llm_client.py`)
- **Better context capture** - Sliding window with configurable bytes/lines
- **Enhanced documentation** - Expanded README with examples, architecture diagram, troubleshooting

### Fixed
- Hardcoded `/tmp/screen-query/` path now configurable
- Hardcoded LLM URL and model now configurable
- Fixed escape mode cursor restoration
- Improved ANSI escape code handling

### Removed
- **Breaking**: Direct CLI arguments for LLM config (use config file or env vars instead)

## [0.1.0] - 2026-02-17

### Added
- Initial prototype release
- Basic pty wrapper functionality
- Input/output logging to files
- Ctrl+X escape mode
- LLM command injection
- Support for litellm and simonw/llm backends

[0.2.0]: https://github.com/day50/ESChatch/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/day50/ESChatch/releases/tag/v0.1.0
