import plistlib
import sys

import json5


def add_settings(tm_theme_default_settings, vsc_theme_colors):
    mappings = {
        "editorCursor.foreground": "caret",
        "editor.selectionBackground": "selection",
        "editor.lineHighlightBackground": "lineHighlight",
        "editor.foreground": "foreground",
        "editor.background": "background",
        "editorWhitespace.foreground": "invisibles",
    }

    for vsc_key, tm_key in mappings.items():
        if vsc_key in vsc_theme_colors:
            tm_theme_default_settings[tm_key] = vsc_theme_colors[vsc_key]


def convert(vsc_theme, input_file=None):
    theme_name = vsc_theme.get("name")
    if not theme_name and input_file:
        # Extract filename without extension as default name
        theme_name = input_file.split("/")[-1].split(".")[0]

    tm_theme = {
        "name": theme_name or "Converted VSCode Theme",
        "settings": vsc_theme["tokenColors"],
    }

    default_settings = next(
        (setting for setting in tm_theme["settings"] if "scope" not in setting), None
    )

    if not default_settings:
        tm_theme["settings"].insert(0, {"settings": {}})

    tm_theme_default_settings = tm_theme["settings"][0]["settings"]
    vsc_theme_colors = vsc_theme["colors"]

    add_settings(tm_theme_default_settings, vsc_theme_colors)

    new_settings = []
    for setting in tm_theme["settings"][1:]:
        if "scope" in setting:
            scope = setting["scope"]
            if isinstance(scope, list):
                for individual_scope in scope:
                    new_settings.append(
                        {
                            "scope": str(individual_scope),
                            "settings": setting["settings"].copy(),
                        }
                    )
            else:
                setting["scope"] = str(scope)
                new_settings.append(setting)
        else:
            new_settings.append(setting)

    tm_theme["settings"] = [tm_theme["settings"][0]] + new_settings
    return tm_theme


def main():
    if len(sys.argv) != 3:
        print("Usage: python vscToTm.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    with open(input_file, "r", encoding="utf-8") as f:
        vsc_theme = json5.loads(f.read())

    with open(sys.argv[2], "wb") as f:
        plistlib.dump(convert(vsc_theme, input_file), f)


if __name__ == "__main__":
    main()
