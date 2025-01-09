"""
Functions that help us to determine the actual colors the current terminal is
using.
"""

import select
import sys
import termios
import tty
from functools import lru_cache

DEBUG = False
TIMEOUT_RESPONSE = 0.2
TIMEOUT_READ_CHAR = 0.05
RETRIES = 2


@lru_cache(maxsize=16)
def get_terminal_ansi_color(
    ansi_color_num: int, debug: bool = DEBUG
) -> str | None:
    """Query terminal for ANSI color."""
    _debug_print(f'\nQuerying ANSI color {ansi_color_num}', debug)

    if ansi_color_num == -1:
        return get_terminal_foreground_color(debug=debug)
    elif ansi_color_num == -2:
        return get_terminal_background_color(debug=debug)
    return _query_osc_4(ansi_color_num, debug=debug)


@lru_cache(maxsize=1)
def get_terminal_foreground_color(debug: bool = DEBUG) -> str | None:
    """Query terminal for foreground color."""
    _debug_print('\nQuerying foreground color', debug)

    # Try standard method first (OSC 10)
    color = _query_osc_10(debug=debug)
    if color is not None:
        _debug_print(f'Got foreground color using OSC 10: {color}', debug)
        return color

    # Fall back to iTerm2 method (OSC 4;-1)
    _debug_print('Falling back to OSC 4;-1', debug)
    return _query_osc_4(-1, debug=debug)


@lru_cache(maxsize=1)
def get_terminal_background_color(debug: bool = DEBUG) -> str | None:
    """Query terminal for background color."""
    _debug_print('\nQuerying background color', debug)

    # Try standard method first (OSC 11)
    color = _query_osc_11(debug=debug)
    if color is not None:
        _debug_print(f'Got background color using OSC 11: {color}', debug)
        return color

    # Fall back to iTerm2 method (OSC 4;-2)
    _debug_print('Falling back to OSC 4;-2', debug)
    return _query_osc_4(-2, debug=debug)


def _debug_print(msg: str, debug: bool = False) -> None:
    """Print debug message if debug is enabled."""
    if debug:
        print(msg)


def _query_osc_4(color_num: int, debug: bool = False) -> str | None:
    """Query terminal for ANSI color using OSC 4."""
    _debug_print(f'\nQuerying OSC 4 color {color_num}', debug)

    try:
        response = _query_osc_retry(f'\033]4;{color_num};?\007', debug=debug)
        return _parse_rgb_response(response, debug=debug)
    except TerminalError:
        return None


def _query_osc_10(debug: bool = False) -> str | None:
    """Query terminal for foreground color using OSC 10."""
    _debug_print('\nQuerying OSC 10 (foreground)', debug)

    try:
        response = _query_osc_retry('\033]10;?\007', debug=debug)
        return _parse_rgb_response(response, debug=debug)
    except TerminalError:
        return None


def _query_osc_11(debug: bool = False) -> str | None:
    """Query terminal for background color using OSC 11."""
    _debug_print('\nQuerying OSC 11 (background)', debug)

    try:
        response = _query_osc_retry('\033]11;?\007', debug=debug)
        return _parse_rgb_response(response, debug=debug)
    except TerminalError:
        return None


def _parse_rgb_response(response: str, debug: bool = False) -> str | None:
    """Parse RGB color from OSC response."""
    _debug_print(f'Parsing response: {repr(response)}', debug)

    if 'rgb:' not in response:
        _debug_print('No rgb: in response', debug)
        return None

    try:
        rgb = response.split('rgb:')[1].split('\007')[0].strip('\033\\')
        r, g, b = [int(c[:2], 16) for c in rgb.split('/')]
        result = f'#{r:02x}{g:02x}{b:02x}'.upper()
        _debug_print(f'Parsed color: {result}', debug)
        return result
    except (ValueError, IndexError) as e:
        _debug_print(f'Error parsing RGB values: {e}', debug)
        return None


def _query_osc_retry(
    query: str,
    retries: int = 2,
    timeout: float = TIMEOUT_RESPONSE,
    debug: bool = False,
) -> str:
    """
    Send an OSC query to the terminal with retries.

    Args:
        query: The full OSC query string (including ESC and terminator)
        retries: Number of times to retry on failure
        timeout: How long to wait for response (seconds)
        debug: Whether to print debug messages

    Returns:
        The complete response string

    Raises:
        TerminalError: If all retries failed
    """
    last_error = None
    for attempt in range(retries):
        try:
            _debug_print(
                f'\nAttempt {attempt + 1}/{retries} for query {repr(query)}',
                debug,
            )
            return _query_osc(query, timeout=timeout, debug=debug)
        except TerminalError as e:
            _debug_print(f'Attempt {attempt + 1} failed: {e}', debug)
            last_error = e
            continue

    _debug_print('All retries failed', debug)
    assert last_error is not None
    raise last_error


def _query_osc(
    query: str, timeout: float = TIMEOUT_RESPONSE, debug: bool = False
) -> str:
    """
    Send an OSC query to the terminal and return the response.

    Args:
        query: The full OSC query string (including ESC and terminator)
        timeout: How long to wait for response (seconds)
        debug: Whether to print debug messages

    Returns:
        The complete response string
    """

    _debug_print(f'Sending query: {repr(query)}', debug)

    fd = None
    old_settings = None

    try:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
    except Exception as e:
        _debug_print(f'Failed to get terminal settings: {e}', debug)
        raise TerminalError('Failed to get terminal settings') from e

    try:
        _debug_print('Setting terminal to raw mode', debug)

        # Set terminal to raw mode
        tty.setraw(fd)

        # Clear input buffer
        termios.tcflush(fd, termios.TCIFLUSH)

        # Send query
        sys.stdout.write(query)
        sys.stdout.flush()

        # Wait for response
        _debug_print(f'Waiting for response (timeout: {timeout}s)', debug)

        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if not rlist:
            _debug_print('Timeout waiting for response', debug)
            raise TerminalTimeoutError('Terminal did not respond')

        # Read response until terminator
        response = ''
        while True:
            # Check if we can read without blocking
            rlist, _, _ = select.select([sys.stdin], [], [], TIMEOUT_READ_CHAR)
            if not rlist:
                _debug_print('No more data available', debug)
                break

            char = sys.stdin.read(1)
            if not char:  # EOF
                _debug_print('Got EOF', debug)
                break

            response += char
            _debug_print(f'Read character: {repr(char)}', debug)

            if char == '\007' or response.endswith('\033\\'):
                _debug_print(f'Got complete response: {repr(response)}', debug)
                return response

        _debug_print('Response incomplete', debug)
        raise TerminalError('Incomplete response from terminal')

    finally:
        if fd is not None and old_settings is not None:
            _debug_print('Restoring terminal settings', debug)
            # Clear any remaining input
            termios.tcflush(fd, termios.TCIFLUSH)
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


class TerminalError(Exception):
    """Base class for terminal-related errors."""


class TerminalTimeoutError(TerminalError):
    """Raised when terminal does not respond in time."""
