from pathlib import Path

import typer

from .vscode_theme import VSCodeTheme

app = typer.Typer(
    help=(
        'VSCode Theme Converter - Convert VSCode themes to other formats.\n\n'
        'Run a command with --help to see its options.'
    ),
    no_args_is_help=True,  # Show help if no command is given
)


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
    # Load and convert theme
    theme = VSCodeTheme.from_json(input_file)
    tm_theme = theme.to_tm_theme()

    # Save converted theme
    tm_theme.to_tm_theme(output_file)
    typer.echo(f'Successfully converted {input_file} to {output_file}')


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == '__main__':
    main()
