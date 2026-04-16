from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys

from .core import GenerationRequest, GenerationResult, GmailGenError, generate_aliases, parse_email
from .terminal import BOLD, Palette, clear, flash_error, hero, key_value, note, prompt, rule, set_color, style


@dataclass(frozen=True)
class RunConfiguration:
    request: GenerationRequest
    output_path: Path
    preview: int
    emit_stdout: bool
    overwrite: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gmailgen",
        description="Generate Gmail aliases with dotted and plus-address variants.",
    )
    parser.add_argument("email", nargs="?", help="Base Gmail address.")
    parser.add_argument("-n", "--count", type=int, help="How many aliases to generate.")
    parser.add_argument(
        "-m",
        "--mode",
        choices=("dots", "plus", "both"),
        default="both",
        help="Alias strategy to use.",
    )
    parser.add_argument("-o", "--output", default="aliases.txt", help="Output file path.")
    parser.add_argument("--preview", type=int, default=12, help="Preview line count.")
    parser.add_argument("--stdout", action="store_true", help="Print all aliases to stdout.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead.")
    parser.add_argument("--shuffle", action="store_true", help="Shuffle aliases after generation.")
    parser.add_argument("--seed", type=int, help="Seed value used with --shuffle.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output without asking.")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    set_color(not args.no_color)

    try:
        configuration = _resolve_run_configuration(parser, args)
        result = generate_aliases(configuration.request)

        if not args.json:
            _render_summary(result, configuration.output_path)

        _write_aliases(configuration.output_path, result.aliases, overwrite=configuration.overwrite)

        if args.json:
            _print_json_payload(result, configuration.output_path)
            return 0

        _render_preview(result.aliases, configuration.preview)
        print(note(f"saved {len(result.aliases)} aliases to {configuration.output_path.resolve()}", "success"))

        if configuration.emit_stdout:
            print("\n".join(result.aliases))

        return 0
    except GmailGenError as error:
        print(note(str(error), "error"), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print()
        print(note("cancelled", "warning"), file=sys.stderr)
        return 130


def _resolve_run_configuration(parser: argparse.ArgumentParser, args: argparse.Namespace) -> RunConfiguration:
    if args.email is None and args.count is None and not args.json:
        request, output_path, preview, emit_stdout, overwrite = _interactive_session()
        return RunConfiguration(
            request=request,
            output_path=output_path,
            preview=preview,
            emit_stdout=emit_stdout,
            overwrite=overwrite,
        )

    if args.email is None:
        parser.error("email is required outside interactive mode")
    if args.count is None:
        parser.error("--count is required outside interactive mode")

    return RunConfiguration(
        request=GenerationRequest(
            email=args.email,
            count=args.count,
            mode=args.mode,
            shuffle=args.shuffle,
            seed=args.seed,
        ),
        output_path=Path(args.output),
        preview=max(0, args.preview),
        emit_stdout=args.stdout,
        overwrite=args.overwrite,
    )


def _print_json_payload(result: GenerationResult, output_path: Path) -> None:
    payload = {
        "canonical_email": result.identity.canonical_email,
        "mode": result.request.mode,
        "count": len(result.aliases),
        "output": str(output_path.resolve()),
        "aliases": result.aliases,
    }
    print(json.dumps(payload, indent=2))


def _interactive_session() -> tuple[GenerationRequest, Path, int, bool, bool]:
    clear()
    print(hero())

    while True:
        email = _required_prompt("email", "name@gmail.com")
        try:
            parse_email(email)
            break
        except GmailGenError as error:
            flash_error(f"error: {error}")

    count = _prompt_count()
    mode = _prompt_mode()
    output_raw = prompt("output", "aliases.txt") or "aliases.txt"
    output_path = Path(output_raw)

    overwrite = False
    if output_path.exists():
        if output_path.stat().st_size > 0:
            overwrite = _prompt_yes_no("overwrite existing file", default=False)
        else:
            overwrite = True

    request = GenerationRequest(email=email, count=count, mode=mode)
    return request, output_path, 0, False, overwrite


def _render_summary(result: GenerationResult, output_path: Path) -> None:
    clear()
    print(hero())
    print(key_value("email", result.identity.canonical_email))
    print(key_value("mode", result.request.mode))
    print(key_value("count", str(result.request.count)))
    print(key_value("dot space", f"{result.identity.dot_capacity:,}"))
    print(key_value("output", str(output_path)))
    print()
    if result.identity.input_local != result.identity.canonical_local:
        print(note("input dots were normalized before generation", "info"))


def _render_preview(aliases: list[str], preview: int) -> None:
    shown = aliases[:preview]
    if not shown:
        return

    print(rule("preview"))
    for alias in shown:
        print(style(alias, Palette.INK))

    hidden = len(aliases) - len(shown)
    if hidden > 0:
        print(style(f"... and {hidden} more", Palette.SUBTLE))


def _write_aliases(output_path: Path, aliases: list[str], overwrite: bool) -> None:
    if output_path.exists() and not overwrite:
        raise GmailGenError(
            f"{output_path} already exists. Re-run with --overwrite or choose a different file."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(aliases) + "\n", encoding="utf-8")


def _required_prompt(label: str, placeholder: str) -> str:
    while True:
        value = prompt(label, placeholder)
        if value:
            return value
        flash_error("error: value required")


def _prompt_count() -> int:
    while True:
        value = prompt("count", "128") or "128"
        try:
            count = int(value)
        except ValueError:
            flash_error("error: count must be an integer")
            continue

        if count > 0:
            return count
        flash_error("error: count must be greater than zero")


def _prompt_mode() -> str:
    allowed = {"1": "both", "2": "dots", "3": "plus", "both": "both", "dots": "dots", "plus": "plus"}
    while True:
        value = prompt("mode", "both / dots / plus") or "both"
        mode = allowed.get(value.lower())
        if mode:
            label = style("mode".ljust(5), BOLD, Palette.INK)
            hint = style("   [both / dots / plus]", Palette.SUBTLE)
            print(f"\033[F\r{label}{hint}:   {style(mode, Palette.SUCCESS)}")
            return mode
        flash_error("error: choose both, dots, or plus")


def _prompt_yes_no(label: str, default: bool) -> bool:
    suffix = "y/n"
    while True:
        value = prompt(label, suffix)
        if not value:
            return default

        normalized = value.strip().lower()
        if normalized in {"y", "yes"}:
            return True
        if normalized in {"n", "no"}:
            return False
        flash_error("error: answer yes or no")
