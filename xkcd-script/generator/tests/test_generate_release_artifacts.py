import importlib.util
import pathlib
import sys

import pytest

_HERE = pathlib.Path(__file__).resolve().parent
_SCRIPT = _HERE.parent / "generate_release_artifacts.py"
_spec = importlib.util.spec_from_file_location("generate_release_artifacts", _SCRIPT)
gra = importlib.util.module_from_spec(_spec)
sys.modules["generate_release_artifacts"] = gra
_spec.loader.exec_module(gra)


@pytest.mark.parametrize("version", ["2026.0", "2026.12", "9999.0", "0.0-dev"])
def test_validate_version_accepts(version):
    gra.validate_version(version)


@pytest.mark.parametrize("version", ["", "v2026.0", "2026", "2026.0.1", "2026-0", "abc"])
def test_validate_version_rejects(version):
    with pytest.raises(ValueError):
        gra.validate_version(version)


from fontTools.ttLib import TTFont

_REPO_ROOT = _HERE.parents[2]
_COMMITTED_OTF = _REPO_ROOT / "xkcd-script" / "font" / "xkcd-script.otf"


def _load_committed_font() -> TTFont:
    """Load a fresh TTFont from the committed unversioned xkcd-script.otf."""
    if not _COMMITTED_OTF.exists():
        pytest.skip(f"Committed font not present at {_COMMITTED_OTF}")
    return TTFont(_COMMITTED_OTF)


def test_patch_font_sets_name_version():
    font = _load_committed_font()
    gra.patch_font(font, version="2026.0", build_date="2026-06-16")
    version_records = [r for r in font["name"].names if r.nameID == 5]
    assert version_records, "real font must have at least one nameID 5 record"
    for r in version_records:
        assert str(r) == "Version 2026.0; 2026-06-16"


def test_patch_font_sets_head_fontrevision():
    font = _load_committed_font()
    gra.patch_font(font, version="2026.1", build_date="2026-06-16")
    assert font["head"].fontRevision == pytest.approx(2026.1, abs=1e-4)


def test_patch_font_dev_leaves_fontrevision():
    font = _load_committed_font()
    original = font["head"].fontRevision
    gra.patch_font(font, version="0.0-dev", build_date="2026-06-16")
    assert font["head"].fontRevision == original


def test_verify_tables_identical_passes_after_patch_only():
    original = _load_committed_font()
    patched = _load_committed_font()
    gra.patch_font(patched, version="2026.0", build_date="2026-06-16")
    gra.verify_tables_identical(original=original, patched=patched)


def test_verify_tables_identical_rejects_unexpected_change():
    original = _load_committed_font()
    patched = _load_committed_font()
    gra.patch_font(patched, version="2026.0", build_date="2026-06-16")
    patched["OS/2"].usWeightClass = 999

    with pytest.raises(gra.TableMismatch) as exc:
        gra.verify_tables_identical(original=original, patched=patched)
    assert "OS/2" in str(exc.value)


def test_verify_tables_identical_rejects_unexpected_name_change():
    original = _load_committed_font()
    patched = _load_committed_font()
    gra.patch_font(patched, version="2026.0", build_date="2026-06-16")
    patched["name"].setName("EvilFamily", 1, 3, 1, 0x409)

    with pytest.raises(gra.TableMismatch):
        gra.verify_tables_identical(original=original, patched=patched)


def test_inject_js_version_adds_header_and_constant():
    source = "console.log('hi');\n"
    out = gra.inject_js_version(source, version="2026.0", build_date="2026-06-16")
    assert out.startswith(
        "/*! xkcd-mathjax v2026.0 — built 2026-06-16 — https://github.com/ipython/xkcd-font */\n"
    )
    assert 'globalThis.XKCD_MATHJAX_VERSION = "2026.0";' in out
    assert "console.log('hi');" in out


def test_inject_js_version_dev():
    out = gra.inject_js_version("x", version="0.0-dev", build_date="2026-06-16")
    assert "v0.0-dev" in out
    assert 'globalThis.XKCD_MATHJAX_VERSION = "0.0-dev";' in out
