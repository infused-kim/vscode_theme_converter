#!/usr/bin/env python3

"""
Script that cycles through Ghostty themes to record demo videos.
"""

import subprocess
import time
from pathlib import Path

import typer

# Default themes to cycle through
DEFAULT_THEMES = [
    'vscode-light-modern',
    'vscode-light-modern-dark',
    'catppuccin-latte',
    'catppuccin-frappe',
    '3024 Day',
    '3024 Night',
    'Adwaita',
    'Adwaita Dark',
    'AtomOneLight',
    'Atom',
    'ayu_light',
    'ayu',
    'BlueDolphin',
    'Borland',
    'WildCherry',
    'vscode-light-modern',
]

# Path to Ghostty config
GHOSTTY_CONFIG = Path.home() / '.config' / 'ghostty' / 'config'

app = typer.Typer()


def update_theme(theme_name: str) -> None:
    """Update the Ghostty config file with the new theme."""
    with open(GHOSTTY_CONFIG, 'r') as f:
        lines = f.readlines()

    theme_line_found = False
    for i, line in enumerate(lines):
        if line.strip().startswith('theme ='):
            lines[i] = f'theme = {theme_name}\n'
            theme_line_found = True
            break

    if not theme_line_found:
        raise ValueError(
            'No theme config found in Ghostty config. Please add one first.'
        )

    with open(GHOSTTY_CONFIG, 'w') as f:
        f.writelines(lines)


def reload_ghostty() -> None:
    """Send cmd+shift+, to reload Ghostty config."""
    apple_script = """
    tell application "System Events"
        keystroke "," using {command down, shift down}
    end tell
    """
    subprocess.run(['osascript', '-e', apple_script])


def set_terminal_title(title: str, tty_path: str) -> None:
    """Set the title of a specific terminal window using its TTY path."""
    # The escape sequence to set window title is: ESC]0;titleBEL
    # Where ESC is \033 and BEL is \007
    title_sequence = f'\033]0;{title}\007'

    try:
        with open(tty_path, 'w') as tty:
            tty.write(title_sequence)
    except (IOError, PermissionError) as e:
        print(f'Failed to set terminal title: {e}')


@app.command()
def main(
    themes: list[str] = typer.Option(
        DEFAULT_THEMES,
        '--theme',
        '-t',
        help='Theme(s) to cycle through. Can be specified multiple times.',
    ),
    sleep_duration: float = typer.Option(
        2.0,
        '--sleep',
        '-s',
        help='Time to wait after switching themes in seconds.',
    ),
    target_tty: str | None = typer.Option(
        None,
        '--tty',
        help='Path to TTY of target terminal (e.g., /dev/ttys001)',
    ),
    delay: float = typer.Option(
        0.0,
        '--delay',
        '-d',
        help='Time to wait before starting the theme cycling in seconds.',
    ),
) -> None:
    """Cycle through Ghostty themes."""
    if delay > 0:
        print(f'Waiting {delay} seconds before starting...')
        time.sleep(delay)

    for theme in themes:
        print(f'Switching to theme: {theme}')
        if target_tty:
            set_terminal_title(
                f'Terminal Theme: {theme} | Bat Theme: vscode-light-modern',
                target_tty,
            )
        update_theme(theme)
        reload_ghostty()
        time.sleep(sleep_duration)


if __name__ == '__main__':
    app()
