#!/usr/bin/env python3
"""
ESChatch - A true pty wrapper with LLM-powered command injection.

Transparently logs terminal I/O and allows invoking an LLM via escape key
to generate and inject commands into any running terminal application.
"""
import os
import pty
import select
import sys
import argparse
import tty
import termios
import fcntl
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from config import load_config, get_escape_sequence, create_default_config, DEFAULT_CONFIG
from context import ContextManager
from llm_client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("eschatch")

# ANSI escape patterns
ANSIESCAPE = r"\033(?:\[[0-9;?]*[a-zA-Z]|][0-9]*;;.*?\\|\\)"
strip_ansi = lambda x: re.sub(ANSIESCAPE, "", x)

# Destructive command patterns for safety checks
DESTRUCTIVE_PATTERNS = [
    r"rm\s+(-[rf]+\s+)?/",
    r"rm\s+-rf\s",
    r"dd\s+if=",
    r"mkfs",
    r":\(\)\{:\|:&\};:",
    r">/dev/sd",
    r"chmod\s+-R\s+777",
]


class ESChatch:
    """Main ESChatch application."""

    def __init__(self, config: Dict[str, Any], exec_command: str):
        self.config = config
        self.exec_command = exec_command

        # Get escape sequence from config
        self.escape_key = get_escape_sequence(config)

        # Initialize context manager
        session_dir = config["general"].get("session_dir", "~/.eschatch/sessions")
        max_bytes = config["context"].get("max_bytes", 2000)
        sliding_window = config["context"].get("sliding_window", True)
        self.context = ContextManager(session_dir, max_bytes, sliding_window)

        # Initialize LLM client
        self.llm = LLMClient(config["llm"])

        # Safety settings
        self.safety = config.get("safety", {})
        self.preview_mode = self.safety.get("preview_mode", False)
        self.confirm_destructive = self.safety.get("confirm_destructive", True)
        self.destructive_patterns = self.safety.get(
            "destructive_patterns",
            DESTRUCTIVE_PATTERNS
        )

        # State
        self.is_escaped = False
        self.chat_mode = False
        self.query_buffer = b""
        self.ansi_save_pos = "\x1b[s"
        self.ansi_restore_pos = "\x1b[u"
        self.conversation_history = []

        # Prompts
        self.system_prompt = config["prompt"].get("system", DEFAULT_CONFIG["prompt"]["system"])

    def build_prompt(self, query: str, chat_mode: bool = False) -> str:
        """Build the LLM prompt with context."""
        recent_input, recent_output = self.context.get_context()

        if chat_mode and self.conversation_history:
            # In chat mode, include conversation history
            history = "\n".join([f"{h['role']}: {h['content']}" for h in self.conversation_history[-4:]])
            context = f"""Previous conversation:
----
{history}
----

"""
        else:
            context = ""

        return f"""You are an experienced fullstack software engineer with expertise in all Linux commands and their functionality.
Given a task, along with a sequence of previous inputs and screen scrape, generate a single line of commands that accomplish the task efficiently.
This command is to be executed in the current program which can be determined by the screen scrape.

{context}The screen scrape is:
----
{recent_output}
----

The recent input is: {recent_input}
----

Take special care and look at the most recent part of the screen scrape. Pay attention to:
- Things like the prompt style, welcome banners
- Be sensitive if the person is say at a python prompt, ruby prompt, gdb, or perhaps inside a program such as vim

Create a command to accomplish the following task: {query}

If there is text enclosed in parenthesis, that's what ought to be changed.

Output only the command as a single line of plain text, with no quotes, formatting, or additional commentary.
Do not use markdown or any other formatting. Do not include the command into a code block.
Don't include the program itself (bash, zsh, etc.) in the command."""

    def is_destructive(self, command: str) -> bool:
        """Check if a command appears to be destructive."""
        if not self.confirm_destructive:
            return False

        for pattern in self.destructive_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False

    def activate(self, query: bytes, chat_mode: bool = False) -> bytes:
        """
        Activate LLM to generate command based on query.

        Args:
            query: The user's query as bytes
            chat_mode: Whether to include conversation history

        Returns:
            Generated command as bytes
        """
        query_str = query.decode("utf-8", errors="replace").strip()

        if not query_str:
            return b""

        # Handle special commands in chat mode
        if query_str.startswith("/"):
            return self._handle_special_command(query_str)

        # Build prompt with context
        prompt = self.build_prompt(query_str, chat_mode)

        # Generate response
        response = self.llm.generate(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=self.system_prompt
        )

        # Store in conversation history if in chat mode
        if chat_mode:
            self.conversation_history.append({"role": "user", "content": query_str})
            self.conversation_history.append({"role": "assistant", "content": response})

        # Safety check for destructive commands
        if self.is_destructive(response):
            logger.warning(f"Potentially destructive command detected: {response}")
            if self.preview_mode:
                # In preview mode, show warning and don't auto-inject
                sys.stdout.write(
                    f"\n\x1b[31m[ESChatch] Warning: Destructive command detected. Press Enter to confirm or Ctrl+C to cancel.\x1b[0m\n"
                )
                sys.stdout.flush()

        logger.info(f"LLM response: {response}")
        return response.encode("utf-8") + b"\n"

    def _handle_special_command(self, cmd: str) -> bytes:
        """Handle special slash commands."""
        cmd = cmd.lower().strip()

        if cmd == "/chat":
            self.chat_mode = True
            return b"[ESChatch] Chat mode enabled. Continue the conversation or press Enter twice to exit.\n"
        elif cmd == "/explain":
            recent_input, recent_output = self.context.get_context()
            prompt = f"Explain what is happening in this terminal session:\n----\n{recent_output}\n----\nRecent input: {recent_input}"
            response = self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a helpful assistant that explains terminal sessions clearly and concisely."
            )
            return f"\n{response}\n".encode()
        elif cmd == "/debug":
            recent_input, recent_output = self.context.get_context()
            prompt = f"Analyze the last error or issue in this terminal session and suggest how to fix it:\n----\n{recent_output}\n----\nRecent input: {recent_input}"
            response = self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are an expert debugger that helps identify and fix terminal/command errors."
            )
            return f"\n{response}\n".encode()
        elif cmd == "/clear":
            self.conversation_history = []
            return b"[ESChatch] Conversation history cleared.\n"
        elif cmd == "/help":
            help_text = """
[ESChatch] Special commands:
  /chat    - Enable multi-turn conversation mode
  /explain - Explain current terminal state
  /debug   - Analyze errors and suggest fixes
  /clear   - Clear conversation history
  /help    - Show this help message
"""
            return help_text.encode()
        else:
            return f"[ESChatch] Unknown command: {cmd}\n".encode()

    def show_escape_prompt(self) -> None:
        """Show the escape mode prompt overlay."""
        # Save cursor position
        sys.stdout.write(self.ansi_save_pos)
        # Show prompt in reverse video
        sys.stdout.write("\x1b[7m[ESChatch] Task: \x1b[0m")
        sys.stdout.flush()

    def restore_after_prompt(self) -> None:
        """Restore cursor position after prompt."""
        sys.stdout.write(self.ansi_restore_pos)
        sys.stdout.flush()

    def set_pty_size(self, pty_fd: int, target_fd: int) -> None:
        """Sync PTY size with terminal."""
        try:
            s = fcntl.ioctl(target_fd, termios.TIOCGWINSZ, b"\x00" * 8)
            fcntl.ioctl(pty_fd, termios.TIOCSWINSZ, s)
        except OSError:
            pass

    def run(self) -> None:
        """Main event loop."""
        orig_attrs = termios.tcgetattr(sys.stdin.fileno())

        try:
            tty.setraw(sys.stdin.fileno())

            # Fork PTY
            pid, fd = pty.fork()

            if pid == 0:
                # Child process - execute the command
                exec_list = self.exec_command.split()
                os.execvp(exec_list[0], exec_list)
            else:
                # Parent process - handle I/O
                self.set_pty_size(fd, sys.stdin.fileno())

                while True:
                    r, _, _ = select.select([fd, sys.stdin], [], [])

                    if sys.stdin in r:
                        user_input = os.read(sys.stdin.fileno(), 1024)
                        if not user_input:
                            break

                        # Handle escape mode
                        if self.is_escaped:
                            self.query_buffer += user_input

                            # Check for Enter/Return to submit
                            if b"\r" in user_input or b"\n" in user_input:
                                # Check for double-enter to exit chat mode
                                query_text = self.query_buffer.decode("utf-8", errors="replace").strip()
                                if self.chat_mode and not query_text:
                                    self.is_escaped = False
                                    self.chat_mode = False
                                    sys.stdout.write("\x1b[2K\r")
                                    sys.stdout.write("\x1b[32m[ESChatch] Chat mode exited.\x1b[0m\n")
                                    sys.stdout.flush()
                                    self.query_buffer = b""
                                    continue

                                self.is_escaped = False

                                # Clear the prompt line
                                sys.stdout.write("\x1b[2K\r")

                                # Generate command (pass chat_mode flag)
                                command = self.activate(self.query_buffer, self.chat_mode)

                                # Restore and inject
                                self.restore_after_prompt()
                                os.write(fd, command)

                                self.query_buffer = b""
                                continue

                        # Check for escape key
                        if self.escape_key in user_input:
                            self.is_escaped = True
                            if self.chat_mode:
                                sys.stdout.write("\x1b[7m[ESChatch] (chat) Task: \x1b[0m")
                            else:
                                self.show_escape_prompt()
                            continue

                        # Log input
                        self.context.append_input(user_input)

                        # Forward to PTY
                        os.write(fd, user_input)

                    if fd in r:
                        output = os.read(fd, 1024)
                        if not output:
                            break

                        # Log output
                        self.context.append_output(output)

                        # Forward to terminal
                        os.write(sys.stdout.fileno(), output)

        except (OSError, KeyboardInterrupt):
            logger.info("Exiting...")
            sys.exit(130)

        finally:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, orig_attrs)


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="ESChatch - LLM-powered terminal command injection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  eschatch                    # Use default shell (bash)
  eschatch -e zsh             # Use zsh
  eschatch -e python          # Start Python REPL
  eschatch --exec vim file.py # Open vim with file

