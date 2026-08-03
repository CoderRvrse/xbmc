"""
Resolve + install Kodi addons from the OFFICIAL Kodi repository mirror.

Kodi's own addon manager does dependency resolution for you. Dropping a bare zip
into the addons folder does not -- so this script reads the repo's addons.xml
index, walks the <requires> graph transitively, and downloads every dependency
too. Anything already shipped inside Kodi (xbmc.python, xbmc.gui, ...) or already
bundled in the install tree is skipped.

Usage:
    python kodi_addons.py list-skins
    python kodi_addons.py install <addon.id> [<addon.id> ...]
"""

import gzip
import io
import os
import shutil
import ssl
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

REPO = "https://mirrors.kodi.tv/addons/omega"
INDEX = f"{REPO}/addons.xml.gz"

# Kodi's mirror redirects to a rotating pool of university/CDN mirrors, and a few
# of them present chains the Windows store doesn't have. certifi's bundle covers
# all of them, so pin it explicitly rather than disabling verification.
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

# Binary (compiled) addons are published per-platform under "<id>+<platform>/",
# while the zip inside keeps the plain "<id>-<version>.zip" name.
PLATFORM = "windows-x86_64"


def get(url, timeout=120, tries=3):
    last = None
    for n in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=timeout,
                                        context=SSL_CTX) as r:
                return r.read()
        except Exception as e:  # transient mirror/TLS hiccups
            last = e
            if n < tries - 1:
                time.sleep(1.5 * (n + 1))
    raise last

KODI_HOME = os.path.join(os.environ["APPDATA"], "Kodi")
ADDONS_DIR = os.path.join(KODI_HOME, "addons")
BUNDLED_DIR = r"C:\Program Files\Kodi\addons"

# Provided by the Kodi binary itself -- never downloadable as an addon zip.
VIRTUAL = {
    "xbmc.python", "xbmc.gui", "xbmc.json", "xbmc.metadata",
    "xbmc.addon", "xbmc.core", "kodi.resource", "kodi.binary",
}


def fetch_index():
    return ET.fromstring(gzip.decompress(get(INDEX, timeout=60)))


def build_map(root):
    """id -> (version, [required ids])"""
    out = {}
    for addon in root.findall("addon"):
        aid = addon.get("id")
        ver = addon.get("version")
        reqs = []
        for req in addon.findall("./requires/import"):
            rid = req.get("addon")
            if rid and not rid.startswith("xbmc.") and not rid.startswith("kodi."):
                reqs.append(rid)
        # keep highest version if duplicated
        if aid not in out or ver > out[aid][0]:
            out[aid] = (ver, reqs)
    return out


def already_present(aid):
    return os.path.isdir(os.path.join(ADDONS_DIR, aid)) or os.path.isdir(
        os.path.join(BUNDLED_DIR, aid)
    )


def resolve(targets, amap):
    seen, order = set(), []

    def walk(aid):
        if aid in seen or aid in VIRTUAL:
            return
        seen.add(aid)
        if aid not in amap:
            print(f"  !! not in official repo: {aid}")
            return
        for dep in amap[aid][1]:
            walk(dep)
        order.append(aid)

    for t in targets:
        walk(t)
    return order


def install(aid, ver):
    # Pure-python addons live at "<id>/"; compiled ones at "<id>+<platform>/".
    candidates = [
        f"{REPO}/{aid}/{aid}-{ver}.zip",
        f"{REPO}/{aid}+{PLATFORM}/{aid}-{ver}.zip",
    ]
    last = None
    for url in candidates:
        try:
            blob = get(url)
        except Exception as e:
            last = e
            continue
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            z.extractall(ADDONS_DIR)
        return len(blob), url
    raise last


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    root = fetch_index()
    amap = build_map(root)
    print(f"official omega repo index: {len(amap)} addons\n")

    if sys.argv[1] == "list-skins":
        skins = []
        for addon in root.findall("addon"):
            for ext in addon.findall("extension"):
                if ext.get("point") == "xbmc.gui.skin":
                    skins.append((addon.get("id"), addon.get("version"),
                                  addon.get("name")))
        for s in sorted(skins):
            print(f"  {s[0]:<45} {s[1]:<12} {s[2]}")
        return 0

    if sys.argv[1] == "install":
        os.makedirs(ADDONS_DIR, exist_ok=True)
        order = resolve(sys.argv[2:], amap)
        print(f"resolved install order ({len(order)}):")
        for a in order:
            print(f"   - {a} {amap.get(a, ('?',))[0]}")
        print()
        ok = skip = fail = 0
        for aid in order:
            if already_present(aid):
                print(f"  = {aid} (already present)")
                skip += 1
                continue
            try:
                size, url = install(aid, amap[aid][0])
                print(f"  + {aid} {amap[aid][0]}  ({size/1024:.0f} KiB)")
                ok += 1
            except Exception as e:
                print(f"  x {aid}: {e}")
                fail += 1
        print(f"\ninstalled={ok} skipped={skip} failed={fail}")
        return 0 if fail == 0 else 1

    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
