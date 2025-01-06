import plistlib
from pathlib import Path
from pprint import pformat
from typing import Union

from pydantic import BaseModel, Field


class TMThemeGlobalSettings(BaseModel):
    """Global settings for TextMate themes."""

    # Basic colors
    background: str | None = None
    foreground: str | None = None
    caret: str | None = None
    line_highlight: str | None = Field(None, alias='lineHighlight')
    selection: str | None = None
    selection_foreground: str | None = Field(None, alias='selectionForeground')
    invisibles: str | None = None

    # Gutter
    gutter: str | None = None
    gutter_foreground: str | None = Field(None, alias='gutterForeground')

    # Guides
    guide: str | None = None
    active_guide: str | None = Field(None, alias='activeGuide')
    stack_guide: str | None = Field(None, alias='stackGuide')

    def __str__(self) -> str:
        return f'TMThemeGlobalSettings({pformat(self.model_dump(), indent=2)})'


class TMThemeSettings(BaseModel):
    """Settings for TextMate theme scopes."""

    foreground: str | None = None
    background: str | None = None
    font_style: str | None = Field(None, alias='fontStyle')

    def __str__(self) -> str:
        return f'TMThemeSettings({pformat(self.model_dump(), indent=2)})'


class TMThemeRule(BaseModel):
    """Rule configuration in TextMate themes."""

    name: str | None = None
    scope: str | None = None
    settings: TMThemeSettings

    def __str__(self) -> str:
        return f'TMThemeRule({pformat(self.model_dump(), indent=2)})'


class TMTheme(BaseModel):
    """
    Model representing a TextMate theme file (.tmTheme).

    This is a property list (plist) XML file that defines colors and styles
    for syntax highlighting in TextMate and other editors that support this
    format.
    """

    name: str
    settings: list[Union[dict[str, TMThemeGlobalSettings], TMThemeRule]]

    @classmethod
    def from_tm_theme(cls, file_path: Union[str, Path]) -> 'TMTheme':
        """Load and validate a TextMate theme from a tmTheme plist file."""
        if isinstance(file_path, str):
            file_path = Path(file_path)

        with open(file_path, 'rb') as f:
            theme_data = plistlib.load(f)
            return cls.model_validate(theme_data)

    def to_tm_theme(self, file_path: Union[str, Path]) -> None:
        """Save the theme as a TextMate tmTheme plist file."""
        if isinstance(file_path, str):
            file_path = Path(file_path)

        with open(file_path, 'wb') as f:
            # Exclude None values when dumping to plist
            data = self.model_dump(by_alias=True, exclude_none=True)
            plistlib.dump(data, f)

    def __str__(self) -> str:
        return f'TMTheme({pformat(self.model_dump(), indent=2)})'
