"""
Helpers to calculate WCAG contrast ratio.
"""


def get_contrast_ratio(fg: str, bg: str) -> float:
    """
    Calculate contrast ratio between two colors using the WCAG method.

    This is what Google Chrome shows in the developer tools.
    """
    fg_rgb = get_rgb(fg)
    bg_rgb = get_rgb(bg)

    fg_lum = get_luminance(*fg_rgb)
    bg_lum = get_luminance(*bg_rgb)

    lighter = max(fg_lum, bg_lum)
    darker = min(fg_lum, bg_lum)

    return (lighter + 0.05) / (darker + 0.05)


def get_contrast_ratio_rating(ratio: float) -> str:
    """Get the WCAG rating for a contrast ratio."""

    if ratio >= 7.0:
        return 'AAA'
    elif ratio >= 4.5:
        return 'AA'
    else:
        return '✗'


def get_rgb(hex_color: str) -> tuple[float, float, float]:
    """Convert hex color to RGB values between 0 and 1."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)


def get_luminance(r: float, g: float, b: float) -> float:
    """Calculate relative luminance."""

    def adjust(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)
