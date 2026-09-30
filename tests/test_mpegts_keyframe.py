"""Regression tests for the Wopet MPEG-TS output path."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
VENDOR = ROOT / "wopet_bridge/vendor/cuboai_tutk"
sys.path.insert(0, str(VENDOR))

from cuboai_stream_video import mux_timed_stream  # noqa: E402


def test_clean_gop_accepts_idr_when_frameinfo_flag_is_clear() -> None:
    """Firmware 40.23.6.5 exposes IDR NALs without its metadata keyframe flag."""
    p_frame = b"\x00\x00\x00\x01\x02\x01" + (b"\x11" * 32)
    idr_frame = b"\x00\x00\x00\x01\x26\x01" + (b"\x22" * 32)
    frameinfo = {
        "codec": "hevc",
        "timestamp_ms": 1_000,
        "ts_valid": True,
        "is_keyframe": False,
        "frame_no": 1,
    }
    output: list[bytes] = []

    mux_timed_stream(
        iter(
            (
                ("video", p_frame, frameinfo),
                ("video", idr_frame, {**frameinfo, "frame_no": 2}),
            )
        ),
        output.append,
        clean_gop=True,
        mux_audio=True,
        log=lambda _message: None,
    )

    assert output
    assert output[0].startswith(b"\x47")
