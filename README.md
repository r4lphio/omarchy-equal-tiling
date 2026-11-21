# COSMIC-style equal tiling for Omarchy

An Omarchy service plugin that aims to replicate the equal tiling and directional
window movement of the [COSMIC desktop from Pop!_OS](https://system76.com/cosmic).
It builds a patched [hy3](https://github.com/outfoxxed/hy3) and applies the layout
while the plugin is enabled. It does not edit your Hyprland configuration files.

This is an independent implementation. It is not affiliated with or endorsed by
System76, and it does not reproduce every COSMIC desktop feature.

![New windows open side by side at equal widths, then key presses stack, move, and widen them](preview.gif)

Press Super+Shift+an arrow to move the focused window through the layout tree.
Moving across a split creates a group, enters a neighboring group, or steps out
of the current group. At the workspace edge, movement stops. New windows get an
equal share of their group, and the plugin keeps sizes you set by hand. A
Hyprland config reload rebuilds the layout with equal tiles.

For example, with `A | D | (B / C)`, focus D and press Right twice. The result is
`A | (B / D / C)`. B, D, and C share the right half equally.

## Requirements

Tested with Hyprland **0.56.2** and Omarchy's Lua configuration and Quickshell
plugin system. On Hyprland **0.57.2**, the layout tests pass in a disposable
nested compositor, and the plugin runs on one live desktop. The plugin
lifecycle test has not yet run on 0.57.2. The builder selects the hy3 source
for the installed Hyprland release, 0.56.x or 0.57.x. Other releases stop with
a message that names the supported versions. Older `.conf` setups are
unsupported. Keep Omarchy's standard `~/.config` location.

The build needs Python 3.9+, curl 8.4.0+, tar, patch, CMake, Ninja, pkg-config, a C++23
compiler, and development files for Hyprland, pixman, libdrm, Pango, libinput,
Wayland, and xkbcommon. The plugin does not install system packages or use sudo.
The first build requires internet access to download pinned hy3 source.

On an up-to-date Omarchy installation, install the build dependencies from a
terminal:

```bash
omarchy pkg add base-devel cmake ninja python curl pixman libdrm pango libinput wayland libxkbcommon
```

This command installs missing system packages and may ask for your password.
The plugin does not run it for you. Arch includes development headers in these
packages. Hyprland's headers come from the installed `hyprland` package and must
match your compositor. After a Hyprland update, log out and back in before enabling
the plugin.

To check setup before enabling, add the plugin without `--enable`, then run:

```bash
omarchy plugin add https://github.com/r4lphio/omarchy-equal-tiling --yes
python3 ~/.config/omarchy/plugins/ralphsmith80.equal-tiling/install.py --check
omarchy plugin enable ralphsmith80.equal-tiling
```

From a checkout, use `python3 install.py --check`. It checks the system tools,
curl version, C++23 language support, Hyprland headers, and development libraries.
Missing requirements include their Arch package names. It also reports a Hyprland
release that has no pinned hy3 source. The check makes no network requests and
does not install packages or change your desktop. A passing check does not
compile the native source.
Fresh builds run the same check before downloading source. A valid cached build
does not require the build tools again.

Do not load another copy of hy3 alongside this plugin. If you installed version
0.1.0 with `install.py`, use its printed rollback command first. A custom
`hypr.dotfiles` loader that supplies equal tiling must also stop loading hy3
before this plugin can take over. The service reports a conflict and leaves an
existing hy3 instance alone.

## Install

```bash
omarchy plugin add https://github.com/r4lphio/omarchy-equal-tiling --enable --yes
```

The first enable builds hy3 in the background. Once ready, the service loads it
and applies the shortcuts below. Allow a few minutes for compilation. Check:

```bash
hyprctl plugin list
hyprctl configerrors
```

The plugin list should show `hy3`, with no configuration errors. The underlying
layout and Lua namespace retain the upstream name.

Build and service messages go to
`${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-equal-tiling/service.log`.
If the build fails, resolve the reported dependency or version problem, then
disable and enable the plugin to retry.

## Shortcuts

| Shortcut | Action |
| --- | --- |
| Super+arrows | Focus a window through hy3's layout tree |
| Super+Shift+arrows | Move a window through tiling groups |
| Super+Alt+P | Toggle the priority column, or make all tiles equal |
| Super+L | Omarchy's layout cycle, with equal tiling as its tiling layout |

The first three replace Omarchy's directional focus and directional swap
shortcuts while enabled, and add the priority column. Omarchy's Super+J split
toggle, Super+G window grouping, and related tab shortcuts remain available.
Super+Ctrl+Backspace centers a lone tile using Omarchy's single-window square
setting. Custom
`layout.single_window_aspect_ratio` and tolerance values also apply.
Movement does not move windows across monitors. This plugin
does not reproduce COSMIC's tab behavior.

Super+Alt+P works on a workspace with three columns side by side. Focus the
middle column and press it. That column takes half the width, and the two side
columns share the other half. On a 7680 px ultrawide, the middle column is the
width of one 4K display. Press Super+Alt+P again to make all tiles equal. In
any other layout, the shortcut makes all tiles on the workspace equal.

Super+L stays Omarchy's own layout cycle: tiling, scrolling, floating. So do
Super+Alt+L, the display key, and the layout button in the bar. While the
plugin is enabled, the tiling layout is equal tiling in place of dwindle.
Omarchy's notifications, saved files, and bar keep their own names, so they
call it tiling. A floating workspace floats the tiles, and the next press puts
them back as equal tiles. On a floating window, the arrow shortcuts do what
Omarchy does without the plugin. When you disable the plugin, the same saved
layouts give Omarchy's dwindle again.

Omarchy's layout commands read the default layout from a saved file. When that
file does not exist and the default is tiling, the plugin saves that default in
`~/.local/state/omarchy/workspace-layouts/default.lua`, in Omarchy's own
format. Without the file, the first Super+L press on a workspace would do
nothing. The file stays after you disable or remove the plugin, and then means
Omarchy's dwindle. Another default that you chose under Appearance > Workspace
Layout stays your default. Equal tiling is then the tiling step of the cycle.

On an Omarchy release without these workspace modes, the plugin keeps its own
Super+L. It switches the workspace between equal tiling and scrolling, saves
the choice, and does nothing on a named workspace.

## Updates and removal

```bash
omarchy plugin update ralphsmith80.equal-tiling --yes
omarchy plugin disable ralphsmith80.equal-tiling
omarchy plugin enable ralphsmith80.equal-tiling
omarchy plugin remove ralphsmith80.equal-tiling --yes
```

Update applies the new service code. Disable and removal unload the native
plugin and reload your saved Hyprland configuration. Cleanup can take a few
seconds. They also stop an unfinished build. Restarting the Omarchy shell keeps
the service active; ending the Hyprland session stops it. The service ignores
SIGTERM, so a broad command such as `pkill -f python3` does not turn equal tiling
off. It writes a line to the service log instead, and restarts a build that the
signal stopped. To stop the service from a terminal, send SIGINT. It then unloads
hy3 like a disable. SIGKILL skips that cleanup and leaves hy3 loaded until you
log out.

After updating Hyprland, log out and back in. The service rebuilds against the
installed headers when needed. An update from 0.56 to 0.57 also selects the hy3
source for the new release. The service refuses to load a build that does not
match the running compositor.

Builds remain under `${XDG_CACHE_HOME:-$HOME/.cache}/omarchy-equal-tiling` for reuse.
Removal keeps that cache, the service log, and your saved workspace choices. You
can delete the cache and log directory after removing the plugin.

## What runs on your computer

Omarchy loads `Service.qml`, which starts a Python worker. The worker uses
Hyprland IPC to load the native library, apply Lua bindings, and restore the
saved configuration on disable. It follows Omarchy's enabled service state and
allows one worker per Hyprland session.

The builder verifies the pinned source archive's SHA-256 before unpacking and
compiling it. Downloads use HTTPS only, with a 15-second connection timeout,
a 120-second transfer deadline, and an 8 MiB size limit, including responses
without a declared size. Checksum verification reads fixed-size chunks.

The worker starts `/usr/bin/python3` with Python environment and site startup
hooks disabled. It receives only home, cache, state, runtime, Hyprland session,
and notification bus paths. Build commands use fixed tools under `/usr/bin`,
an empty temporary home, and a fixed environment. Custom compiler flags,
toolchains, loader settings, proxy variables, and user curl configuration are
not used. Updating from the older build policy requires a fresh native build.

Native plugins execute inside Hyprland. The code makes no telemetry
or upload requests. Review the source before enabling it, as with other
unsandboxed Omarchy plugins.

## Standalone installer

The older standalone install remains available for users who do not want the
Omarchy service. Use only one installation method.

```bash
git clone https://github.com/r4lphio/omarchy-equal-tiling.git
cd omarchy-equal-tiling
python3 install.py --build
python3 install.py          # Preview changes
python3 install.py --apply  # Back up and install
```

This method installs `~/.config/hypr/equal-tiling.lua`, the library and build stamp
under `~/.local/lib/omarchy-equal-tiling`, and a loader in `hyprland.lua`. Each apply
prints an exact rollback command. Backups live under
`~/.local/state/omarchy-equal-tiling/restore-*`. Undo multiple applies in reverse
order. Rollback refuses to overwrite later local edits. Reconcile those edits
before retrying. Rebuild and apply after Hyprland updates.

## Development

```bash
omarchy plugin validate .
python3 install.py --check
python3 -m unittest discover -s tests -v
python3 tests/launcher.py
python3 install.py --build
python3 tests/session.py
python3 tests/plugin_session.py
EQUAL_TILING_TEST_FRESH=1 python3 tests/plugin_session.py
```

The download tests use curl and OpenSSL against a local HTTPS server. The launcher
test checks the actual QML process environment with an offscreen Quickshell.
The session tests need an active Wayland desktop and `foot`. They use temporary
homes and separate nested Hyprland sessions. The plugin test also starts a private
Omarchy shell and runs the real add, enable, disable, update, and remove commands.
The fresh-build mode interrupts the first build, then verifies that enabling
again compiles and activates the plugin. See [VALIDATION.md](VALIDATION.md).

To recreate `preview.gif` and `preview.png`, run `uv run tests/capture_preview.py`
after building. It requires `foot`, `grim`, `ffmpeg`, `bat`, `eza`, and `uv`. It opens
five terminal windows in a disposable compositor at 1920x960 and presses the real
bindings. It floats and resizes only that temporary window in the parent Hyprland
session. The wallpaper is added after capture, in place of the background color.
All text is public repository content; it does not capture the active desktop.
`preview.png` is a still from the same recording, because the plugin marketplace
accepts only static previews.

`HY3_SOURCES` in `install.py` pins one upstream hy3 commit for each Hyprland
release series. The builder reads the series from Hyprland's `version.h`.

| Hyprland | Patch | hy3 commit | Archive SHA-256 |
| --- | --- | --- | --- |
| 0.56.x | `hy3.patch` | `42b7ed8fd9aefd3f36e5f617afd5071245c67853` | `b4b8842cdfb0562f1f4228ef35c746f040379a33ee0912ad089f693206c34076` |
| 0.57.x | `hy3-0.57.patch` | `4c0199b42967b3511e3520b75cfa1f6411fb7e87` | `ab84e5cab4cd437a95a2a121390ba0609969ded02c815dc34e33d2d07f89dc63` |

The two patches make the same changes. They differ only in the name of the
workspace type, which Hyprland 0.57 changed. Keep them in sync. Each patch adds
`hl.plugin.hy3.move_cosmic(direction)`, honors Hyprland's single-window
aspect settings, and implements target swapping for native window groups.
It leaves upstream movement and focus dispatchers intact. Update a commit, its
checksum, and its patch together, then build and run the checks before
publishing a release.

## License and credit

GPL-3.0, see [LICENSE](LICENSE). hy3 is by outfoxxed and its contributors.
Ralph Smith's package adds the directional movement patch, Omarchy configuration,
service, and installer. Omarchy-derived configuration retains its MIT notice in
[LICENSE.omarchy](LICENSE.omarchy).
