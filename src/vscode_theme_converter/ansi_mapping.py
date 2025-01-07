import json
from enum import IntEnum
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field, field_validator


class AnsiColor(IntEnum):
    """Standard ANSI colors."""

    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7

    # Bright variants
    BLACK_BRIGHT = 8
    RED_BRIGHT = 9
    GREEN_BRIGHT = 10
    YELLOW_BRIGHT = 11
    BLUE_BRIGHT = 12
    MAGENTA_BRIGHT = 13
    CYAN_BRIGHT = 14
    WHITE_BRIGHT = 15

    @classmethod
    def from_string(cls, value: str) -> 'AnsiColor':
        """Convert string to AnsiColor enum."""
        try:
            return cls[value.upper()]
        except KeyError as e:
            raise ValueError(
                f'Invalid ANSI color name: {value}. '
                f'Valid values are: {", ".join(cls.__members__)}'
            ) from e


class ColorMapping(BaseModel):
    """Maps a color to ANSI and tracks its usage."""

    color_code: str  # Hex color code like '#FFFFFF'
    ansi_color: AnsiColor | None = None
    ui_settings: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)

    @field_validator('ansi_color', mode='before')
    @classmethod
    def validate_ansi_color(cls, value: str | int | None) -> AnsiColor | None:
        """Convert string to AnsiColor enum."""
        if value is None:
            return None
        if isinstance(value, (AnsiColor, int)):
            return AnsiColor(value)
        if isinstance(value, str):
            return AnsiColor.from_string(value)
        raise ValueError(f'Invalid ANSI color value: {value}')

    @property
    def usage_count(self) -> int:
        """Total number of places this color is used."""
        return len(self.ui_settings) + len(self.scopes)


class AnsiMapping(BaseModel):
    """Collection of color mappings for a theme."""

    theme_name: str
    token_color_mappings: dict[str, ColorMapping]

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
