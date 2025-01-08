"""
Mappings for converting between VSCode and TextMate themes.

Stored in a separate module to avoid circular imports.
"""

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
