from pathlib import Path

import typer
from rich import print as rprint
from rich.style import Style

from .ansi_mapping import AnsiMapping, ColorMapping
from .contrast import get_contrast_ratio, get_contrast_ratio_rating
from .terminal import (
    AnsiColor,
    get_terminal_background_color,
    get_terminal_foreground_color,
)
from .vscode_theme import VSCodeTheme

app = typer.Typer(
    help=(
        'VSCode Theme Converter - Convert VSCode themes to other formats.\n\n'
        'Run a command with --help to see its options.'
    ),
    no_args_is_help=True,
)

#
# CLI Commands
#


@app.command()
def convert(
    input_file: Path = typer.Argument(
        ..., help='VSCode theme file (.json or .jsonc)'
    ),
    output_file: Path = typer.Argument(
        ..., help='Output TextMate theme file (.tmTheme)'
    ),
) -> None:
    """Convert a VSCode theme to TextMate format."""
    theme = VSCodeTheme.from_json(input_file)
    tm_theme = theme.to_tm_theme()
    tm_theme.to_tm_theme(output_file)
    typer.echo(f'Successfully converted {input_file} to {output_file}')


@app.command()
def ansi_map_gen(
    input_file: Path = typer.Argument(
        ..., help='VSCode theme file (.json or .jsonc)'
    ),
    output_file: Path = typer.Argument(
        ..., help='Output JSON file for color mappings'
    ),
) -> None:
    """Generate initial ANSI color mappings from a VSCode theme."""
    # Load theme
    theme = VSCodeTheme.from_json(input_file)

    # Generate color mapping
    mapping = theme.generate_ansi_mapping()

    # Save to JSON
    mapping.save_json(output_file)
    typer.echo(
        f'Generated ANSI color mapping in {output_file}\n'
        'Edit this file to customize the color assignments.'
    )


@app.command()
def ansi_map_show(
    mapping_file: Path = typer.Argument(..., help='ANSI mapping JSON file'),
    quiet: bool = typer.Option(
        False,
        '-q',
        '--quiet',
        help='Show only color codes and their ANSI mappings',
    ),
) -> None:
    """Display all colors and their ANSI mappings."""
    # Load mapping
    mapping = AnsiMapping.load_json(mapping_file)

    # Print header
    typer.echo(f'\nToken color mappings for theme: {mapping.theme_name}\n')

    def sort_key(item: tuple[str, ColorMapping]) -> tuple[int, str]:
        """Sort by ANSI color name, with unmapped last."""
        _, color_map = item
        if color_map.ansi_color is None:
            return (1, '')  # Unmapped colors go last
        return (0, color_map.ansi_color.name)

    # Print each color's info
    for idx, (color_code, color_map) in enumerate(
        sorted(mapping.token_color_mappings.items(), key=sort_key), start=1
    ):
        # Create styles
        hex_style = Style(color=color_code)

        if color_map.ansi_color is not None:
            ansi_color = color_map.ansi_color
            ansi_text = (
                f'[{ansi_color.rich_style}]'
                f'{ansi_color.get_color_code("")} {ansi_color.title}[/]'
            )
        else:
            ansi_text = 'Unmapped'

        # Print with color and index
        rprint(
            f'[{idx:2d}] ',
            f'[{hex_style}]■■■■ Abcd {color_code:<8}[/]',
            f' → {ansi_text:<15} (Used in {color_map.usage_count} places)',
        )

        if not quiet:
            if color_map.ui_settings:
                typer.echo('  UI Settings:')
                for setting in sorted(color_map.ui_settings):
                    typer.echo(f'    - {setting}')

            if color_map.scopes:
                typer.echo('  Scopes:')
                for scope in sorted(color_map.scopes):
                    typer.echo(f'    - {scope}')

            typer.echo('')  # Empty line between colors


@app.command()
def print_terminal_colors() -> None:
    """Show how the current terminal colors look."""

    def print_color(
        color_code: str,
        bg_color_code: str | None,
        style: Style,
        title: str,
    ) -> None:
        contrast_info = ''
        if bg_color_code is not None and color_code is not None:
            contrast_ratio = get_contrast_ratio(color_code, bg_color_code)
            contrast_rating = get_contrast_ratio_rating(contrast_ratio)
            contrast_info = f'\t→ {contrast_ratio:4.1f} ({contrast_rating})'

        # Print the color info
        rprint(
            f'    [on {style}]    [/]  ',
            f'[{style}]{color_code}[/]',
            f'  {title:<12}{contrast_info}',
        )

    # Print header
    typer.echo('\nCurrent Terminal Colors:\n')

    # Get terminal colors
    bg_color_code = get_terminal_background_color()
    fg_color_code = get_terminal_foreground_color()

    # Print terminal default colors
    if bg_color_code is not None:
        print_color(bg_color_code, None, Style(), 'Background')

    if fg_color_code is not None:
        print_color(
            fg_color_code,
            bg_color_code,
            Style(color=fg_color_code),
            'Foreground',
        )

    if bg_color_code is not None or fg_color_code is not None:
        typer.echo('')

    # Print each color family
    for color in AnsiColor.iter_by_family():
        print_color(
            color.color_code_title,
            bg_color_code,
            color.rich_style,
            color.title,
        )

        # Add space between families if this was a bright variant
        if color.is_bright:
            typer.echo('')


@app.command()
def check_contrast(
    background_color: str = typer.Argument(..., help='Background color (hex)'),
    foreground_colors: list[str] = typer.Argument(
        ..., help='Foreground colors (hex)'
    ),
) -> None:
    """
    Check contrast ratio between background and multiple foreground colors.
    """

    try:
        bg_style = get_color_style(None, background_color)
        rprint(f'Background: {background_color} [{bg_style}]■■■■[/]\n')
    except Exception as e:
        rprint(f'[red]Error:[/] {e}')
        return

    rprint('Foreground Colors:')
    for color in foreground_colors:
        try:
            fg_style = get_color_style(color, background_color)
        except Exception as e:
            rprint(f'\t{color} is invalid: {e}')
            continue

        try:
            ratio = get_contrast_ratio(color, background_color)
            rating = get_contrast_ratio_rating(ratio)
        except Exception:
            ratio = -1
            rating = '(N/A)'

        rprint(
            f'\t[{fg_style}]{color:<8} ■■■■[/]',
            f' → {ratio:4.1f} ({rating})',
        )


#
# Helper Functions
#


def get_color_style(color: str | None, bg_color: str | None) -> Style:
    """Get a Rich Style object for a color."""

    def ensure_hex_prefix(c: str | None) -> str | None:
        if c is not None and len(c) == 6 and c.startswith('#') is False:
            return f'#{c}'
        return c

    color = ensure_hex_prefix(color)
    bg_color = ensure_hex_prefix(bg_color)

    return Style(color=color, bgcolor=bg_color)


#
# CLI Entry Point
#


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == '__main__':
    main()
