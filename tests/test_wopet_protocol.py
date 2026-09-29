"""Tests for the Wopet-specific TUTK handshake additions."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "wopet_bridge/vendor/cuboai_tutk/cuboai_pure.py"


def _load_protocol_module():
    spec = importlib.util.spec_from_file_location("wopet_cuboai_pure", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_wopet_x2043_carries_ack_and_av_session_fields() -> None:
    """The registration packet must bind the discovery and AV handshakes."""
    protocol = _load_protocol_module()

    ack_decoded = bytearray(88)
    ack_decoded[16:32] = bytes(range(0x20, 0x30))
    av_decoded = bytearray(598)
    av_decoded[16:21] = bytes.fromhex("a1a2a3a4a5")
    av_decoded[24] = 0xC0
    av_decoded[28] = 0x78
    av_decoded[29] = 0x01
    av_decoded[31] = 0x13

    wire = protocol.build_wopet_x2043(
        protocol.xor_frame(bytes(ack_decoded)),
        protocol.xor_frame(bytes(av_decoded)),
    )
    decoded = protocol.xor_frame(wire)

    assert len(decoded) == 52
    assert decoded[:16] == bytes.fromhex("20431020000000001040a02140020002")
    assert decoded[16:32] == ack_decoded[16:32]
    assert decoded[32:37] == av_decoded[16:21]
    assert decoded[40] == 0xD3
    assert decoded[44:46] == bytes.fromhex("7841")
    assert decoded[47] == 0x13
    assert decoded[48:52] == bytes.fromhex("0b5fcde3")
