"""
AnsiColor class and function that help us to determine the actual colors the
current terminal is using.
"""

import sys
import termios
import tty
from enum import Enum
from typing import ClassVar, Iterator, Literal, cast

from rich.style import Style

#
# ANSI color definitions
#


class AnsiColorName(Enum):
    """Names of standard ANSI colors."""

    # Normal colors (0-7)
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7

    # Bright colors (8-15)
    BLACK_BRIGHT = 8
    RED_BRIGHT = 9
    GREEN_BRIGHT = 10
    YELLOW_BRIGHT = 11
    BLUE_BRIGHT = 12
    MAGENTA_BRIGHT = 13
    CYAN_BRIGHT = 14
    WHITE_BRIGHT = 15


# Define a new type for ANSI color numbers
AnsiColorNum = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]


class AnsiColor:
    """
    Represents an ANSI terminal color.

    This class manages all 16 standard ANSI colors (8 normal + 8 bright).

    Colors are cached at class level to ensure single instance per color.
    """

    # Class-level storage
    _by_name: ClassVar[dict[AnsiColorName, 'AnsiColor']] = {}
    _by_num: ClassVar[dict[AnsiColorNum, 'AnsiColor']] = {}
    _initialized: ClassVar[bool] = False

    def __init__(self, name: AnsiColorName) -> None:
        """Initialize color (should only be called by create())."""
        self.name = name.name
        self.title = name.name.replace('_', ' ').title()
        self.num: AnsiColorNum = name.value
        self.color_code: str | None = get_terminal_ansi_color(self.num)
        self.color_code_title = (
            self.color_code if self.color_code is not None else '' * 7
        )

    def __str__(self) -> str:
        """Return the color name."""
        return f'ANSI {self.num:02d}: {self.name}'

    def get_rich_style(self, bgcolor: str | None = None) -> Style:
        """Return a rich style for this color and set background color."""
        return Style(color=f'color({self.num})', bgcolor=bgcolor)

    @property
    def rich_style(self) -> Style:
        """Return a rich style for this color."""
        return self.get_rich_style()

    @property
    def is_bright(self) -> bool:
        """Whether this is a bright variant."""
        return self.num >= 8

    @property
    def base_color(self) -> 'AnsiColor':
        """Get the non-bright version of this color."""
        if self.is_bright:
            return self.from_num(cast(AnsiColorNum, self.num - 8))
        return self

    #
    # Class methods
    #

    @classmethod
    def create(cls) -> None:
        """Create all standard ANSI colors."""
        if cls._initialized:
            return

        for color_name in AnsiColorName:
            color = cls(color_name)
            cls._by_name[color_name] = color
            cls._by_num[color_name.value] = color

        cls._initialized = True

    @classmethod
    def from_name(cls, name: AnsiColorName) -> 'AnsiColor':
        """Get a color by its name."""

        if name not in AnsiColorName:
            raise ValueError(f'Invalid color name: {name}')

        return cls._by_name[name]

    @classmethod
    def from_num(cls, num: AnsiColorNum) -> 'AnsiColor':
        """Get a color by its number."""
        return cls._by_num[num]

    @classmethod
    def iter_by_number(cls) -> Iterator['AnsiColor']:
        """Iterate through all colors in numerical order (0-15)."""
        return (
            cls._by_num[color.value]
            for color in sorted(AnsiColorName, key=lambda color: color.value)
        )

    @classmethod
    def iter_by_name(cls) -> Iterator['AnsiColor']:
        """Iterate through all colors in alphabetical order."""
        return (
            cls._by_name[color]
            for color in sorted(AnsiColorName, key=lambda color: color.name)
        )

    @classmethod
    def iter_by_family(cls) -> Iterator['AnsiColor']:
        """
        Iterate through colors grouped by family.

        Returns colors in order: BLACK, BLACK_BRIGHT, RED, RED_BRIGHT, etc.
        """
        base_colors = (color for color in AnsiColorName if color.value < 8)

        for color in base_colors:
            # Normal color
            yield cls._by_num[color.value]

            # Bright variant
            yield cls._by_num[cast(AnsiColorNum, color.value + 8)]


#
# Terminal color queries
#


def get_terminal_ansi_color(ansi_color_num: int) -> str | None:
    """Query terminal for ANSI color using OSC 4."""
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


# Create all standard colors
AnsiColor.create()
