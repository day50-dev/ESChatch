<p align="center">
  <img width="394" height="173" alt="eschatch_sm" src="https://github.com/user-attachments/assets/b40eb05d-3de7-4982-b635-c8fb49ffb4c7" />

</p>


**ESChatch** is a true pty wrapper that transparently logs every byte of input/output from any terminal application (`zsh`, `vim`, `python`, SSH sessions, etc.), then lets you hit **Ctrl+X**, type a natural-language task, and have an LLM instantly generate and inject the exact keystrokes back into the running program.

The screen-scrape context makes it magically context-aware across all applications.

## Features

- **Universal terminal copilot** - Works in shells, editors, REPLs, SSH sessions, anywhere
- **Transparent logging** - Logs all I/O to configurable session directories
- **Context-aware** - LLM sees your terminal screen and recent input history
- **Configurable** - Escape keys, LLM providers, models, prompts via TOML config
- **Safety rails** - Preview mode and destructive command detection
- **Multi-provider** - Supports OpenAI, Ollama, vLLM, litellm proxy, and more
- **Chat mode** - Multi-turn conversations with context retention
- **Special commands** - `/explain`, `/debug`, `/chat`, `/clear`, `/help`

## Quick Start

### Installation

```bash
# Install from source
pip install -e .

# Or with pipx (recommended)
pipx install git+https://github.com/day50/ESChatch.git
```

### Usage

```bash
# Start with default shell (bash)
eschatch

# Use zsh
eschatch -e zsh

# Start Python REPL
eschatch -e python

# Open vim with a file
eschatch -e "vim myfile.py"

# SSH session
eschatch -e "ssh user@host"
```

### Basic Workflow

1. Start ESChatch with your desired command
2. Work normally in the terminal
3. Press **Ctrl+X** to enter escape mode
4. Type your task (e.g., "find all .py files modified today")
5. Press **Enter**
6. The LLM generates and injects the appropriate command

### Special Commands

ESChatch supports special slash commands:

- `/chat` - Enable multi-turn conversation mode (press Enter twice to exit)
- `/explain` - Explain what's happening in the current terminal state
- `/debug` - Analyze errors and suggest fixes
- `/clear` - Clear conversation history
- `/help` - Show available commands

Example:
```
Ctrl+X → /explain
→ "You're in a Python REPL with pandas loaded. The last operation filtered a DataFrame..."

Ctrl+X → /debug
→ "The error shows a FileNotFoundError. Check that 'data.csv' exists in your current directory..."
```

## Configuration

### Config File

Create `~/.config/eschatch/config.toml`:

```toml
[general]
escape_key = "ctrl+x"  # Options: ctrl+x, ctrl+space, ctrl+c, ctrl+d, escape
log_dir = "~/.eschatch/logs"
session_dir = "~/.eschatch/sessions"

[llm]
provider = "litellm"  # Options: litellm, ollama, openai, vllm, simonw
model = "gpt-4o-mini"
base_url = "http://localhost:4000"
api_key = "sk-..."  # Optional for local providers
temperature = 0.0
max_tokens = 500

[context]
max_bytes = 2000  # Amount of I/O history to include
sliding_window = true

[prompt]
system = """You are an expert Linux/terminal operator..."""

[safety]
preview_mode = false  # Show commands before injecting
confirm_destructive = true  # Warn about rm -rf, dd, etc.
```

### Environment Variables

Override config with environment variables:

```bash
export ESCHATCH_MODEL="gpt-4o"
export ESCHATCH_BASE_URL="http://localhost:4000"
export ESCHATCH_API_KEY="sk-..."
```

### Generate Default Config

```bash
eschatch --install-config
```

## LLM Providers

### OpenAI / litellm Proxy

```toml
[llm]
provider = "litellm"
model = "gpt-4o-mini"
base_url = "http://localhost:4000"
api_key = "sk-..."
```

### Ollama (Local)

```toml
[llm]
provider = "ollama"
model = "llama3.1"
base_url = "http://localhost:11434"
```

### vLLM

```toml
[llm]
provider = "vllm"
model = "meta-llama/Llama-3.1-8B"
base_url = "http://localhost:8000/v1"
```

### simonw/llm CLI

```toml
[llm]
provider = "simonw"
```

## Examples

### Shell Commands

```
Task: "find all Python files modified in the last 2 days"
→ find . -name "*.py" -mtime -2 -type f

Task: "show disk usage sorted by size"
→ du -sh * | sort -rh
```

### Inside Vim

```
Task: "format this Python function"
→ :%!black -

Task: "search for all occurrences of 'TODO'"
→ /TODO
```

### Python REPL

```
Task: "load the json file and parse it"
→ import json; data = json.load(open("file.json"))
```

### SSH Session

Works transparently over SSH - the LLM sees the remote terminal state.

## Safety Features

### Preview Mode

Enable to review generated commands before injection:

```bash
eschatch --preview
```

Or in config:

```toml
[safety]
preview_mode = true
```

### Destructive Command Detection

Automatically warns about dangerous patterns like:
- `rm -rf /` or `rm -rf ~`
- `dd if=...`
- `mkfs`
- Fork bombs
- Direct disk writes

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User Terminal                        │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    ESChatch (pty)                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Input Log   │  │ Output Log   │  │ Escape Handler │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      LLM Client                          │
│  (OpenAI / Ollama / vLLM / litellm / simonw)            │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Injected Command → Application              │
└─────────────────────────────────────────────────────────┘
```

## Command Line Options

```
usage: eschatch [-h] [--exec EXEC_COMMAND] [--config CONFIG]
                [--model MODEL] [--base-url BASE_URL] [--preview]
                [--install-config] [--verbose]

ESChatch - LLM-powered terminal command injection

options:
  -h, --help            show this help message and exit
  --exec, -e EXEC_COMMAND
                        Command to execute (default: bash)
  --config, -c CONFIG   Path to config file
  --model, -m MODEL     LLM model to use
  --base-url BASE_URL   LLM base URL
  --preview             Preview mode - show generated commands
  --install-config      Create default config file
  --verbose, -v         Enable verbose logging
```

## Limitations

- **Unix-only** - Uses pty, so Linux/macOS only
- **Single-threaded** - One session at a time
- **Raw terminal** - Requires tty (won't work in some IDE terminals)
- **Early alpha** - Actively developed, may have bugs

## Troubleshooting

### LLM connection fails

- Check your `base_url` and `api_key` in config
- Ensure your LLM provider is running (Ollama, litellm proxy, etc.)
- Run with `--verbose` for detailed logs

### Escape key not working

- Try different escape keys in config: `ctrl+space`, `escape`
- Some terminals may intercept certain key combinations

### Commands not injecting correctly

- Check that the LLM understands the current context
- Review the screen scrape in verbose logs
- Try a more specific task description

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Lint
ruff check .
```

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## Related Projects

- [sidechat](https://github.com/day50/sidechat) - LLM side panel for terminals
- [llm](https://github.com/simonw/llm) - CLI tool for LLM access
- [litellm](https://github.com/BerriAI/litellm) - Unified LLM API

## Acknowledgments

ESChatch was inspired by the idea of making LLMs a seamless part of the terminal workflow, working at the pty level to be truly application-agnostic.
