"""Tests for the Wopet-specific TUTK handshake additions."""

from __future__ import annotations

import importlib.util
import inspect
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


def test_verbose_protocol_logging_uses_stderr() -> None:
    """Debug traces must never be mixed into go2rtc's stdout media stream."""
    protocol = _load_protocol_module()
    source = inspect.getsource(protocol.TUTKDirectSession._vlog)
    assert "file=sys.stderr" in source


def test_wopet_wrapper_uses_go2rtc_native_hevc_input() -> None:
    """Avoid gating Wopet video on the Cubo-specific MPEG-TS clean-IDR path."""
    source = (ROOT / "wopet_bridge/wopet/wopet_stream.py").read_text(encoding="utf-8")
    assert 'os.environ["CUBOAI_OUTPUT_FORMAT"] = "annexb"' in source


def test_wopet_wrapper_supervises_the_stream_with_bounded_backoff() -> None:
    """A failed camera handshake must not become a go2rtc respawn storm."""
    wrapper_path = ROOT / "wopet_bridge/wopet/wopet_stream.py"
    spec = importlib.util.spec_from_file_location("wopet_stream_wrapper", wrapper_path)
    assert spec is not None and spec.loader is not None
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)

    assert [wrapper._retry_delay(attempt) for attempt in range(1, 7)] == [
        30,
        60,
        120,
        240,
        300,
        300,
    ]

    source = inspect.getsource(wrapper.main)
    assert "subprocess.Popen" in source
    assert "child.terminate()" in source


def test_annexb_stream_waits_for_a_safe_hevc_opening_frame() -> None:
    """A reconnect that begins on a P-frame must wait for VPS/IRAP before go2rtc sees it."""
    module_path = ROOT / "wopet_bridge/vendor/cuboai_tutk/cuboai_stream_video.py"
    spec = importlib.util.spec_from_file_location("wopet_cuboai_stream_video", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    p_frame = bytes.fromhex("000000010201d04c")
    vps_frame = bytes.fromhex("0000000140010c01")
    idr_frame = bytes.fromhex("000000012601af09")

    assert not module.is_annexb_keyframe(p_frame)
    assert module.is_annexb_keyframe(vps_frame)
    assert module.is_annexb_keyframe(idr_frame)

    source = inspect.getsource(module.main)
    assert "waiting_for_keyframe = True" in source
    assert "if not is_annexb_keyframe(data)" in source


def test_annexb_stream_rejects_short_or_invalid_hevc_nalus() -> None:
    """Malformed NAL units must not reach go2rtc's panic-prone HEVC packetizer."""
    module_path = ROOT / "wopet_bridge/vendor/cuboai_tutk/cuboai_stream_video.py"
    spec = importlib.util.spec_from_file_location("wopet_cuboai_stream_safety", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    valid = bytes.fromhex("0000000140010c01000000012601af09")
    one_byte_nalu = bytes.fromhex("0000000140010c010000000102")
    invalid_tid = bytes.fromhex("0000000140000c01")

    assert module.is_safe_hevc_annexb_au(valid)
    assert not module.is_safe_hevc_annexb_au(one_byte_nalu)
    assert not module.is_safe_hevc_annexb_au(invalid_tid)

    source = inspect.getsource(module.main)
    assert "elif not is_safe_hevc_annexb_au(data)" in source
