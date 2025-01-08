import json
from pathlib import Path
from typing import Self, cast

from pydantic import BaseModel, Field, field_serializer, field_validator

from .terminal import AnsiColor, AnsiColorName


class ColorMapping(BaseModel):
    """Maps a color to ANSI and tracks its usage."""

    class Config:
        arbitrary_types_allowed = True

    color_code: str
    ansi_color: AnsiColor | None = None
    ui_settings: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)

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