Configuration:
  Config file: ~/.config/eschatch/config.toml
  Environment variables: ESCHATCH_MODEL, ESCHATCH_BASE_URL, ESCHATCH_API_KEY

Escape mode:
  Press Ctrl+X to enter escape mode, type your task, press Enter.
  The LLM will generate and inject the appropriate command.
"""
    )

    parser.add_argument(
        "--exec", "-e",
        default="bash",
        dest="exec_command",
        help="Command to execute (default: bash)"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to config file (default: ~/.config/eschatch/config.toml)"
    )
    parser.add_argument(
        "--model", "-m",
        help="LLM model to use (overrides config)"
    )
    parser.add_argument(
        "--base-url",
        help="LLM base URL (overrides config)"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview mode - show generated commands before injecting"
    )
    parser.add_argument(
        "--install-config",
        action="store_true",
        help="Create default config file and exit"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.install_config:
        config_path = create_default_config()
        print(f"Default config created at: {config_path}")
        sys.exit(0)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    config = load_config(args.config)

    # Override with CLI args
    if args.model:
        config["llm"]["model"] = args.model
    if args.base_url:
        config["llm"]["base_url"] = args.base_url
    if args.preview:
        config["safety"]["preview_mode"] = True

    # Print info
    logger.info(f"Starting ESChatch with command: {args.exec_command}")
    logger.info(f"Escape key: {config['general'].get('escape_key', 'ctrl+x')}")
    logger.info(f"Model: {config['llm'].get('model', 'gpt-4o-mini')}")

    # Run
    app = ESChatch(config, args.exec_command)
    app.run()


if __name__ == "__main__":
    main()
