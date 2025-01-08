from pathlib import Path
from typing import Any, Literal

import json5
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self

from .ansi_mapping import AnsiMapping, ColorMapping


class TokenColorSettings(BaseModel):
    foreground: str | None = None
    font_style: str | None = Field(None, alias='fontStyle')


class TokenColor(BaseModel):
    """A syntax highlighting rule."""

    name: str | None = None
    scope: str | None = None
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

    def generate_ansi_mapping(self) -> AnsiMapping:
        """Generate initial ANSI color mappings from theme colors."""
        # Track all unique colors and their usage
        color_mapping_dict: dict[str, ColorMapping] = {}

        # Process token colors
        for token in self.token_colors:
            if not token.settings.foreground:
                continue

            color = token.settings.foreground

            # Create or update mapping
            if color not in color_mapping_dict:
                mapping = ColorMapping(color_code=color)
                color_mapping_dict[color] = mapping

            # Update scopes
            if token.scope:
                if isinstance(token.scope, list):
                    color_mapping_dict[color].scopes.update(token.scope)
                else:
                    color_mapping_dict[color].scopes.add(token.scope)

        return AnsiMapping(
            theme_name=self.name or 'Unnamed Theme',
            color_mappings=list(color_mapping_dict.values()),
        )

    def apply_ansi_mapping(self, mapping: AnsiMapping) -> 'VSCodeTheme':
        """
        Create a new theme with colors replaced by their ANSI mappings.

        Args:
            mapping: ANSI color mapping to apply

        Returns:
            New theme with ANSI colors
        """
        # Create new theme
        ansi_theme = self.model_copy()

        # Get color mappings
        color_map = mapping.token_color_mappings

        # Replace colors in UI settings
        for field_name, field in self.colors.model_fields.items():
            color = getattr(self.colors, field_name)
            if not color:
                continue

            if color in color_map:
                ansi_color = color_map[color].ansi_color
                if ansi_color is not None:
                    setattr(ansi_theme.colors, field_name, ansi_color.ansi_hex)

        # Replace colors in token colors
        for token in ansi_theme.token_colors:
            if not token.settings.foreground:
                continue

            color = token.settings.foreground
            if color in color_map:
                ansi_color = color_map[color].ansi_color
                if ansi_color is not None:
                    token.settings.foreground = ansi_color.ansi_hex

        return ansi_theme

    @field_validator('token_colors', mode='before')
    @classmethod
    def normalize_token_colors(
        cls, token_colors: list[dict[str, Any]]
    ) -> list[TokenColor]:
        """
        Some VSCode themes import other themes and override their token
        colors, but the `Generate Color Theme` command doesn't deduplicate
        the scopes.

        VSCode just uses the last instance of a scope.

        So we need to do the same thing here. We do it at parsing time because
        it reduces the number of colors we need to map to convert to ANSI.

        Normalize token colors by:
        1. Splitting list-based scopes into separate rules
        2. Keeping only the last rule for each scope
        """
        # Track the last rule for each scope
        scope_map: dict[str, TokenColor] = {}

        for token_data in token_colors:
            name = token_data.get('name')
            scopes = token_data.get('scope')
            settings = token_data.get('settings')

            # Skip rules without scopes or settings
            if scopes is None or settings is None:
                continue

            if isinstance(scopes, str):
                scopes = [scopes]

            for scope in scopes:
                rule = TokenColor(
                    name=name,
                    scope=scope,
                    settings=settings,
                )
                scope_map[scope] = rule

        return list(scope_map.values())
