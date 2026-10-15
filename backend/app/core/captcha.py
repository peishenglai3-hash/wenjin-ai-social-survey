"""CAPTCHA module — SVG-based text CAPTCHA for bot prevention.

Generates a random 4-character alphanumeric string rendered as SVG with:
- Background noise (random lines)
- Slight character rotation
- Color variation
- Warped/curved text path

The answer is stored in-memory with a short TTL (5 minutes).
"""

import base64
import io
import math
import random
import string
import time
from dataclasses import dataclass, field


# ── In-memory CAPTCHA store ────────────────────────────────────────
@dataclass
class CaptchaEntry:
    answer: str
    created_at: float = field(default_factory=time.time)


# {token: CaptchaEntry}
_captcha_store: dict[str, CaptchaEntry] = {}

CAPTCHA_TTL_SECONDS = 300  # 5 minutes
CAPTCHA_CLEANUP_INTERVAL = 60  # Clean expired entries every N creates
_cleanup_counter = 0


def _cleanup_expired():
    """Remove expired CAPTCHA entries."""
    now = time.time()
    expired = [t for t, e in _captcha_store.items() if now - e.created_at > CAPTCHA_TTL_SECONDS]
    for t in expired:
        del _captcha_store[t]


def _generate_token() -> str:
    """Generate a random CAPTCHA token."""
    return base64.urlsafe_b64encode(random.randbytes(24)).decode("ascii")


def _random_color(base: int, variance: int = 40) -> str:
    """Generate a hex color with variation around base."""
    r = min(255, max(0, base + random.randint(-variance, variance)))
    g = min(255, max(0, base + random.randint(-variance, variance)))
    b = min(255, max(0, base + random.randint(-variance, variance)))
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_captcha() -> tuple[str, str, str]:
    """Generate a new CAPTCHA.

    Returns:
        (captcha_token, answer_text, svg_markup)
    """
    global _cleanup_counter
    _cleanup_counter += 1
    if _cleanup_counter >= CAPTCHA_CLEANUP_INTERVAL:
        _cleanup_expired()
        _cleanup_counter = 0

    # Generate answer: 4 chars, avoid confusable characters
    charset = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # No 0/O/1/I
    answer = "".join(random.choices(charset, k=4))

    # Store answer
    token = _generate_token()
    _captcha_store[token] = CaptchaEntry(answer=answer)

    # Generate SVG
    width = 160
    height = 60
    chars = list(answer)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        # Background
        f'<rect width="{width}" height="{height}" fill="#f8f9fa" rx="6"/>',
    ]

    # Background noise — random lines
    for _ in range(6):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        stroke = _random_color(180, 30)
        svg_parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{stroke}" stroke-width="1" opacity="0.5"/>'
        )

    # Background dots
    for _ in range(30):
        cx = random.randint(5, width - 5)
        cy = random.randint(5, height - 5)
        r = random.uniform(0.5, 1.5)
        fill = _random_color(160, 50)
        svg_parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" opacity="0.4"/>'
        )

    # Characters with rotation
    char_width = width / (len(chars) + 1)
    for i, ch in enumerate(chars):
        x = char_width * (i + 1)
        # Slight vertical offset
        y = height / 2 + random.randint(-8, 8)
        # Rotation between -20 and +20 degrees
        angle = random.randint(-20, 20)
        # Font size variation
        font_size = random.randint(24, 30)
        # Color
        color = _random_color(40, 30)  # Dark base for contrast

        svg_parts.append(
            f'<text x="{x:.0f}" y="{y:.0f}" '
            f'font-family="monospace" font-size="{font_size}" '
            f'fill="{color}" '
            f'text-anchor="middle" dominant-baseline="central" '
            f'transform="rotate({angle}, {x:.0f}, {y:.0f})" '
            f'font-weight="bold" '
            f'opacity="0.85">'
            f'{ch}</text>'
        )

    # Border
    svg_parts.append(
        f'<rect width="{width - 1}" height="{height - 1}" '
        f'x="0.5" y="0.5" fill="none" stroke="#d0d5dd" stroke-width="1" rx="6"/>'
    )

    svg_parts.append("</svg>")
    svg = "\n".join(svg_parts)

    return token, answer, svg


def verify_captcha(token: str, answer: str) -> bool:
    """Verify a CAPTCHA answer. Consumes the token (one-time use).

    Returns:
        True if the answer matches and token is valid.
    """
    global _cleanup_counter
    entry = _captcha_store.get(token)
    if entry is None:
        return False

    now = time.time()
    if now - entry.created_at > CAPTCHA_TTL_SECONDS:
        del _captcha_store[token]
        return False

    # Case-insensitive comparison, trim whitespace
    is_valid = entry.answer.upper() == answer.strip().upper()

    # One-time use: always delete after verification attempt
    del _captcha_store[token]

    return is_valid
