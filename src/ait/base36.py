from __future__ import annotations


ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def encode_base36(value: int) -> str:
    if not 0 <= value < 36:
        raise ValueError("AIT v0 target id must be between 0 and 35")
    return ALPHABET[value]


def decode_base36(char: str) -> int:
    if len(char) != 1 or char not in ALPHABET:
        raise ValueError(f"invalid base36 target: {char}")
    return ALPHABET.index(char)

