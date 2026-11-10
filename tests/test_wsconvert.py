"""Tests for the WordStar to Markdown converter."""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import wsconvert


def test_truncated_escape_byte_does_not_crash():
    """A file ending with a lone 0x1B escape byte must not raise IndexError."""
    assert wsconvert.converttext(bytes([0x41, 0x1B]), False) == bytearray(b"A")


def test_plain_ascii_conversion():
    assert wsconvert.converttext(b"Hello\x1a", False) == bytearray(b"Hello")


def test_escape_sequence_skips_next_byte():
    assert wsconvert.converttext(b"A\x1BB\x1a", False) == bytearray(b"AB")
