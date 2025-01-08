"""
Function to convert VSCode theme to tmTheme format.
"""

from vscode_theme_converter.tm_theme import (
    TMTheme,
    TMThemeGlobalSettings,
    TMThemeRule,
    TMThemeSettings,
)
from vscode_theme_converter.vscode_theme import VSCodeTheme

# Mapping of TextMate global settings to VSCode editor settings
# From: https://www.sublimetext.com/docs/color_schemes_tmtheme.html#global_settings
TM_TO_VSCODE_SETTINGS_MAP = {
    # Core colors
    'background': 'editor.background',
    'foreground': 'editor.foreground',
    'caret': 'editorCursor.foreground',
    'lineHighlight': 'editor.lineHighlightBackground',
    # Selection
    'selection': 'editor.selectionBackground',
    'selectionForeground': 'editor.selectionForeground',
    'selectionBorder': None,  # No direct equivalent
    'inactiveSelection': 'editor.inactiveSelectionBackground',
    'inactiveSelectionForeground': None,  # No direct equivalent
    # Find
    'highlight': 'editor.findMatchBorder',
    'findHighlight': 'editor.findMatchBackground',
    'findHighlightForeground': 'editor.findMatchForeground',
    'guide': 'editorIndentGuide.background',
    'activeGuide': 'editorIndentGuide.activeBackground',
    'stackGuide': None,
    'bracketsOptions': None,  # VSCode uses different bracket highlighting system
    'bracketsForeground': None,
    'bracketContentsOptions': None,
    'bracketContentsForeground': None,
    # Tags
    'tagsOptions': None,  # VSCode uses different tag highlighting system
    'tagsForeground': None,
    # Shadows
    'shadow': None,  # No direct equivalent
    'shadowWidth': None,  # No direct equivalent
    # Accents
    'misspelling': None,  # No direct equivalent
    'minimapBorder': None,  # Different in VSCode
    'accent': None,  # No direct equivalent
    # Gutter
    'gutter': 'editorGutter.background',
    'gutterForeground': 'editorLineNumber.foreground',
}

VSCODE_TO_TM_SETTINGS_MAP = {
    value: key
    for key, value in TM_TO_VSCODE_SETTINGS_MAP.items()
    if value is not None
}


def convert_vscode_theme_to_tm_theme(
    vscode_theme: VSCodeTheme,
) -> TMTheme:
    """Convert VSCode theme to TextMate theme format."""

    # Create global settings from our colors
    global_settings = TMThemeGlobalSettings(
        background=vscode_theme.colors.editor_background,
        foreground=vscode_theme.colors.editor_foreground,
        caret=vscode_theme.colors.editor_cursor_foreground,
        selection=vscode_theme.colors.editor_selection_background,
        lineHighlight=vscode_theme.colors.editor_line_highlight_background,
        invisibles=vscode_theme.colors.editor_whitespace_foreground,
        selectionForeground=None,
        gutterForeground=None,
        activeGuide=None,
        stackGuide=None,
    )

    # Convert token colors to rules
    rules = [
        TMThemeRule(
            name=token.name,
            scope=', '.join(token.scope)
            if isinstance(token.scope, list)
            else token.scope,
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
