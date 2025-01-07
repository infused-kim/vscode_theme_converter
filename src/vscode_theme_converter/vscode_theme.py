from pathlib import Path
from typing import Literal, Union

import json5
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from .ansi_mapping import AnsiMapping, ColorMapping
from .tm_theme import (
    TMTheme,
    TMThemeGlobalSettings,
    TMThemeRule,
    TMThemeSettings,
)


class TokenColorSettings(BaseModel):
    foreground: str | None = None
    font_style: str | None = Field(None, alias='fontStyle')


class TokenColor(BaseModel):
    name: str | None = None
    scope: Union[str, list[str]] | None = None
    settings: TokenColorSettings


class Colors(BaseModel):
    """Expected colors in a VSCode theme."""

    class Config:
        populate_by_name = True

    # Editor colors
    editor_foreground: str | None = Field(None, alias='editor.foreground')
    editor_background: str | None = Field(None, alias='editor.background')
    editor_cursor_foreground: str | None = Field(
        None, alias='editorCursor.foreground'
    )
    editor_selection_background: str | None = Field(
        None, alias='editor.selectionBackground'
    )
    editor_line_highlight_background: str | None = Field(
        None, alias='editor.lineHighlightBackground'
    )
    editor_whitespace_foreground: str | None = Field(
        None, alias='editorWhitespace.foreground'
    )

    # Terminal colors
    terminal_foreground: str | None = Field(None, alias='terminal.foreground')
    terminal_cursor_foreground: str | None = Field(
        None, alias='terminalCursor.foreground'
    )

    # Additional colors
    other_colors: dict[str, str] = Field(default_factory=dict)


class VSCodeTheme(BaseModel):
    """
    Model representing a VSCode color theme JSONC file.

    This file is not the raw theme file you find in repos or the VSCode
    codebase.

    These files can contain include statements that point to other files.

    Instead it should be generated using the VSC command:
        `Developer: Generate Color Theme From Current Settings`
    """

    class Config:
        populate_by_name = True

    json_schema: str | None = Field(None, alias='$schema')
    type: Literal['light', 'dark'] | None = None
    name: str | None = None
    semantic_highlighting: bool | None = Field(
        None, alias='semanticHighlighting'
    )
    semantic_token_colors: dict[str, str] | None = Field(
        None, alias='semanticTokenColors'
    )
    colors: Colors
    token_colors: list[TokenColor] = Field(alias='tokenColors')

    @model_validator(mode='after')
    def check_no_includes(self) -> Self:
        """Ensure this is a compiled theme without includes."""
        values = self.model_dump()
        if 'include' in values:
            raise ValueError(
                'This converter should be used with compiled theme files that '
                "don't contain any `include` keys.\n\n"
                "Use VSCode's `Developer: Generate Color Theme From Current "
                'Settings` to generate a compiled theme file.'
            )
        return self

    @classmethod
    def from_json(cls, json_path: str | Path) -> Self:
        """Load and validate a VSCode theme from a JSON(C) file."""

        if isinstance(json_path, str):
            json_path = Path(json_path)

        with open(json_path, 'r', encoding='utf-8') as f:
            theme_data = json5.loads(f.read())

        theme = cls.model_validate(theme_data)

        if theme.name is None:
            theme.name = json_path.stem

        return theme

    def to_tm_theme(self) -> TMTheme:
        """Convert VSCode theme to TextMate theme format."""
        # Create global settings from our colors
        global_settings = TMThemeGlobalSettings(
            background=self.colors.editor_background,
            foreground=self.colors.editor_foreground,
            caret=self.colors.editor_cursor_foreground,
            selection=self.colors.editor_selection_background,
            lineHighlight=self.colors.editor_line_highlight_background,
            invisibles=self.colors.editor_whitespace_foreground,
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
            for token in self.token_colors
        ]

        # Create theme with global settings first, then rules
        return TMTheme(
            name=self.name or 'Converted Theme',
            settings=[{'settings': global_settings}, *rules],
        )

    def generate_ansi_mapping(self) -> AnsiMapping:
        """Generate initial ANSI color mappings from theme colors."""
        token_color_mappings: dict[str, ColorMapping] = {}

        # Collect colors from token colors
        for token in self.token_colors:
            if token.settings.foreground:
                color = token.settings.foreground
                if color not in token_color_mappings:
                    token_color_mappings[color] = ColorMapping(
                        color_code=color
                    )
                if token.scope:
                    token_color_mappings[color].scopes.append(
                        token.scope
                        if isinstance(token.scope, str)
                        else ', '.join(token.scope)
                    )

        return AnsiMapping(
            theme_name=self.name or 'Unnamed Theme',
            token_color_mappings=token_color_mappings,
        )
