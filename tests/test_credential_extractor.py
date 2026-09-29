"""Tests for the local credential extractor's pure helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "extract_device_credentials", ROOT / "tools/extract_device_credentials.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_dechunk() -> None:
    """Decode a minimal chunked response body."""
    assert MODULE._dechunk(b"4\r\ntest\r\n0\r\n\r\n") == b"test"


def test_device_records_only_yields_required_fields() -> None:
    """Ignore unrelated account records."""
    value = {
        "account": {"userid": "private"},
        "devices": [{"devid": "uid", "devusr": "user", "devpw": "password"}],
    }
    records = list(MODULE._device_records(value))
    assert records == [{"devid": "uid", "devusr": "user", "devpw": "password"}]
