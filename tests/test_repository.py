"""Repository-level tests that do not require Home Assistant."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def test_manifest_and_hacs_metadata_are_valid_json() -> None:
    """Keep the two user-facing package manifests syntactically valid."""
    manifest = json.loads(
        (ROOT / "custom_components/wopet_local/manifest.json").read_text(encoding="utf-8")
    )
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == "wopet_local"
    assert manifest["config_flow"] is True
    assert manifest["version"] == "0.2.10"
    assert hacs["name"] == "Wopet Local"


def test_no_capture_files_are_tracked_in_project_tree() -> None:
    """Protect against accidentally publishing credential-bearing captures."""
    forbidden = {".pcap", ".pcapng"}
    assert not [path for path in ROOT.rglob("*") if path.suffix.lower() in forbidden]


def test_home_assistant_app_metadata_is_valid_yaml() -> None:
    """Keep app and repository metadata syntactically valid."""
    repository = yaml.safe_load((ROOT / "repository.yaml").read_text(encoding="utf-8"))
    app = yaml.safe_load((ROOT / "wopet_bridge/config.yaml").read_text(encoding="utf-8"))
    translations = yaml.safe_load(
        (ROOT / "wopet_bridge/translations/en.yaml").read_text(encoding="utf-8")
    )
    assert repository["name"] == "Wopet Local"
    assert app["slug"] == "wopet_local_bridge"
    assert app["version"] == "0.2.10"
    assert app["arch"] == ["amd64"]
    assert app["host_network"] is True
    assert app["ingress_port"] == 1985
    assert app["options"]["rtsp_port"] == 8554
    assert app["options"]["control_port"] == 1986
    assert app["options"]["enable_audio"] is False
    assert app["schema"]["rtsp_port"] == "port"
    assert app["schema"]["control_token"] == "password"
    assert "configuration" in translations


def test_audio_stream_does_not_wait_for_unreliable_firmware_keyframe_hints() -> None:
    """Publish MPEG-TS discovery tables immediately on firmware 40.23.6.5."""
    source = (ROOT / "wopet_bridge/wopet/wopet_stream.py").read_text(encoding="utf-8")
    assert 'os.environ["CUBOAI_CLEAN_GOP"] = "0" if audio_enabled else "1"' in source


def test_go2rtc_build_is_pinned_and_discovers_pcma_mpegts() -> None:
    """Keep the public build reproducible and preserve Wopet listen audio."""
    dockerfile = (ROOT / "wopet_bridge/Dockerfile").read_text(encoding="utf-8")
    patch = (ROOT / "wopet_bridge/patches/go2rtc-pcma-mpegts.patch").read_text(
        encoding="utf-8"
    )
    assert "GO2RTC_VERSION=v1.9.14" in dockerfile
    assert "GO2RTC_COMMIT=b5948cfb25404cc5cb37b166ecaa2dca20b11d4b" in dockerfile
    assert "git apply --check /tmp/go2rtc-pcma-mpegts.patch" in dockerfile
    assert "case StreamTypePCMATapo:" in patch
    assert "Name:      core.CodecPCMA" in patch


def test_camera_initializes_home_assistant_base_class() -> None:
    """Prevent Camera internals from being absent when the entity is registered."""
    source = (ROOT / "custom_components/wopet_local/camera.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    camera_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "WopetLocalCamera"
    )
    initializer = next(
        node
        for node in camera_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Call)
        and isinstance(node.func.value.func, ast.Name)
        and node.func.value.func.id == "super"
        and node.func.attr == "__init__"
        for node in ast.walk(initializer)
    )


def test_camera_uses_rtsp_stream_for_stills() -> None:
    """Ensure Home Assistant does not call the unimplemented camera_image API."""
    source = (ROOT / "custom_components/wopet_local/camera.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    camera_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "WopetLocalCamera"
    )
    stream_for_stills = next(
        node
        for node in camera_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "use_stream_for_stills"
    )
    assert any(
        isinstance(node, ast.Return)
        and isinstance(node.value, ast.Constant)
        and node.value.value is True
        for node in ast.walk(stream_for_stills)
    )


def test_options_changes_reload_the_integration() -> None:
    """Ensure newly saved control credentials take effect immediately."""
    source = (ROOT / "custom_components/wopet_local/__init__.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    setup = next(
        node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_setup_entry"
    )
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_update_listener"
        for node in ast.walk(setup)
    )


def test_connection_options_override_initial_camera_settings() -> None:
    """Allow HAOS users to replace an unusable loopback bridge address."""
    camera_source = (ROOT / "custom_components/wopet_local/camera.py").read_text(
        encoding="utf-8"
    )
    button_source = (ROOT / "custom_components/wopet_local/button.py").read_text(
        encoding="utf-8"
    )
    flow_source = (ROOT / "custom_components/wopet_local/config_flow.py").read_text(
        encoding="utf-8"
    )
    assert "entry.options.get(CONF_HOST, entry.data[CONF_HOST])" in camera_source
    assert "entry.options.get(CONF_HOST, entry.data[CONF_HOST])" in button_source
    assert "vol.Required(\n                    CONF_HOST," in flow_source
    assert "CONF_RTSP_PORT" in flow_source
    assert "CONF_STREAM_NAME" in flow_source
