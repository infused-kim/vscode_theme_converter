"""
Functions that help us to determine the actual colors the current terminal is
using.
"""

import sys
import termios
import tty

#
# Terminal color queries
#


def get_terminal_ansi_color(ansi_color_num: int) -> str | None:
    """Query terminal for ANSI color."""
    if ansi_color_num == -1:
        return get_terminal_foreground_color()
    elif ansi_color_num == -2:
        return get_terminal_background_color()
    return _query_osc_color(4, ansi_color_num)


def get_terminal_foreground_color() -> str | None:
    """Query terminal for foreground color using OSC 10."""
    return _query_osc_color(10)


def get_terminal_background_color() -> str | None:
    """Query terminal for background color using OSC 11."""
    return _query_osc_color(11)


def _query_osc_color(osc_code: int, param: int | None = None) -> str | None:
    """
    Query terminal for color using OSC escape sequence.

    Args:
        osc_code: OSC code to query (4 for ANSI colors, 11 for background)
        param: Optional parameter (e.g., color number for OSC 4)

    Returns:
        Hex color code or None if no response
    """

    try:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
    except Exception:
        return None

    try:
        # Set terminal to raw mode
        tty.setraw(fd)

        # Send OSC query (with optional parameter)
        query = f'\033]{osc_code}'
        if param is not None:
            query += f';{param}'
        query += ';?\007'

        sys.stdout.write(query)
        sys.stdout.flush()

        # Read response
        response = ''
        while len(response) < 100:  # Safeguard against infinite loop
            if sys.stdin.readable():
                char = sys.stdin.read(1)
                response += char
                if char == '\007':  # Bell character
                    break

        # Parse the response
        if 'rgb:' in response:
            rgb = response.split('rgb:')[1].strip('\007')
            r, g, b = [int(c[:2], 16) for c in rgb.split('/')]
            return f'#{r:02x}{g:02x}{b:02x}'.upper()

    finally:
        # Restore terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return None
