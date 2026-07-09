"""Patch version metadata into xkcd-script fonts and JS, then verify."""

from __future__ import annotations

import argparse
import datetime
import pathlib
import re

from fontTools.ttLib import TTFont

_VERSION_RE = re.compile(r"^\d{4}\.\d+$")
_DEV_VERSION = "0.0-dev"
_HEAD_ALLOWED_DIFF = frozenset({"fontRevision", "modified", "checksumAdjustment"})
_NAME_ALLOWED_DIFF = frozenset({5})


class TableMismatch(Exception):
    """Raised when a verified font table differs from its expected baseline."""


def validate_version(version: str) -> None:
    """Raise ValueError if *version* is not a CalVer YYYY.MICRO or "0.0-dev"."""
    if version == _DEV_VERSION:
        return
    if not _VERSION_RE.match(version):
        raise ValueError(
            f"Version {version!r} does not match YYYY.MICRO or {_DEV_VERSION!r}"
        )


def patch_font(font: TTFont, *, version: str, build_date: str) -> None:
    """Patch name table version + head.fontRevision in-place."""
    validate_version(version)

    version_string = f"Version {version}; {build_date}"
    name_table = font["name"]
    existing = [r for r in name_table.names if r.nameID == 5]
    for record in existing:
        name_table.setName(
            version_string,
            record.nameID,
            record.platformID,
            record.platEncID,
            record.langID,
        )

    if version != _DEV_VERSION:
        font["head"].fontRevision = float(version)


def verify_tables_identical(*, original: TTFont, patched: TTFont) -> None:
    """Raise TableMismatch if any table differs outside the allowed fields."""
    # GlyphOrder is a virtual table fontTools exposes but never serialises.
    tags_original = {t for t in original.keys() if t != "GlyphOrder"}
    tags_patched = {t for t in patched.keys() if t != "GlyphOrder"}
    if tags_original != tags_patched:
        raise TableMismatch(
            f"Table tag set differs: only-original={tags_original - tags_patched}, "
            f"only-patched={tags_patched - tags_original}"
        )

    for tag in sorted(tags_original):
        if tag == "head":
            _verify_head(original["head"], patched["head"])
        elif tag == "name":
            _verify_name(original["name"], patched["name"])
        else:
            _verify_generic(tag, original, patched)


def _verify_head(orig, patched) -> None:
    for field in orig.__dict__:
        if field in _HEAD_ALLOWED_DIFF:
            continue
        if getattr(orig, field) != getattr(patched, field):
            raise TableMismatch(f"head.{field} changed unexpectedly")


def _verify_name(orig, patched) -> None:
    def key(record):
        return (record.nameID, record.platformID, record.platEncID, record.langID)

    orig_records = {key(r): str(r) for r in orig.names}
    patched_records = {key(r): str(r) for r in patched.names}

    if set(orig_records) != set(patched_records):
        raise TableMismatch("name table record set differs")

    for record_key, original_value in orig_records.items():
        if record_key[0] in _NAME_ALLOWED_DIFF:
            continue
        if patched_records[record_key] != original_value:
            raise TableMismatch(f"name record {record_key} changed unexpectedly")


def _verify_generic(tag: str, original: TTFont, patched: TTFont) -> None:
    orig_bytes = original.getTableData(tag)
    patched_bytes = patched.getTableData(tag)
    if orig_bytes != patched_bytes:
        raise TableMismatch(
            f"Table {tag!r} bytes differ ({len(orig_bytes)} vs {len(patched_bytes)})"
        )


def inject_js_version(source: str, *, version: str, build_date: str) -> str:
    """Prepend a header comment and a runtime version constant to JS source."""
    header = (
        f"/*! xkcd-mathjax v{version} — built {build_date} — "
        f"https://github.com/ipython/xkcd-font */\n"
    )
    runtime = f'globalThis.XKCD_MATHJAX_VERSION = "{version}";\n'
    return header + runtime + source


def _ttf_seconds(build_date: str) -> int:
    """Seconds since 1904-01-01 for *build_date* (YYYY-MM-DD, UTC midnight)."""
    epoch = datetime.datetime(1904, 1, 1, tzinfo=datetime.timezone.utc)
    when = datetime.datetime.strptime(build_date, "%Y-%m-%d").replace(
        tzinfo=datetime.timezone.utc
    )
    return int((when - epoch).total_seconds())


def write_patched_font(
    in_path: pathlib.Path,
    out_path: pathlib.Path,
    *,
    version: str,
    build_date: str,
) -> TTFont:
    """Patch *in_path*, verify the in-memory patched font, then save to *out_path*."""
    original = TTFont(in_path)
    patched = TTFont(in_path)
    patch_font(patched, version=version, build_date=build_date)
    if version != _DEV_VERSION:
        patched["head"].modified = _ttf_seconds(build_date)
    # Verify BEFORE save: fontTools recomputes head bounds + checksums on
    # compile, so post-save the in-memory `patched` no longer mirrors the
    # original's head fields.
    verify_tables_identical(original=original, patched=patched)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    patched.save(out_path)
    return patched


def regenerate_woff(patched_otf: pathlib.Path, out_path: pathlib.Path) -> None:
    font = TTFont(patched_otf)
    font.flavor = "woff"
    font.save(out_path)


def regenerate_woff2(patched_otf: pathlib.Path, out_path: pathlib.Path) -> None:
    font = TTFont(patched_otf)
    font.flavor = "woff2"
    font.save(out_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--font-dir", type=pathlib.Path, required=True)
    parser.add_argument("--js", type=pathlib.Path, required=True)
    parser.add_argument("--out-dir", type=pathlib.Path, required=True)
    parser.add_argument("--build-date", default=datetime.date.today().isoformat())
    args = parser.parse_args(argv)

    validate_version(args.version)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    otf_in = args.font_dir / "xkcd-script.otf"
    ttf_in = args.font_dir / "xkcd-script.ttf"
    otf_out = args.out_dir / "xkcd-script.otf"
    ttf_out = args.out_dir / "xkcd-script.ttf"
    woff_out = args.out_dir / "xkcd-script.woff"
    woff2_out = args.out_dir / "xkcd-script.woff2"

    if not otf_in.exists():
        raise FileNotFoundError(otf_in)
    if not ttf_in.exists():
        raise FileNotFoundError(ttf_in)

    write_patched_font(
        otf_in, otf_out, version=args.version, build_date=args.build_date
    )
    write_patched_font(
        ttf_in, ttf_out, version=args.version, build_date=args.build_date
    )
    regenerate_woff(otf_out, woff_out)
    regenerate_woff2(otf_out, woff2_out)

    js_source = args.js.read_text(encoding="utf-8")
    js_out = args.out_dir / "xkcd-mathjax3.js"
    js_out.write_text(
        inject_js_version(js_source, version=args.version, build_date=args.build_date),
        encoding="utf-8",
    )

    print(f"Wrote artifacts to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
