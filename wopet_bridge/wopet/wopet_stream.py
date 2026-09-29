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

INITIAL_RETRY_DELAY = 30
MAX_RETRY_DELAY = 300
HEALTHY_RUN_SECONDS = 60


def _required_string(options: dict[str, object], name: str) -> str:
    value = options.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Required app option is missing: {name}")
    return value.strip()


def _retry_delay(consecutive_failures: int) -> int:
    """Return a camera-friendly exponential reconnect delay."""
    exponent = max(0, consecutive_failures - 1)
    return min(INITIAL_RETRY_DELAY * (2**exponent), MAX_RETRY_DELAY)


def main() -> None:
    """Load private options without putting credentials in arguments or logs."""
    options_path = Path(os.environ.get("WOPET_OPTIONS_FILE", "/data/options.json"))
    options = json.loads(options_path.read_text(encoding="utf-8"))

    os.environ["CUBOAI_CAMERA_IP"] = _required_string(options, "camera_ip")
    os.environ["CUBOAI_UID"] = _required_string(options, "device_uid")
    os.environ["CUBOAI_ACCOUNT"] = _required_string(options, "device_username")
    os.environ["CUBOAI_PASSWORD"] = _required_string(options, "device_password")
    os.environ["CUBOAI_MUX_AUDIO"] = "0"
    os.environ["CUBOAI_OUTPUT_FORMAT"] = "annexb"
    os.environ["CUBOAI_WOPET_X2043"] = "1"
    os.environ["CUBOAI_VERBOSE"] = (
        "1" if str(options.get("log_level", "info")).lower() == "debug" else "0"
    )

    vendor = Path(__file__).parents[1] / "vendor" / "cuboai_tutk"
    streamer = vendor / "cuboai_stream_video.py"
    stopping = False
    child: subprocess.Popen[bytes] | None = None

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True
        if child is not None and child.poll() is None:
            child.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    consecutive_failures = 0
    while not stopping:
        started = time.monotonic()
        child = subprocess.Popen([sys.executable, str(streamer)], env=os.environ.copy())
        return_code = child.wait()
        runtime = time.monotonic() - started
        child = None

        if stopping:
            return

        if runtime >= HEALTHY_RUN_SECONDS:
            consecutive_failures = 0
        consecutive_failures += 1
        delay = _retry_delay(consecutive_failures)
        print(
            "Wopet stream process ended "
            f"(exit {return_code}, ran {runtime:.1f}s); retrying in {delay}s",
            file=sys.stderr,
            flush=True,
        )

        deadline = time.monotonic() + delay
        while not stopping and time.monotonic() < deadline:
            time.sleep(min(0.5, deadline - time.monotonic()))


if __name__ == "__main__":
    main()
