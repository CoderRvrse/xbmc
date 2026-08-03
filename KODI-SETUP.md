# Kodi 21.3 "Omega" — Full Setup, Tuning & Maintenance

Complete record of the Kodi installation on this Windows 11 PC: what was
installed, every setting that was changed and **why**, what was deliberately
*not* changed, and how to maintain or undo all of it.

- **Installed:** Kodi **21.3 Omega** (x64) — `C:\Program Files\Kodi`
- **Profile / userdata:** `C:\Users\Franc\AppData\Roaming\Kodi\userdata`
- **Media library root:** `D:\Kodi\Media`
- **Kodi source fork:** [`CoderRvrse/xbmc`](https://github.com/CoderRvrse/xbmc) → cloned to `D:\Kodi\xbmc`

---

## 1. Target hardware

The tuning below is specific to this machine. If you move this config to another
PC, re-read §4 before trusting it.

| | |
|---|---|
| CPU | Intel Core i7-13700KF — 16 cores / 24 threads |
| GPU | NVIDIA GeForce RTX 4070 (driver 32.0.16.1074) |
| RAM | 63.8 GB |
| Display | 1920×1080 @ 60 Hz |
| Audio devices | Realtek HD Audio, NVIDIA HD Audio (HDMI), USB Audio |

Kodi confirmed at runtime:

```
DX::DeviceResources::CreateDeviceResources: device is created on adapter
    'NVIDIA GeForce RTX 4070' with D3D_FEATURE_LEVEL_12_1
CheckDXVA2SharedDecoderSurfaces: DXVA2 shared decoder surfaces is supported
CheckDXVA2SharedDecoderSurfaces: DXVA2 shared decoder surfaces WITH fence synchronization.
CheckDXVA2SharedDecoderSurfaces: DXVA Video Super Resolution is potentially supported
```

---

## 2. Install & integrity

`winget`'s manifest advertised 21.3 but actually resolved to and installed
**21.0** — so the official installer was pulled from the Kodi mirror instead and
verified against two independent sources before running.

| Check | Value |
|---|---|
| File | `kodi-21.3-Omega-x64.exe` (73.97 MiB) |
| Published `.sha256` | `2c46c2bd60b38bb60eb0a5e3468bfd43e9235521eae2910b8c81455e46335c5c` |
| Computed SHA-256 | `2c46c2bd…46335c5c` ✅ **match** |
| Mirror `Content-Sha256` header | decodes to the same digest ✅ **match** |
| Authenticode | *not signed* — see note |

> **On the missing code signature:** Team Kodi does not Authenticode-sign their
> Windows installers; they publish checksums instead. An unsigned installer here
> is expected, not a red flag. Integrity was established by the two matching
> SHA-256 values above. Always verify the hash when you upgrade.

Upgrade later with:

```powershell
# Do NOT rely on `winget upgrade` for Kodi -- its manifest lagged behind.
$u   = 'https://mirrors.kodi.tv/releases/windows/win64/kodi-21.3-Omega-x64.exe'
$exe = "$env:TEMP\kodi.exe"
Invoke-WebRequest $u -OutFile $exe -UseBasicParsing
$want = (Invoke-WebRequest "$u.sha256" -UseBasicParsing).Content.Split(' ')[0]
if ((Get-FileHash $exe -Algorithm SHA256).Hash -eq $want) {
    Start-Process $exe -ArgumentList '/S' -Wait      # silent, upgrades in place
} else { Write-Error 'HASH MISMATCH - do not run' }
```

---

## 3. `advancedsettings.xml` — cache, network, library

Deployed to `…\Kodi\userdata\advancedsettings.xml`
(reference copy: [`kodi-config/advancedsettings.xml`](kodi-config/advancedsettings.xml)).

**Kodi only ever reads this file — it never writes to it.** That makes it the
right home for anything you want to survive settings changes, addon installs and
version upgrades. Anything not listed keeps its Kodi default.

| Setting | Value | Why |
|---|---|---|
| `cache/buffermode` | `1` | Buffer *all* filesystems, not just internet ones. |
| `cache/memorysize` | `524288000` (500 MB) | Kodi reserves **3×** this (~1.5 GB) — 2.3 % of 63.8 GB. Kills stutter on high-bitrate remuxes. |
| `cache/readfactor` | `20` | Fill the cache ~20× faster than playback. Safe on NVMe/gigabit. |
| `network/curlclienttimeout` | `30` | Patience with slow sources before erroring out. |
| `video/ignoresecondsatstart` | `180` | Don't create a resume point if you bail in the first 3 min. |
| `video/playcountminimumpercent` | `90` | Mark watched at 90 % so end credits don't block it. |
| `video/ignorepercentatend` | `8` | Treat the last 8 % as finished. |
| `videolibrary/cleanonupdate` | `true` | Purge deleted files from the library automatically. |
| `musiclibrary/downloadinfo` | `true` | Fetch artist/album art + bios while scanning. |
| `gui/algorithmdirtyregions` | `3` | Full-screen redraw — free on a 4070, avoids skin redraw artifacts. |

---

## 4. `guisettings.xml` — playback & display tuning

`guisettings.xml` is **owned by Kodi**: it is rewritten on every clean exit. So
it was never hand-authored. Kodi generated it, then
[`tools/patch_guisettings.py`](tools/patch_guisettings.py) edited the values of
settings that already existed. Every value below was confirmed to **survive a
full Kodi load→save cycle**, which is the only real proof Kodi accepted it.

> Kodi marks untouched settings `default="true"`. Overriding a value requires
> flipping that attribute to `"false"`, or Kodi treats the node as unset and
> silently restores its own default. The script handles this.

| Setting | Was | Now | Why |
|---|---|---|---|
| `videoplayer.adjustrefreshrate` | `0` | **`2`** | Switch display refresh to match video fps on start/stop — the single biggest win for judder. See caveat below. |
| `videoplayer.usedxva2` | `true` | `true` | DXVA2 hardware decode (H.264/HEVC/AV1) on the 4070. Already default; pinned. |
| `videoplayer.usesuperresolution` | `false` | **`true`** | **RTX Video Super Resolution** — AI upscale of sub-1080p content. Log confirms the GPU supports it. |
| `videoplayer.highprecision` | `true` | `true` | High-precision processing. Free on this GPU. |
| `videoplayer.hqscalers` | `20` | **`10`** | Engage high-quality scalers from 10 % upscale instead of 20 %. |
| `videoscreen.10bitsurfaces` | `0` (AUTO) | **`2`** (ALWAYS) | 10-bit render surfaces always → less colour banding. *This is an integer (0=AUTO/1=NEVER/2=ALWAYS), not a boolean.* |
| `videoscreen.dither` | `false` | **`true`** | Dithering hides banding on gradients. |
| `videolibrary.backgroundupdate` | `false` | **`true`** | Library scans stop blocking the UI. |
| `lookandfeel.skin` | `skin.estuary` | **`skin.arctic.zephyr.mod`** | Arctic: Zephyr – Reloaded. |
| `lookandfeel.enablerssfeeds` | `false` | `false` | No RSS ticker. Already default; pinned. |
| `weather.addon` | *(empty)* | `weather.openweathermap.extended` | Wires up the weather provider. |
| `subtitles.tv` / `subtitles.movie` | *(empty)* | `service.subtitles.a4ksubtitles` | Default subtitle service. |

### ⚠️ Refresh-rate switching caveat

`adjustrefreshrate=2` only helps if your display actually exposes a mode near the
video's frame rate. **Your monitor currently reports 1920×1080 @ 60 Hz only.**
Most film is 23.976 fps, which does not divide into 60 — that's what causes the
periodic hitch known as 3:2 judder.

Check what modes are available:
**Settings → System → Display → Resolution / Whitelist** (Expert level).

- If **23.976 / 24 / 48 Hz** modes appear → add them to the whitelist. You now
  get genuinely judder-free film playback.
- If only 60 Hz exists → the setting is harmless but does nothing. Fixing it
  needs a display/HDMI mode that supports 24 Hz.

### 🔊 Audio passthrough was deliberately left OFF

This machine has three possible outputs (Realtek, NVIDIA HDMI, USB). Enabling
AC3/DTS/TrueHD passthrough sends *undecoded* bitstreams — if the receiving device
can't decode them, **you get silence, not an error**. Guessing your speaker setup
would likely have broken audio, so it was left at Kodi's safe defaults.

Turn it on **only if Kodi output goes to an AV receiver or soundbar over HDMI**:

1. **Settings → System → Audio**
2. *Audio output device* → your **NVIDIA High Definition Audio** HDMI endpoint
3. *Number of channels* → match your speakers (e.g. `7.1`)
4. *Allow passthrough* → **On**
5. Enable only the formats your receiver lists: AC3 / E-AC3 / DTS / TrueHD / DTS-HD

If audio goes to PC speakers or headphones, **leave passthrough off** and instead
set *Number of channels* = `2.0` with *Stereo upmix* off.

---

## 5. Add-ons — 42 installed, official repository only

Nothing from third-party or unofficial sources; `addons.unknownsources` remains
**off**. Installed via [`tools/kodi_addons.py`](tools/kodi_addons.py), which
resolves the full transitive `<requires>` graph — Kodi's own manager does this
for you, but a bare zip drop does not.

| Add-on | Purpose |
|---|---|
| `skin.arctic.zephyr.mod` | **Arctic: Zephyr – Reloaded** — the active skin |
| `service.subtitles.a4ksubtitles` | Subtitles, no account required *(default provider)* |
| `service.subtitles.opensubtitles.com` | Subtitles — needs a free OpenSubtitles account |
| `script.trakt` | Sync watched state / ratings / lists to Trakt.tv |
| `plugin.video.youtube` | YouTube *(needs your own API keys — see §8)* |
| `plugin.video.themoviedb.helper` | Discovery, recommendations, rich metadata |
| `script.artwork.beef` | Bulk-download extra fanart, logos, discart |
| `weather.openweathermap.extended` | Weather |
| `plugin.video.kodi.tv` | Official Kodi channel |
| `script.globalsearch` | Search across the whole library at once |
| `inputstream.adaptive` | DASH/HLS/SmoothStreaming — required by most streaming addons |
| `game.libretro` + `snes9x`, `nestopia`, `mgba` | RetroPlayer cores (SNES / NES / GBA) |
| `game.controller.*` | Controller layouts for the above |
| ~28 `script.module.*` | Auto-resolved dependencies |

> **Two things worth knowing.** Binary add-ons (`inputstream.adaptive`, the
> libretro cores) are published under a platform path — `<id>+windows-x86_64/` —
> not the generic one, which is why a naïve fetch 404s. And side-loaded add-ons
> land in Kodi's DB **disabled**; all 40 were enabled and stamped with
> `origin=repository.xbmc.org` so they receive normal auto-updates.

**Arctic Horizon and Aeon MQ are not in the official repository** — they're
third-party. Arctic: Zephyr – Reloaded is the closest official-repo equivalent.
Other official skins available: `skin.aeon.nox.silvo`, `skin.copacetic`,
`skin.amber`, `skin.mimic.lr`, `skin.quartz`, `skin.confluence`.

Revert to the stock skin at any time:
**Settings → Interface → Skin → Estuary**

---

## 6. Media sources

Configured in `…\userdata\sources.xml`
(reference copy: [`kodi-config/sources.xml`](kodi-config/sources.xml)).

### Library sources — scraper-ready, currently empty

| Source | Path |
|---|---|
| Movies | `D:\Kodi\Media\Movies\` |
| TV Shows | `D:\Kodi\Media\TV Shows\` |
| Music Videos | `D:\Kodi\Media\Music Videos\` |
| Home Videos | `D:\Kodi\Media\Home Videos\` |
| Music | `D:\Kodi\Media\Music\` |

### Browse-only sources — your existing content

`C:\Users\Franc\Videos` (game clips, screen recordings), `C:\Users\Franc\Music`,
`C:\Users\Franc\Pictures`.

These were **intentionally left without a scraper.** TMDB/TVDB would match
nothing against `Roblox clip 04.mp4` and would only pollute the library with junk
entries. They browse as plain files, which is correct for this content.

### ✅ Remaining manual step — assign the scrapers

Scraper assignment lives in Kodi's video **database**, not in any XML, so it
can't be pre-seeded safely. It's a one-time, ~30-second job **per source**, and
only worth doing once you actually put films/shows in those folders:

1. **Videos → Files → hover *Movies* → context menu (`C` or right-click) → Edit source**
2. **Set content** → **Movies**
3. Scraper → *The Movie Database* → **OK** → agree to scan

Repeat for **TV Shows** → *Set content* → **TV shows** → *TheTVDB* or *TMDB*.

### Naming that scrapers reliably match

```
D:\Kodi\Media\Movies\
    Blade Runner 2049 (2017)\Blade Runner 2049 (2017).mkv
    Dune Part Two (2024)\Dune Part Two (2024).mkv

D:\Kodi\Media\TV Shows\
    Severance\Season 01\Severance S01E01.mkv
                        Severance S01E02.mkv
```

The `(year)` on films and `SxxExx` on episodes are what make matching accurate.

---

## 7. The fork & staying up to date

Fork: **[`CoderRvrse/xbmc`](https://github.com/CoderRvrse/xbmc)** → cloned to `D:\Kodi\xbmc`

Cloned with `--filter=blob:none` (blobless). Full history and all branches, but
file contents download on demand: **~230 MB instead of ~1.6 GB**, and far faster
to clone. It behaves like a normal clone for building, branching and pushing.

### Branch layout — and why it's built this way

| Branch | Role |
|---|---|
| `kodi-toolkit` | **Default branch.** Docs, scripts, workflow. Contains nothing from upstream. |
| `master` / `Omega` / `Nexus` | **Pristine mirrors.** Fast-forwarded from upstream daily. Never commit here. |

The mirrors are kept clean on purpose. The moment you commit your own work to
`master`, it diverges from upstream and every future sync becomes a merge that
will eventually conflict. Keeping our files on a separate branch means **every
sync stays a trivial fast-forward, forever.**

That also drives the default-branch choice: GitHub only runs *scheduled*
workflows from a repository's default branch, so `kodi-toolkit` has to be the
default in order for the daily sync to fire while `master` stays untouched.

### Automatic sync

[`.github/workflows/sync-upstream.yml`](.github/workflows/sync-upstream.yml)
runs **daily at 05:17 UTC** and fast-forwards all three mirrors, writing a
summary table to the Actions run. You can also trigger it by hand from the
**Actions** tab (*Run workflow*).

> ⏰ GitHub disables scheduled workflows in a repo with **no activity for 60
> days**. If syncing ever goes quiet, open the Actions tab and re-enable it.

### Manual sync

```powershell
D:\Kodi\kodi-toolkit\tools\sync-upstream.ps1                     # all mirrors
D:\Kodi\kodi-toolkit\tools\sync-upstream.ps1 -Branches master -UpdateLocal
```

Server-side fast-forward push — your working tree and any in-progress branch are
untouched. It refuses to force-push, so a diverged mirror fails loudly rather
than silently losing commits.

### Doing your own work on the fork

```powershell
cd D:\Kodi\xbmc
git fetch upstream
git checkout -b my-feature upstream/master   # branch off upstream, never off a mirror
# ...edit...
git push -u origin my-feature
```

Then open a PR against `xbmc/xbmc` if you want it upstream.

---

## 8. Finishing touches you may want

**YouTube API keys** — `plugin.video.youtube` needs your own Google API
credentials since Google's quota changes. Without them the addon installs fine
but won't play. Create a project at
<https://console.cloud.google.com/>, enable *YouTube Data API v3*, then enter the
key + OAuth client id/secret under
*Add-ons → YouTube → Configure → API*.

**Trakt** — *Add-ons → Trakt → Configure → Authorize*, then enter the code at
<https://trakt.tv/activate>.

**OpenSubtitles** — free account at <https://www.opensubtitles.com/>, then
*Add-ons → OpenSubtitles.com → Configure*.

**Controller for RetroPlayer** — plug in a gamepad, then
*Settings → System → Input → Configure attached controllers*.

**Run Kodi at boot / on a TV** — pass `-fs` for fullscreen. To autostart:
`Win+R` → `shell:startup` → drop a shortcut to `C:\Program Files\Kodi\kodi.exe -fs`.

---

## 9. Troubleshooting & rollback

**Backups taken automatically before any edit:**

| File | Backup |
|---|---|
| `guisettings.xml` | `guisettings.xml.bak` |
| `Database\Addons33.db` | `Addons33.db.bak` |

**Restore stock settings** (with Kodi closed):

```powershell
$ud = "$env:APPDATA\Kodi\userdata"
Copy-Item "$ud\guisettings.xml.bak" "$ud\guisettings.xml" -Force
Copy-Item "$ud\Database\Addons33.db.bak" "$ud\Database\Addons33.db" -Force
```

**Full factory reset** — delete `%APPDATA%\Kodi` entirely; Kodi rebuilds it on
next launch. This destroys your library, addons and settings.

**Logs:** `%APPDATA%\Kodi\kodi.log` (previous run: `kodi.old.log`). For a verbose
log set `<loglevel>1</loglevel>` in `advancedsettings.xml`.

**Known-harmless log line:**
`Error loading include file …\script-skinshortcuts-includes.xml` — Arctic Zephyr
generates that file the first time you customise the home menu. It is logged at
*info* level, not error, and nothing is broken.

**Video stutters / audio out of sync** → lower `readfactor` to `10` and
`memorysize` to `104857600` (100 MB) in `advancedsettings.xml`.

**Black screen on playback** → turn off RTX Video Super Resolution:
*Settings → Player → Videos → Enable VSR* (Expert level).

---

## 10. Quick reference

```powershell
# launch
& 'C:\Program Files\Kodi\kodi.exe'          # add -fs for fullscreen

# sync the fork
D:\Kodi\kodi-toolkit\tools\sync-upstream.ps1

# install more official-repo addons (handles dependencies)
python D:\Kodi\kodi-toolkit\tools\kodi_addons.py install <addon.id>
python D:\Kodi\kodi-toolkit\tools\kodi_addons.py list-skins

# re-apply the tuned settings (Kodi must be CLOSED)
python D:\Kodi\kodi-toolkit\tools\patch_guisettings.py
```

| Path | |
|---|---|
| `C:\Program Files\Kodi` | Program files |
| `%APPDATA%\Kodi\userdata` | Settings, sources, databases |
| `%APPDATA%\Kodi\addons` | Installed add-ons |
| `D:\Kodi\Media` | Media library root |
| `D:\Kodi\xbmc` | Source clone of the fork |
| `D:\Kodi\kodi-toolkit` | This toolkit |

**Links:** [Kodi wiki](https://kodi.wiki/) · [advancedsettings.xml reference](https://kodi.wiki/view/Advancedsettings.xml) · [forum](https://forum.kodi.tv/) · [upstream repo](https://github.com/xbmc/xbmc) · [release mirrors](https://mirrors.kodi.tv/releases/)
