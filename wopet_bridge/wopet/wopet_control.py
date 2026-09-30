#!/usr/bin/env python3
"""Authenticated local HTTP controls for the active Wopet stream session."""

from __future__ import annotations

import hmac
import json
import os
import struct
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

CONTROL_COMMANDS = {
    "pan_left": (0x5047, struct.pack("<III", 1, 1, 10), 0x5048),
    "pan_right": (0x5047, struct.pack("<III", 1, 0, 10), 0x5048),
    "dispense_treat": (0x5043, struct.pack("<I", 1), 0x5044),
}

# Talk is intentionally deferred. Captured start/stop IOCTLs are 0x0350/0x0351.


def _stream_is_ready(session) -> bool:
    """Return whether the underlying transport's AV reader is running."""
    transport = getattr(session, "_inner", session)
    reader = getattr(transport, "_av_reader_thread", None)
    return reader is not None and reader.is_alive()


def execute_control(session, action: str) -> dict[str, object]:
    """Execute a validated one-shot command on the active camera session."""
    try:
        io_type, payload, response_type = CONTROL_COMMANDS[action]
    except KeyError as exc:
        raise ValueError(f"unsupported action: {action}") from exc

    actual_type, response = session.ioctl_during_stream(
        io_type,
        payload,
        resp_type=response_type,
        timeout=3.0,
    )
    if actual_type != response_type:
        raise RuntimeError("camera returned an unexpected response type")
    if not response or len(response) < 4:
        raise RuntimeError("camera returned an incomplete control response")
    result = struct.unpack_from("<I", response)[0]
    if result != 0:
        raise RuntimeError(f"camera rejected the control command (result {result})")
    return {"ok": True, "action": action}


def start_control_server(session):
    """Start the local control API when a token and port are configured."""
    token = os.environ.get("WOPET_CONTROL_TOKEN", "")
    port_text = os.environ.get("WOPET_CONTROL_PORT", "")
    if not token or not port_text:
        print(
            "Wopet controls disabled: configure control_token and control_port",
            file=sys.stderr,
            flush=True,
        )
        return None

    port = int(port_text)

    class ControlHandler(BaseHTTPRequestHandler):
        server_version = "WopetControl/1"

        def log_message(self, _format, *_args):
            return

        def _write_json(self, status: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _authorized(self) -> bool:
            supplied = self.headers.get("Authorization", "")
            expected = f"Bearer {token}"
            return hmac.compare_digest(supplied, expected)

        def do_GET(self):
            if self.path != "/health":
                self._write_json(404, {"ok": False, "error": "not found"})
                return
            if not self._authorized():
                self._write_json(401, {"ok": False, "error": "unauthorized"})
                return
            if not _stream_is_ready(session):
                self._write_json(503, {"ok": False, "error": "stream not ready"})
                return
            self._write_json(200, {"ok": True})

        def do_POST(self):
            if self.path != "/control":
                self._write_json(404, {"ok": False, "error": "not found"})
                return
            if not self._authorized():
                self._write_json(401, {"ok": False, "error": "unauthorized"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > 4096:
                    raise ValueError("invalid request size")
                request = json.loads(self.rfile.read(length))
                action = request.get("action")
                if not isinstance(action, str):
                    raise ValueError("action is required")
                response = execute_control(session, action)
            except ValueError as exc:
                self._write_json(400, {"ok": False, "error": str(exc)})
                return
            except Exception as exc:
                print(f"Wopet control failed: {exc}", file=sys.stderr, flush=True)
                self._write_json(502, {"ok": False, "error": "camera command failed"})
                return
            self._write_json(200, response)

    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), ControlHandler)
    except OSError as exc:
        print(
            f"Wopet controls disabled: could not bind port {port}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return None
    Thread(target=server.serve_forever, name="wopet-control", daemon=True).start()
    print(f"Wopet control API listening on port {port}", file=sys.stderr, flush=True)
    return server
