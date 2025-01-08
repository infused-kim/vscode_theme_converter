import json
from enum import Enum
from pathlib import Path
from typing import ClassVar, Iterator, Literal, Self, cast

from pydantic import BaseModel, Field, field_serializer, field_validator
from rich.color import Color
from rich.style import Style

from .terminal import get_terminal_ansi_color

#
# ANSI color definitions
#


class AnsiColorName(Enum):
    """Names of standard ANSI colors."""

    # Special colors (-2 to -1)
    BACKGROUND = -2
    FOREGROUND = -1

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
AnsiColorNum = Literal[
    # Special colors
    -2,
    -1,
    # Normal colors
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    # Bright colors
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
]


class AnsiColor:
    """
    Represents an ANSI terminal color.

    This class manages all 16 standard ANSI colors (8 normal + 8 bright).

    Colors are cached at class level to ensure single instance per color.
    """

    # Class-level storage
    _by_name: ClassVar[dict[AnsiColorName, 'AnsiColor']] = {}
    _by_num: ClassVar[dict[AnsiColorNum, 'AnsiColor']] = {}
    _by_family: ClassVar[list['AnsiColor']] = []
    _initialized: ClassVar[bool] = False

    def __init__(self, name: AnsiColorName) -> None:
        """Initialize color (should only be called by create())."""
        self.name: str = name.name
        self.title: str = name.name.replace('_', ' ').title()
        self.num: AnsiColorNum = name.value
        self.color_code: str | None = get_terminal_ansi_color(self.num)
        self.color_code_title = (
            self.color_code if self.color_code is not None else '' * 7
        )

    def __str__(self) -> str:
        """Return the color name."""
        return f'ANSI {self.num:02d}: {self.name}'

    def get_color_code(self, if_none: str = '' * 7) -> str:
        """Get the color code, or a default if none."""
        return self.color_code or if_none

    def get_rich_style(
        self, bgcolor: str | None = None
    ) -> Style | Literal['normal']:
        """Return a rich style for this color and set background color."""
        color = f'color({self.num})'

        if self.num < 0:
            if self.color_code is not None:
                color = self.color_code
            else:
                color = Color.default()

        style = Style(color=color, bgcolor=bgcolor)

        if style == Style():
            style = 'normal'

        return style

    @property
    def rich_style(self) -> Style | Literal['normal']:
        """Return a rich style for this color."""
        return self.get_rich_style()

    @property
    def is_bright(self) -> bool:
        """Whether this is a bright variant."""
        return self.num >= 8

    @property
    def is_special(self) -> bool:
        """Whether this is a special color."""
        return self.num < 0

    @property
    def is_background(self) -> bool:
        """Whether this is the background color."""
        return self.num == AnsiColorName.BACKGROUND.value

    @property
    def is_foreground(self) -> bool:
        """Whether this is the foreground color."""
        return self.num == AnsiColorName.FOREGROUND.value

    @property
    def base_color(self) -> 'AnsiColor':
        """Get the non-bright version of this color."""
        if self.is_bright:
            return self.from_num(cast(AnsiColorNum, self.num - 8))
        return self

    @property
    def ansi_hex(self) -> str:
        """
        Get the hex code that encodes this ANSI color number.
        """
        return f'#{self.num:02x}000000'

    @property
    def sort_order_by_family(self) -> int:
        """Get index in family ordering."""
        return self._by_family.index(self)

    #
    # Class methods
    #

    @classmethod
    def create(cls) -> None:
        """Create all standard ANSI colors."""
        if cls._initialized:
            return

        # Create all colors first
        for color_name in AnsiColorName:
            color = cls(color_name)
            cls._by_name[color_name] = color
            cls._by_num[color_name.value] = color

        # Build family order list
        cls._by_family = [
            cls._by_num[AnsiColorName.BACKGROUND.value],
            cls._by_num[AnsiColorName.FOREGROUND.value],
        ]

        base_colors_names = [
            color_name
            for color_name in AnsiColorName
            if color_name.value < 8 and color_name.value >= 0
        ]

        for color_name in base_colors_names:
            # Normal color
            cls._by_family.append(cls._by_num[color_name.value])

            # Bright variant
            cls._by_family.append(
                cls._by_num[cast(AnsiColorNum, color_name.value + 8)]
            )

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
        if num < 0 or num > 15:
            raise ValueError(
                f'ANSI color number must be between 0 and 15, got: {num}'
            )

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
        """Iterate through colors in family order."""
        return iter(cls._by_family)


# Create all standard colors
AnsiColor.create()


#
# Color mapping Models
#


class ColorMapping(BaseModel):
    """Maps a color to ANSI and tracks its usage."""

    class Config:
        arbitrary_types_allowed = True

    color_code: str
    ansi_color: AnsiColor | None = None
    ui_settings: set[str] = Field(default_factory=set)
    scopes: set[str] = Field(default_factory=set)

    @field_serializer('ui_settings', 'scopes')
    def serialize_sets(self, value: set[str]) -> list[str]:
        """Convert sets to sorted lists for JSON serialization."""
        return sorted(value)

    @field_validator('ui_settings', 'scopes', mode='before')
    @classmethod
    def validate_sets(cls, value: list[str] | set[str]) -> set[str]:
        """Convert lists to sets when loading from JSON."""
        if isinstance(value, list):
            return set(value)
        return value

    @field_validator('ansi_color', mode='before')
    @classmethod
    def validate_ansi_color(
        cls, value: AnsiColor | str | int | None
    ) -> AnsiColor | None:
        """Convert string or int to AnsiColor object."""
        if value is None:
            return None

        # Handle AnsiColor object
        if isinstance(value, AnsiColor):
            return value

        # Handle string input (color name)
        if isinstance(value, str):
            try:
                # Try to get enum by name
                color_name = AnsiColorName[value.upper()]
                return AnsiColor.from_name(color_name)
            except KeyError as e:
                # If not a name, try converting to int
                try:
                    num = int(value)
                    return AnsiColor.from_num(num)  # type: ignore
                except ValueError:
                    raise ValueError(
                        f'Invalid ANSI color name or number: {value}'
                    ) from e

        # Handle integer input
        if isinstance(value, int):
            return AnsiColor.from_num(value)  # type: ignore

        raise ValueError(f'Invalid ANSI color value: {value}')

    @property
    def usage_count(self) -> int:
        """Total number of places this color is used."""
        return len(self.ui_settings) + len(self.scopes)

    @field_serializer('ansi_color')
    def serialize_ansi_color(self, ansi_color: AnsiColor | None) -> str | None:
        """Serialize AnsiColor to string."""
        if ansi_color is None:
            return None
        return cast(str, ansi_color.name)


class AnsiMapping(BaseModel):
    """Collection of color mappings for a theme."""

    theme_name: str
    color_mappings: list[ColorMapping]

    def save_json(self, file_path: Path | str) -> None:
        """Save the color mappings to a JSON file."""
        if isinstance(file_path, str):
            file_path = Path(file_path)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(
                self.model_dump(mode='json'),
                f,
                indent=2,
                ensure_ascii=False,
            )

    @classmethod
    def load_json(cls, file_path: Path | str) -> Self:
        """Load color mappings from a JSON file."""
        if isinstance(file_path, str):
            file_path = Path(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return cls.model_validate(data)

    @property
    def token_color_mappings(self) -> dict[str, ColorMapping]:
        """Get mappings as a dict for backward compatibility."""
        return {mapping.color_code: mapping for mapping in self.color_mappings}
