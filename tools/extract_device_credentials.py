#!/usr/bin/env python3
"""Extract Wopet device credentials from an owner's PCAPdroid capture.

The utility intentionally prints only the three device credentials required by
the bridge. It does not print Wopet account login material or response bodies.
"""

from __future__ import annotations

import argparse
import gzip
import json
import socket
import sys
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import dpkt

WOPET_API_PORT = 8088
REQUIRED_FIELDS = frozenset({"devid", "devusr", "devpw"})


def _ip_packet(linktype: int, packet: bytes) -> dpkt.ip.IP | None:
    """Decode the raw-IP and Ethernet capture formats used by PCAPdroid."""
    try:
        # PCAP uses LINKTYPE_RAW=101; dpkt's historical DLT_RAW constant is 12.
        if linktype in {dpkt.pcap.DLT_RAW, 101}:
            value = dpkt.ip.IP(packet)
        else:
            value = dpkt.ethernet.Ethernet(packet).data
        return value if isinstance(value, dpkt.ip.IP) else None
    except (ValueError, dpkt.UnpackError):
        return None


def _reassemble(parts: list[tuple[int, bytes]]) -> bytes:
    """Reassemble the captured side of a TCP flow, ignoring retransmissions."""
    output = bytearray()
    next_sequence: int | None = None
    for sequence, data in sorted(parts):
        if next_sequence is None:
            output.extend(data)
            next_sequence = sequence + len(data)
            continue
        if sequence > next_sequence:
            break
        overlap = next_sequence - sequence
        if overlap < len(data):
            output.extend(data[overlap:])
            next_sequence += len(data) - overlap
    return bytes(output)


def _dechunk(body: bytes) -> bytes:
    """Decode an HTTP/1.1 chunked body."""
    output = bytearray()
    position = 0
    while True:
        line_end = body.find(b"\r\n", position)
        if line_end < 0:
            raise ValueError("incomplete chunk size")
        size = int(body[position:line_end].split(b";", 1)[0], 16)
        position = line_end + 2
        if size == 0:
            return bytes(output)
        if position + size + 2 > len(body):
            raise ValueError("incomplete chunk body")
        output.extend(body[position : position + size])
        position += size + 2


def _device_records(value: Any) -> Iterator[dict[str, Any]]:
    """Yield device records without exposing unrelated account data."""
    if isinstance(value, dict):
        if REQUIRED_FIELDS <= value.keys():
            yield value
        for child in value.values():
            yield from _device_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from _device_records(child)


def extract(path: Path) -> list[dict[str, str]]:
    """Return unique bridge credential records from a capture."""
    flows: dict[tuple[str, int, str, int], list[tuple[int, bytes]]] = defaultdict(list)
    with path.open("rb") as capture_file:
        capture = dpkt.pcap.Reader(capture_file)
        linktype = capture.datalink()
        for _timestamp, packet in capture:
            ip = _ip_packet(linktype, packet)
            if ip is None or ip.p != dpkt.ip.IP_PROTO_TCP:
                continue
            tcp = ip.data
            if not isinstance(tcp, dpkt.tcp.TCP) or tcp.sport != WOPET_API_PORT or not tcp.data:
                continue
            source = socket.inet_ntoa(ip.src)
            destination = socket.inet_ntoa(ip.dst)
            flows[(source, tcp.sport, destination, tcp.dport)].append((tcp.seq, bytes(tcp.data)))

    unique: dict[tuple[str, str, str], dict[str, str]] = {}
    for parts in flows.values():
        stream = _reassemble(parts)
        starts: list[int] = []
        position = 0
        while (position := stream.find(b"HTTP/1.1 ", position)) >= 0:
            starts.append(position)
            position += len(b"HTTP/1.1 ")
        starts.append(len(stream))

        for start, end in zip(starts, starts[1:]):
            message = stream[start:end]
            header_end = message.find(b"\r\n\r\n")
            if header_end < 0:
                continue
            headers = message[:header_end].decode("latin1", "replace").lower()
            body = message[header_end + 4 :]
            try:
                if "transfer-encoding: chunked" in headers:
                    body = _dechunk(body)
                if "content-encoding: gzip" in headers:
                    body = gzip.decompress(body)
                response = json.loads(body.decode("utf-8"))
            except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
                continue

            for record in _device_records(response):
                values = tuple(str(record[field]) for field in ("devid", "devusr", "devpw"))
                unique[values] = {
                    "name": str(record.get("devalias", "Wopet Camera")),
                    "device_uid": values[0],
                    "device_username": values[1],
                    "device_password": values[2],
                }
    return list(unique.values())


def main() -> int:
    """Run the credential extraction utility."""
    parser = argparse.ArgumentParser(
        description="Extract bridge credentials from your own Wopet PCAPdroid capture."
    )
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()
    if not args.capture.is_file():
        parser.error(f"capture does not exist: {args.capture}")

    devices = extract(args.capture)
    if not devices:
        print("No Wopet device credential records were found.", file=sys.stderr)
        return 1

    print("WARNING: The values below grant access to your camera. Do not share this output.")
    for index, device in enumerate(devices, start=1):
        print(f"\nDevice {index}: {device['name']}")
        print(f"device_uid: {device['device_uid']}")
        print(f"device_username: {device['device_username']}")
        print(f"device_password: {device['device_password']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
