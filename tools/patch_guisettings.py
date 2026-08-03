"""
Patch Kodi's guisettings.xml in place.

guisettings.xml is OWNED by Kodi -- it is rewritten on every clean exit. So we
never hand-author it; we let Kodi generate it, then edit the values of settings
that already exist in the file. Editing an existing <setting> node this way
survives Kodi's own load/validate path.

Kodi marks untouched settings default="true". When we override a value we must
also flip that attribute to "false", otherwise Kodi treats the node as unset and
silently restores its own default.

Run with Kodi CLOSED, or Kodi will overwrite these on exit.
"""

import os
import shutil
import sys
import xml.etree.ElementTree as ET

GUI = os.path.join(os.environ["APPDATA"], "Kodi", "userdata", "guisettings.xml")

# id -> (value, why)
CHANGES = {
    # ---------- Video playback: RTX 4070 ----------
    "videoplayer.adjustrefreshrate": (
        "2", "Match display refresh to video fps on start/stop -> kills 24p judder"),
    "videoplayer.usedxva2": (
        "true", "DXVA2 hardware decode on the RTX 4070 (HEVC/AV1/H.264)"),
    "videoplayer.highprecision": (
        "true", "High-precision processing; free on this GPU"),
    "videoplayer.usesuperresolution": (
        "true", "RTX Video Super Resolution - AI upscale of sub-1080p content"),
    "videoplayer.hqscalers": (
        "10", "Use high-quality scalers from 10% upscale (default 20)"),

    # ---------- Display ----------
    # NOTE: integer, not boolean -- 0=AUTO, 1=NEVER, 2=ALWAYS.
    "videoscreen.10bitsurfaces": (
        "2", "Always use 10-bit render surfaces -> less colour banding"),
    "videoscreen.dither": (
        "true", "Dithering to hide banding on gradients"),

    # ---------- Interface polish ----------
    "lookandfeel.enablerssfeeds": (
        "false", "Remove the scrolling RSS ticker from the home screen"),

    # ---------- Library behaviour ----------
    "videolibrary.backgroundupdate": (
        "true", "Scan the library in the background instead of blocking the UI"),

    # ---------- Active addons ----------
    "lookandfeel.skin": (
        "skin.arctic.zephyr.mod", "Arctic: Zephyr - Reloaded (official repo)"),
    "weather.addon": (
        "weather.openweathermap.extended", "Wire up the weather provider"),
    "subtitles.tv": (
        "service.subtitles.a4ksubtitles", "Default subtitle service for TV"),
    "subtitles.movie": (
        "service.subtitles.a4ksubtitles", "Default subtitle service for films"),
}


def main():
    if not os.path.isfile(GUI):
        print(f"ERROR: {GUI} not found -- run Kodi once first.")
        return 1

    backup = GUI + ".bak"
    if not os.path.exists(backup):
        shutil.copy2(GUI, backup)
        print(f"backup -> {backup}\n")

    tree = ET.parse(GUI)
    root = tree.getroot()

    index = {s.get("id"): s for s in root.iter("setting")}
    applied, missing, same = [], [], []

    for sid, (val, why) in CHANGES.items():
        node = index.get(sid)
        if node is None:
            missing.append(sid)
            continue
        old = (node.text or "").strip()
        if old == val:
            same.append((sid, val))
            node.set("default", "false")
            continue
        node.text = val
        node.set("default", "false")
        applied.append((sid, old, val, why))

    tree.write(GUI, encoding="utf-8", xml_declaration=True)

    print(f"CHANGED ({len(applied)}):")
    for sid, old, new, why in applied:
        print(f"  {sid}")
        print(f"      {old!r} -> {new!r}   # {why}")
    if same:
        print(f"\nALREADY CORRECT ({len(same)}) - pinned so Kodi keeps them:")
        for sid, v in same:
            print(f"  {sid} = {v}")
    if missing:
        print(f"\nNOT PRESENT ON THIS BUILD ({len(missing)}) - skipped safely:")
        for sid in missing:
            print(f"  {sid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
