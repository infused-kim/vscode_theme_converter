import plistlib
from pathlib import Path
from pprint import pformat
from typing import Literal, TypeAlias, Union

from pydantic import BaseModel, Field

from .ansi_mapping import AnsiColor, AnsiMapping


class TMThemeTokenRuleSettings(BaseModel):
    """Settings for TextMate theme scopes."""

    foreground: str | None = None
    background: str | None = None
    font_style: str | None = Field(None, alias='fontStyle')

    def __str__(self) -> str:
        return f'TMThemeSettings({pformat(self.model_dump(), indent=2)})'


class TMThemeTokenRule(BaseModel):
    """Token rule configuration in TextMate themes."""

    type: Literal['token'] = 'token'
    name: str | None = None
    scope: str | None = None
    settings: TMThemeTokenRuleSettings

    def __str__(self) -> str:
        return f'TMThemeRule({pformat(self.model_dump(), indent=2)})'


class TMThemeGlobalSettings(BaseModel):
    """Global settings for TextMate themes."""

    type: Literal['global'] = 'global'
    settings: dict[str, str]


# Type for a single settings item in a TMTheme
TMThemeSettingsItem: TypeAlias = TMThemeGlobalSettings | TMThemeTokenRule


class TMTheme(BaseModel):
    """
    Model representing a TextMate theme file (.tmTheme).

    This is a property list (plist) XML file that defines colors and styles
    for syntax highlighting in TextMate and other editors that support this
    format.
    """

    name: str
    settings: list[TMThemeSettingsItem]

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

    def apply_ansi_mapping(self, mapping: AnsiMapping) -> 'TMTheme':
        """Create a new theme with colors replaced by their ANSI mappings."""
        # Create new theme
        ansi_theme = self.model_copy()
        ansi_color_map = {
            mapping.color_code: mapping for mapping in mapping.color_mappings
        }

        first_setting: TMThemeSettingsItem = ansi_theme.settings[0]
        if isinstance(first_setting, TMThemeGlobalSettings):
            global_settings: TMThemeGlobalSettings = first_setting
        else:
            raise ValueError(
                'First setting in TMTheme is not a global settings dict'
            )

        # Adjust global settings
        unmapped_colors: list[str] = []
        for field_name, color in global_settings.settings.items():
            if not color:
                continue
            if color in ansi_color_map:
                ansi_color = ansi_color_map[color].ansi_color
                if ansi_color is None:
                    unmapped_colors.append(color)
                    continue
                global_settings.settings[field_name] = (
                    self._convert_ansi_to_tm_hex(ansi_color)
                )
            else:
                unmapped_colors.append(color)

        # Process remaining settings (token rules)
        for setting in ansi_theme.settings[1:]:
            if not isinstance(setting, TMThemeTokenRule):
                continue
            if not setting.settings.foreground:
                continue
            color = setting.settings.foreground
            if color in ansi_color_map:
                ansi_color = ansi_color_map[color].ansi_color
                if ansi_color is None:
                    unmapped_colors.append(color)
                    continue
                setting.settings.foreground = self._convert_ansi_to_tm_hex(
                    ansi_color
                )
            else:
                unmapped_colors.append(color)

        # Update theme name
        ansi_theme.name = f'{self.name} (ANSI)'

        return ansi_theme

    def _convert_ansi_to_tm_hex(self, ansi_color: AnsiColor) -> str:
        """
        Convert an ANSI color to a TextMate hex color in the format bat
        expects it.
        """
        hex = f'#{ansi_color.num:02x}000000'
        if ansi_color.is_foreground:
            hex = '#00000001'
        elif ansi_color.is_background:
            hex = '#00000002'
        else:
            hex = f'#{ansi_color.num:02x}000000'

        return hex
