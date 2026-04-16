"""source package."""

from .core import EmailIdentity, GenerationRequest, GenerationResult, generate_aliases, parse_email

__all__ = [
    "EmailIdentity",
    "GenerationRequest",
    "GenerationResult",
    "generate_aliases",
    "parse_email",
]
