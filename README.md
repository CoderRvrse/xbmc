# kodi-toolkit

Everything used to install, tune and maintain a Kodi 21.3 "Omega" setup on
Windows 11 — plus the automation that keeps this fork of
[`xbmc/xbmc`](https://github.com/xbmc/xbmc) permanently in sync with upstream.

📖 **Start here → [KODI-SETUP.md](KODI-SETUP.md)** — the full writeup: what was
installed, every setting that was changed and *why*, how to finish the library
setup, and how to undo any of it.

## Layout

| Path | What it is |
|---|---|
| [KODI-SETUP.md](KODI-SETUP.md) | The complete setup & maintenance document |
| [.github/workflows/sync-upstream.yml](.github/workflows/sync-upstream.yml) | Daily job that fast-forwards the mirror branches from upstream |
| [tools/sync-upstream.ps1](tools/sync-upstream.ps1) | Manual/local equivalent of the sync job |
| [tools/kodi_addons.py](tools/kodi_addons.py) | Installs official-repo addons with transitive dependency resolution |
| [tools/patch_guisettings.py](tools/patch_guisettings.py) | Safely edits values in Kodi's `guisettings.xml` |
| [kodi-config/](kodi-config/) | Reference copies of the deployed `advancedsettings.xml` / `sources.xml` |

## Branches in this fork

| Branch | Purpose |
|---|---|
| `kodi-toolkit` | **default** — the files above. Nothing from upstream, so it never conflicts. |
| `master`, `Omega`, `Nexus` | Pristine mirrors of upstream. Auto fast-forwarded daily. Do not commit here. |

The mirrors are deliberately kept clean so every sync is a fast-forward rather
than a merge that eventually conflicts. See KODI-SETUP.md for the reasoning.
