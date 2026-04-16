from __future__ import annotations

import os
import shutil
import sys
import time

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
CLEAR_LINE = "\033[K"
UP_ONE = "\033[F"


class Palette:
    INK = "\033[38;5;252m"
    SUBTLE = "\033[38;5;245m"
    ACCENT = "\033[38;5;110m"
    SUCCESS = "\033[38;5;114m"
    WARNING = "\033[38;5;180m"
    ERROR = "\033[38;5;210m"


USE_COLOR = sys.stdout.isatty()


def set_color(enabled: bool) -> None:
    global USE_COLOR
    USE_COLOR = enabled


def style(text: str, *codes: str) -> str:
    if not USE_COLOR or not codes:
        return text
    return "".join(codes) + text + RESET


def width(maximum: int = 78) -> int:
    columns = shutil.get_terminal_size((maximum, 20)).columns
    return max(48, min(columns, maximum))


def rule(label: str = "") -> str:
    size = width()
    if not label:
        return style("-" * size, Palette.SUBTLE)

    tag = f" {label} "
    filler = max(0, size - len(tag))
    left = filler // 2
    right = filler - left
    line = f"{'-' * left}{tag}{'-' * right}"
    return style(line[:size], Palette.SUBTLE)


def hero() -> str:
    credits = style(" @ lvlify", Palette.SUBTLE)
    return "\n".join(["", f"gmailgen{credits}", "", ""])


def key_value(key: str, value: str) -> str:
    left = style(key.ljust(12), Palette.SUBTLE)
    right = style(value, Palette.INK)
    return f"{left} {right}"


def note(message: str, tone: str = "info") -> str:
    palette = {
        "info": Palette.ACCENT,
        "success": Palette.SUCCESS,
        "warning": Palette.WARNING,
        "error": Palette.ERROR,
    }.get(tone, Palette.ACCENT)
    return style(message, palette)


def prompt(label: str, default: str | None = None) -> str:
    hint = "" if default is None else style(f"   [{default}]", Palette.SUBTLE)
    return input(f"{style(label, BOLD, Palette.INK)}{hint}:   ").strip()


def flash_error(message: str) -> None:
    print(f"{UP_ONE}{CLEAR_LINE}{style(message, RED)}", end="\r")
    time.sleep(1)
    print(CLEAR_LINE, end="\r")


def clear() -> None:
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")
