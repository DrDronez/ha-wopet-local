"""Repository-level tests that do not require Home Assistant."""

from __future__ import annotations

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
    assert app["arch"] == ["amd64"]
    assert "configuration" in translations
