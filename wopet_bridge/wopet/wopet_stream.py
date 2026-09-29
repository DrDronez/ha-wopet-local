#!/usr/bin/env python3
"""Read HA app options and run the vendored pure-Python TUTK streamer."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _required_string(options: dict[str, object], name: str) -> str:
    value = options.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Required app option is missing: {name}")
    return value.strip()


def main() -> None:
    """Load private options without putting credentials in arguments or logs."""
    options_path = Path(os.environ.get("WOPET_OPTIONS_FILE", "/data/options.json"))
    options = json.loads(options_path.read_text(encoding="utf-8"))

    os.environ["CUBOAI_CAMERA_IP"] = _required_string(options, "camera_ip")
    os.environ["CUBOAI_UID"] = _required_string(options, "device_uid")
    os.environ["CUBOAI_ACCOUNT"] = _required_string(options, "device_username")
    os.environ["CUBOAI_PASSWORD"] = _required_string(options, "device_password")
    os.environ["CUBOAI_MUX_AUDIO"] = "0"
    os.environ["CUBOAI_WOPET_X2043"] = "1"
    os.environ["CUBOAI_VERBOSE"] = (
        "1" if str(options.get("log_level", "info")).lower() == "debug" else "0"
    )

    vendor = Path(__file__).parents[1] / "vendor" / "cuboai_tutk"
    sys.path.insert(0, str(vendor))
    from cuboai_stream_video import main as stream_main

    stream_main()


if __name__ == "__main__":
    main()
