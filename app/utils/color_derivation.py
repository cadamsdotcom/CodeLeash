"""Color derivation utilities for email template theming.

Derives accent colors from a primary brand color using OKLCH color space
for perceptually uniform results. This is a Python port of the TypeScript
implementation in src/utils/colorDerivation.ts.
"""

import math


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string to RGB components."""
    cleaned = hex_color.lstrip("#")
    r = int(cleaned[0:2], 16)
    g = int(cleaned[2:4], 16)
    b = int(cleaned[4:6], 16)
    return r, g, b


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB components to a hex color string."""
    r = round(max(0, min(255, r)))
    g = round(max(0, min(255, g)))
    b = round(max(0, min(255, b)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _srgb_to_linear(c: int) -> float:
    """Convert sRGB to linear RGB (remove gamma correction)."""
    s = c / 255
    if s <= 0.04045:
        return s / 12.92
    return ((s + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> int:
    """Convert linear RGB to sRGB (apply gamma correction)."""
    s = c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return round(s * 255)


def rgb_to_oklch(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Convert RGB to OKLCH color space via OKLab intermediate."""
    lr = _srgb_to_linear(r)
    lg = _srgb_to_linear(g)
    lb = _srgb_to_linear(b)

    # Linear RGB to LMS (cone responses)
    l_ = 0.4122214708 * lr + 0.5363325363 * lg + 0.0514459929 * lb
    m_ = 0.2119034982 * lr + 0.6806995451 * lg + 0.1073969566 * lb
    s_ = 0.0883024619 * lr + 0.2817188376 * lg + 0.6299787005 * lb

    # Apply cube root
    l__ = math.copysign(abs(l_) ** (1 / 3), l_) if l_ != 0 else 0.0
    m__ = math.copysign(abs(m_) ** (1 / 3), m_) if m_ != 0 else 0.0
    s__ = math.copysign(abs(s_) ** (1 / 3), s_) if s_ != 0 else 0.0

    # LMS to OKLab
    ok_l = 0.2104542553 * l__ + 0.7936177850 * m__ - 0.0040720468 * s__
    ok_a = 1.9779984951 * l__ - 2.4285922050 * m__ + 0.4505937099 * s__
    ok_b = 0.0259040371 * l__ + 0.7827717662 * m__ - 0.8086757660 * s__

    # OKLab to OKLCH
    c = math.sqrt(ok_a * ok_a + ok_b * ok_b)
    h = math.degrees(math.atan2(ok_b, ok_a))
    if h < 0:
        h += 360

    return ok_l, c, h


def oklch_to_rgb(ok_l: float, c: float, h: float) -> tuple[int, int, int]:
    """Convert OKLCH to RGB color space."""
    h_rad = math.radians(h)
    ok_a = c * math.cos(h_rad)
    ok_b = c * math.sin(h_rad)

    # OKLab to LMS
    l__ = ok_l + 0.3963377774 * ok_a + 0.2158037573 * ok_b
    m__ = ok_l - 0.1055613458 * ok_a - 0.0638541728 * ok_b
    s__ = ok_l - 0.0894841775 * ok_a - 1.2914855480 * ok_b

    # Apply cube
    l_ = l__ * l__ * l__
    m_ = m__ * m__ * m__
    s_ = s__ * s__ * s__

    # LMS to linear RGB
    lr = 4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_
    lg = -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_
    lb = -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_

    return _linear_to_srgb(lr), _linear_to_srgb(lg), _linear_to_srgb(lb)


def derive_accent_color(primary_hex: str) -> str:  # check_unused_code: ignore
    """Derive an accent color from a primary color.

    The accent is a lighter, more vibrant version of the primary color.
    Derivation (in OKLCH): L=0.87, C=2.5x (capped at 0.25), same hue.
    """
    r, g, b = hex_to_rgb(primary_hex)
    _l, c, h = rgb_to_oklch(r, g, b)

    accent_l = 0.87
    accent_c = min(0.25, c * 2.5)
    accent_h = h

    ar, ag, ab = oklch_to_rgb(accent_l, accent_c, accent_h)
    return rgb_to_hex(ar, ag, ab)


def derive_accent_color2(primary_hex: str) -> str:
    """Derive a secondary accent color from a primary color.

    Medium brightness suitable for buttons with white text.
    Derivation (in OKLCH): L=0.55, C=1.8x (capped at 0.18), same hue.
    """
    r, g, b = hex_to_rgb(primary_hex)
    _l, c, h = rgb_to_oklch(r, g, b)

    accent_l = 0.55
    accent_c = min(0.18, c * 1.8)
    accent_h = h

    ar, ag, ab = oklch_to_rgb(accent_l, accent_c, accent_h)
    return rgb_to_hex(ar, ag, ab)


def get_contrast_text_color(background_hex: str) -> str:
    """Determine appropriate text color (black or white) for a background.

    Returns black for light backgrounds (L > 0.65), white for dark.
    """
    r, g, b = hex_to_rgb(background_hex)
    ok_l, _c, _h = rgb_to_oklch(r, g, b)
    return "#000000" if ok_l > 0.65 else "#ffffff"


# Brand colors for email templates
BRAND_COLORS: dict[str, str] = {
    "button": "#46B260",  # Grass green - for CTAs
    "button_text": "#FFFFFF",  # White text on default green button
    "heading": "#19351D",  # Moss green - for headings
    "text": "#333735",  # Dark gray - for body text
    "muted": "#A0A39F",  # Mid gray - for footer text
    "link": "#2D6D4D",  # Pine green - for links
    "background": "#F8F9FA",  # Light gray - for backgrounds
    "white": "#FFFFFF",  # White
}


def derive_email_brand_colors(  # check_unused_code: ignore
    primary_hex: str,
) -> dict[str, str]:
    """Derive a complete set of email brand colors from a primary color.

    Starts from BRAND_COLORS and overrides heading/button/link with colors
    derived from the primary color. Neutral colors are kept at their defaults.
    """
    accent2 = derive_accent_color2(primary_hex)
    return {
        **BRAND_COLORS,
        "button": accent2,
        "button_text": get_contrast_text_color(accent2),
        "heading": primary_hex.lower(),
        "link": accent2,
    }
