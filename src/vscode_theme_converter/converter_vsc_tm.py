"""
Function to convert VSCode theme to tmTheme format.
"""

from vscode_theme_converter.conversion_mappings import (
    VSCODE_TO_TM_SETTINGS_MAP,
)
from vscode_theme_converter.tm_theme import (
    TMTheme,
    TMThemeGlobalSettings,
    TMThemeRule,
    TMThemeSettings,
)
from vscode_theme_converter.vscode_theme import VSCodeTheme


def convert_vscode_theme_to_tm_theme(
    vscode_theme: VSCodeTheme,
) -> TMTheme:
    """Convert VSCode theme to TextMate theme format."""

    # Create global settings by mapping VSCode colors to TM settings
    settings_dict = {}
    for vscode_key, color in vscode_theme.colors.items():
        if vscode_key in VSCODE_TO_TM_SETTINGS_MAP:
            tm_key = VSCODE_TO_TM_SETTINGS_MAP[vscode_key]
            settings_dict[tm_key] = color

    # Create global settings from mapped colors
    global_settings = TMThemeGlobalSettings(**settings_dict)

    # Convert token colors to rules
    rules = [
        TMThemeRule(
            name=token.name,
            scope=token.scope,
            settings=TMThemeSettings(
                foreground=token.settings.foreground,
                fontStyle=token.settings.font_style,
            ),
        )
        for token in vscode_theme.token_colors
    ]

    # Create theme with global settings first, then rules
    return TMTheme(
        name=vscode_theme.name or 'Converted Theme',
        settings=[{'settings': global_settings}, *rules],
    )
