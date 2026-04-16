from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
import random
import re
from typing import Iterator, Literal

AliasMode = Literal["dots", "plus", "both"]
SUPPORTED_DOMAINS = frozenset({"gmail.com", "googlemail.com"})

EMAIL_RE = re.compile(r"^(?P<local>[^@\s]+)@(?P<domain>[^@\s]+\.[^@\s]+)$")


class GmailGenError(ValueError):
    """Raised when the request cannot be fulfilled."""


@dataclass(frozen=True)
class EmailIdentity:
    original: str
    canonical_local: str
    normalized_domain: str
    input_local: str

    @property
    def canonical_email(self) -> str:
        return f"{self.canonical_local}@{self.normalized_domain}"

    @property
    def dot_capacity(self) -> int:
        return 1 if len(self.canonical_local) <= 1 else 1 << (len(self.canonical_local) - 1)


@dataclass(frozen=True)
class GenerationRequest:
    email: str
    count: int
    mode: AliasMode = "both"
    shuffle: bool = False
    seed: int | None = None


@dataclass(frozen=True)
class GenerationResult:
    identity: EmailIdentity
    request: GenerationRequest
    aliases: list[str]


def parse_email(address: str) -> EmailIdentity:
    candidate = address.strip().lower()
    match = EMAIL_RE.match(candidate)
    if not match:
        raise GmailGenError("Enter a valid email address.")

    local = match.group("local")
    domain = match.group("domain")
    if domain not in SUPPORTED_DOMAINS:
        raise GmailGenError("Only Gmail addresses are supported.")

    canonical_local = local.replace(".", "")
    if not canonical_local:
        raise GmailGenError("The local part of the address cannot be empty.")

    return EmailIdentity(
        original=candidate,
        canonical_local=canonical_local,
        normalized_domain=domain,
        input_local=local,
    )


def generate_aliases(request: GenerationRequest) -> GenerationResult:
    if request.count <= 0:
        raise GmailGenError("Alias count must be greater than zero.")

    identity = parse_email(request.email)
    if request.mode == "dots" and request.count > identity.dot_capacity:
        raise GmailGenError(
            f"Only {identity.dot_capacity} dotted aliases exist for {identity.canonical_email}. "
            "Use mode='both' for more."
        )

    aliases = list(islice(_iter_aliases(identity, request.mode), request.count))
    if request.shuffle:
        random.Random(request.seed).shuffle(aliases)

    return GenerationResult(identity=identity, request=request, aliases=aliases)


def _iter_aliases(identity: EmailIdentity, mode: AliasMode) -> Iterator[str]:
    if mode == "plus":
        yield from _iter_plus_only(identity)
        return

    if mode == "dots":
        yield from _iter_dotted_emails(identity, suffix="")
        return

    plus_tag = 0
    while True:
        suffix = "" if plus_tag == 0 else f"+{plus_tag}"
        yield from _iter_dotted_emails(identity, suffix=suffix)
        plus_tag += 1


def _iter_plus_only(identity: EmailIdentity) -> Iterator[str]:
    yield identity.canonical_email
    plus_tag = 1
    while True:
        yield f"{identity.canonical_local}+{plus_tag}@{identity.normalized_domain}"
        plus_tag += 1


def _iter_dotted_emails(identity: EmailIdentity, suffix: str) -> Iterator[str]:
    for local in _iter_dot_variants(identity.canonical_local):
        yield f"{local}{suffix}@{identity.normalized_domain}"


def _iter_dot_variants(local: str) -> Iterator[str]:
    if len(local) <= 1:
        yield local
        return

    slots = len(local) - 1
    for mask in range(1 << slots):
        pieces = [local[0]]
        for index, character in enumerate(local[1:]):
            if mask & (1 << index):
                pieces.append(".")
            pieces.append(character)
        yield "".join(pieces)
