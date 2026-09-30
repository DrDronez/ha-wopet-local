#!/usr/bin/env python3
"""Read HA app options and run the vendored pure-Python TUTK streamer."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

INITIAL_RETRY_DELAY = 60
MAX_RETRY_DELAY = 600
HEALTHY_RUN_SECONDS = 60
DEFAULT_RETRY_STATE_FILE = "/data/wopet_retry_state.json"


def _required_string(options: dict[str, object], name: str) -> str:
    value = options.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Required app option is missing: {name}")
    return value.strip()


def _retry_delay(consecutive_failures: int) -> int:
    """Return a camera-friendly exponential reconnect delay."""
    exponent = max(0, consecutive_failures - 1)
    return min(INITIAL_RETRY_DELAY * (2**exponent), MAX_RETRY_DELAY)


def _load_retry_state(path: Path) -> tuple[int, float]:
    """Load a cross-process cooldown, tolerating old or damaged state files."""
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        failures = max(0, int(state.get("consecutive_failures", 0)))
        next_attempt = max(0.0, float(state.get("next_attempt", 0)))
        return failures, next_attempt
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return 0, 0.0


def _save_retry_state(path: Path, failures: int, next_attempt: float) -> None:
    """Atomically persist retry history so a go2rtc respawn cannot erase it."""
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(
            {"consecutive_failures": failures, "next_attempt": next_attempt},
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    temporary.replace(path)


def _clear_retry_state(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def main() -> None:
    """Load private options without putting credentials in arguments or logs."""
    options_path = Path(os.environ.get("WOPET_OPTIONS_FILE", "/data/options.json"))
    options = json.loads(options_path.read_text(encoding="utf-8"))

    os.environ["CUBOAI_CAMERA_IP"] = _required_string(options, "camera_ip")
    os.environ["CUBOAI_UID"] = _required_string(options, "device_uid")
    os.environ["CUBOAI_ACCOUNT"] = _required_string(options, "device_username")
    os.environ["CUBOAI_PASSWORD"] = _required_string(options, "device_password")
    audio_enabled = bool(options.get("enable_audio", False))
    os.environ["CUBOAI_MUX_AUDIO"] = "1" if audio_enabled else "0"
    os.environ["CUBOAI_OUTPUT_FORMAT"] = "mpegts" if audio_enabled else "annexb"
    # Firmware 40.23.6.5 does not reliably mark a complete IDR at the assembled
    # access-unit boundary. Do not hold back the MPEG-TS PAT/PMT while waiting
    # for that hint; downstream demuxers can lock immediately and the decoder
    # will begin displaying at the next usable keyframe.
    os.environ["CUBOAI_CLEAN_GOP"] = "0" if audio_enabled else "1"
    os.environ["CUBOAI_WOPET_X2043"] = "1"
    os.environ["WOPET_CONTROL_PORT"] = str(options.get("control_port", 1986))
    os.environ["WOPET_CONTROL_TOKEN"] = str(options.get("control_token", "")).strip()
    os.environ["CUBOAI_VERBOSE"] = (
        "1" if str(options.get("log_level", "info")).lower() == "debug" else "0"
    )

    vendor = Path(__file__).parents[1] / "vendor" / "cuboai_tutk"
    streamer = vendor / "cuboai_stream_video.py"
    retry_state_path = Path(
        os.environ.get("WOPET_RETRY_STATE_FILE", DEFAULT_RETRY_STATE_FILE)
    )
    stopping = False
    child: subprocess.Popen[bytes] | None = None

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True
        if child is not None and child.poll() is None:
            child.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    consecutive_failures, next_attempt = _load_retry_state(retry_state_path)
    while not stopping:
        while not stopping and time.time() < next_attempt:
            time.sleep(min(0.5, next_attempt - time.time()))
        if stopping:
            return

        started = time.monotonic()
        child = subprocess.Popen([sys.executable, str(streamer)], env=os.environ.copy())
        return_code = child.wait()
        runtime = time.monotonic() - started
        child = None

        if runtime >= HEALTHY_RUN_SECONDS:
            consecutive_failures = 0
            next_attempt = 0.0
            _clear_retry_state(retry_state_path)

        if stopping:
            # go2rtc stops an on-demand exec producer when its last consumer
            # disconnects. That is a normal lifecycle event, not a camera
            # failure; carrying a cooldown into the next viewer would make the
            # producer emit no bytes and break the next RTSP request.
            _clear_retry_state(retry_state_path)
            return

        consecutive_failures += 1
        delay = _retry_delay(consecutive_failures)
        next_attempt = time.time() + delay
        _save_retry_state(retry_state_path, consecutive_failures, next_attempt)
        print(
            "Wopet stream process ended "
            f"(exit {return_code}, ran {runtime:.1f}s); retrying in {delay}s",
            file=sys.stderr,
            flush=True,
        )

        while not stopping and time.time() < next_attempt:
            time.sleep(min(0.5, next_attempt - time.time()))


if __name__ == "__main__":
    main()
