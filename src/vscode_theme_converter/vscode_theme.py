from pathlib import Path
from typing import Literal, Union

import json5
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self


class TokenColorSettings(BaseModel):
    foreground: str | None = None
    font_style: str | None = Field(None, alias='fontStyle')


class TokenColor(BaseModel):
    name: str | None = None
    scope: Union[str, list[str]] | None = None
    settings: TokenColorSettings


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
    colors: dict[str, str]
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
