"""
Function to convert VSCode theme to tmTheme format.
"""

from vscode_theme_converter.conversion_mappings import (
    VSCODE_TO_TM_SETTINGS_MAP,
)
from vscode_theme_converter.tm_theme import (
    TMTheme,
    TMThemeGlobalSettings,
    TMThemeSettingsItem,
    TMThemeTokenRule,
    TMThemeTokenRuleSettings,
)
from vscode_theme_converter.vscode_theme import VSCodeTheme


def convert_vscode_theme_to_tm_theme(
    vscode_theme: VSCodeTheme,
) -> TMTheme:
    """Convert VSCode theme to TextMate theme format."""

    # Create global settings by mapping VSCode colors to TM settings
    global_settings_dict: dict[str, str] = {}
    for vscode_key, color in vscode_theme.colors.items():
        if vscode_key in VSCODE_TO_TM_SETTINGS_MAP:
            tm_key = VSCODE_TO_TM_SETTINGS_MAP[vscode_key]
            global_settings_dict[tm_key] = color
    global_settings_item = TMThemeGlobalSettings(settings=global_settings_dict)

    settings: list[TMThemeSettingsItem] = [global_settings_item]

    for token in vscode_theme.token_colors:
        settings.append(
            TMThemeTokenRule(
                name=token.name,
                scope=token.scope,
                settings=TMThemeTokenRuleSettings(
                    foreground=token.settings.foreground,
                    fontStyle=token.settings.font_style,
                ),
            )
        )

    return TMTheme(
        name=vscode_theme.name or 'Converted Theme',
        settings=settings,
    )
