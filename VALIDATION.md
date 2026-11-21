# Validation

## Omarchy workspace layout cycle

Validated on 2026-11-21 on two machines: Hyprland 0.56.2 with Omarchy 4.5.0,
and Hyprland 0.57.2 with an Omarchy edge build. Both Omarchy versions have the
layout cycle with a floating mode.

- Ran `python3 tests/session.py` on both machines, in a disposable nested
  compositor with a temporary home and state directory. All 18 checks passed on
  both. The test config now loads `default.hypr.toggles`, so saved layouts load
  after the plugin's loader, as in a real standalone install.
- The test runs Omarchy's own `omarchy-hyprland-workspace-layout-toggle`, the
  command behind Super+L, Super+Alt+L, and the display key. A forward cycle and
  a back cycle each went through scrolling and floating and returned to three
  equal hy3 tiles. After each step, `omarchy-hyprland-workspace-layout-current`
  printed the mode, and the notification text matched Omarchy's message for it.
  `omarchy-hyprland-workspace-layout-default` printed `dwindle`.
- The test replaces `omarchy-notification-send` and `omarchy-shell` with stubs,
  so the nested run sends nothing to the desktop's notifications or shell.
- On the floating workspace, the plugin's Super+Left and Super+Shift+Left ran
  Hyprland's own focus and swap, and the windows stayed floating.
- A native window group floated with the workspace and tiled again as one
  group of two.
- After a reload, a saved `mode = "dwindle"` file, a file in the format of the
  plugin's older releases, and a workspace with no file all used hy3. A saved
  scrolling file used scrolling. Omarchy's command printed `dwindle` for the
  first three.
- With the plugin skipped by a mismatched build stamp, the same files gave
  stock dwindle, and Omarchy's cycle switched between its stock layouts.
- Loaded the library after the config, with the two Lua steps that the Omarchy
  service runs. The saved files and the default then used hy3.
- All 31 unit tests passed on both machines. The layout files of the live
  desktops did not change during the nested runs.

Not validated: an Omarchy without workspace modes, which keeps the plugin's
own Super+L toggle. Neither machine has one. `tests/plugin_session.py` and
`tests/capture_preview.py` got the same helper loading as the session test, but
were not run. The service itself, the bar, the dock, and the Appearance menu
were not exercised. Titlebars on floating windows were not inspected.

## Hyprland 0.57

Validated on 2026-11-21 on two machines: Hyprland 0.56.2 with Omarchy 4.5.0,
and Hyprland 0.57.2 with an Omarchy edge build.

- On Hyprland 0.56.2, `python3 install.py --build` selected hy3 commit
  `42b7ed8f` and `hy3.patch`, and the build passed. The build signature is the
  same as before this change, so cached builds stay valid.
- On Hyprland 0.57.2, the same command selected hy3 commit `4c0199b4` and
  `hy3-0.57.patch`. All 8 build steps passed. The build stamp holds the 0.57.2
  commit.
- Compared the symbols that each library needs with the symbols that the
  installed Hyprland and its libraries export. No symbol was missing on either
  version.
- All 31 automated tests passed on both machines. Four new tests cover source
  selection, the message for an unsupported release, the signature change after
  an upgrade, and stopping before download.
- Compared the Hyprland 0.56.2 and 0.57.2 sources for the calls that the patch
  adds: `hasFullscreen`, `tiledTargets`, `workArea`, the single-window aspect
  options, and the callers of `swapTargets`. The signatures and callers are the
  same. The port changes only the workspace type name in two lines.
- Ran `python3 tests/session.py` on both machines. It loads the built library
  in a disposable nested compositor with a temporary home. All 14 checks passed
  on Hyprland 0.56.2 and on 0.57.2: single-window ratios with fullscreen,
  Super+J, native window groups, directional movement, 40 random moves, the
  priority column, saved layouts, reload, a mismatched build, and installer
  rollback. No nested compositor stayed behind.
- The session test did not start on current Omarchy. Omarchy's default tiling
  bindings now read `o.workspaces`, and the test had its own copy of `o` with
  `bind` only. The test now loads `default.hypr.helpers` and
  `default.hypr.monitor-workspaces`, as Omarchy does, and records the bindings.
  The single-window check sets zero tolerance, so it no longer depends on the
  shape of the nested window.
- Added a check for workspaces with no numbered id. Before the fix, Super+Alt+P
  on a special workspace with three columns failed on Hyprland 0.57.2: the
  columns stayed equal. On Hyprland 0.56.2, Super+L on a named workspace saved
  a layout file for it. Both pass after the fix on both versions.

Not validated on Hyprland 0.57.2 by these runs: the Omarchy service.
`tests/plugin_session.py` was not run. It starts a second Omarchy shell and
runs the real plugin commands, so it is less isolated than the session test.
These runs loaded no library into a live desktop. Multiple monitors and a full
Omarchy configuration are not covered by the nested test. After these runs, the
owner enabled this branch on the live Hyprland 0.57.2 desktop, where it loaded.

## Animated preview

Validated on 2026-10-01 with Hyprland 0.56.2.

- Ran `uv run tests/capture_preview.py`. Five windows opened side by side at
  equal widths. The script then pressed the real bindings from
  `config/hypr/equal-tiling.lua` through the test binding table. Geometry checks
  passed for five equal columns, a stack of three equal windows, a half-width
  priority column, and three equal columns after the second Super+Alt+P.
- Inspected `preview.png` (1920x960) and frames from `preview.gif` (1000x500,
  12 fps, about 23 seconds). Window text comes from an export of the committed
  files and tag names only. The wallpaper replaces one background color after
  capture.
- A failed frame capture now stops the run with an error. Each window command
  must exit 0 with output before recording starts.

## Setup check and preview

Validated on 2026-10-01 with Hyprland 0.56.2.

- `python3 install.py --check` passed against the installed tools and development
  libraries. In a read-only Bubblewrap filesystem with Ninja and Hyprland's
  pkg-config file hidden, it returned exit 1 and named both missing requirements.
  The sandbox had no network access and did not change system packages.
- All 26 automated tests passed, including grouped prerequisite failures,
  unsupported tool versions, check exit status, and stopping before download.
- Exercised cancelled-build recovery and a fresh native build through the actual
  Omarchy service. The library compiled and loaded in the disposable compositor.
  The full lifecycle test then passed using the verified cached build.
- Corrected two test assumptions exposed during fresh-build runs. The square
  assertion now sets zero aspect-ratio tolerance in the test compositor. The
  reload test waits for the service callback instead of accepting Omarchy's
  temporary default dispatcher. Runtime tiling code is unchanged.
- Captured and inspected the 1600x900 preview from four real windows. Geometry
  checks confirmed equal column widths and three equal heights on the right.
  The screenshot contains public demo text only.
- Checked dependency package names against the installed Arch package database
  and repository metadata. Manifest validation and diff checks passed. An
  independent scenario review found no P1 or P2 issues.

## Build security changes

Validated on 2026-09-29 against Hyprland 0.56.2 and curl 8.22.0.

- Rebuilt the pinned native source with invalid inherited PATH, CC, CXX,
  CMAKE_TOOLCHAIN_FILE, CMAKE_PROJECT_INCLUDE, CMAKE_PROJECT_INCLUDE_BEFORE,
  CXXFLAGS, LDFLAGS, LD_PRELOAD, PYTHONPATH, PKG_CONFIG_PATH, TAR_OPTIONS, and
  CURL_HOME values. The build used the system compiler and completed successfully.
- Tested actual curl transfers against a local HTTPS server. Oversized responses
  with and without Content-Length stopped with exit 63. A stalled response hit
  the total deadline with exit 28. Invalid checksums removed the download.
  Valid downloads ignored user curl configuration. Older curl versions were
  rejected before transfer because they lack a streaming size limit.
- Checked the actual QML launcher in an offscreen Quickshell with a fake Python
  on PATH and a Python startup hook. The worker used `/usr/bin/python3`, disabled
  site startup and Python environment controls, and received only the documented
  session environment. This test also caught and fixed a missing Quickshell.Io
  import that a full Omarchy shell had masked.
- Ran the fresh-build plugin lifecycle test in a disposable home, nested
  compositor, and private shell. Cancelling a build, enabling again, loading hy3,
  reload, disable/enable, rapid toggles, ownership conflict, update, shell restart,
  and removal passed. The test did not edit the active desktop's configuration.
- All 22 automated tests passed. The separate layout and installer session test,
  manifest validation, and diff checks passed. An independent scenario review
  found no P1 or P2 issues. The QML linter reports the Quickshell.Io import as
  unused, but the standalone launcher test confirms it is needed to register
  the process context type.

The catalog's approval and automated validation are separate from these local
checks. The corrected commit still needs marketplace revalidation and review.

## Initial validation

Validated on 2026-09-16 with Hyprland 0.56.2, commit
`efb50993780079460b0cbed1363e2166a2de1d9f`, on Linux x86_64.

- Downloaded the pinned hy3 archive, verified its SHA-256, applied the patch,
  and compiled the shared library against the installed headers.
- All 16 unit tests passed. The 14 installer tests cover backups, byte and permission
  preservation, local edits, write failures, concurrent edits, symlink conflicts,
  loader insertion, build-cache integrity, conflicting dotfiles setup, and an
  editor save between configuration collection and apply.
- Loaded the built library in a separate nested Hyprland session with a temporary
  home and four real foot windows. No plugin was loaded into the existing desktop.
- Verified directional grouping, equal sibling sizes, workspace-edge behavior,
  and 40 mixed-direction moves. All windows kept positive sizes and did not
  overlap. Focus stayed on the moved window.
- Verified floating and retiling, saved workspace layout toggles, configuration
  reload, and movement after reload.
- Verified custom XDG_STATE_HOME layouts take priority over conflicting
  default-state files across two reloads, including the missing-plugin fallback.
- Changed the temporary install's build stamp to an incompatible commit. Reload
  skipped the plugin without configuration errors. Restoring the stamp loaded
  the plugin again.
- Ran the real installer in the temporary home. Preview wrote no configuration,
  repeated apply changed no files, and rollback restored the prior main config
  and removed the installed module and library.

The nested test uses Omarchy's module bootstrap and a minimal configuration.
Other Hyprland releases, multiple monitors, and full desktop startup on another
machine have not been tested. Reproduce with the commands in README.md.

## Priority column and manual sizes in 0.3.0

Validated on 2026-09-24 with the same Hyprland build.

- Removed automatic balancing. The first grouping check and the 40 random moves
  still passed, so hy3 keeps tiles equal without it.
- Pressed Super+Alt+P on the middle of three columns. Each side column was
  within 4 px of a quarter of the combined width, and the middle column was
  within 8 px of half.
- Opened and closed a fourth window and switched workspaces. The three widths
  stayed within 4 px of their priority sizes.
- Pressed Super+Alt+P again on the middle column, and then on a side column
  while priority was on. Both times, all tiles became equal.
- Made the right column over 75% wide, then pressed Super+Alt+P. Both side
  columns reached a quarter. The wider side is resized first, and a second pass
  corrects the few pixels that hy3 loses to gaps.
- Built two rows of three windows and pressed Super+Alt+P on the top middle
  window. Both rows got the priority split.
- With window animations slowed down, Lua reported the final window size right
  after a resize. The second pass therefore reads settled sizes.
- Ran the plugin lifecycle test and all 16 unit tests again. All passed.

## Omarchy plugin lifecycle in 0.2.0

- Validated `manifest.json` with `omarchy plugin validate` and checked `Service.qml`
  with Qt's QML linter.
- Started the real Omarchy shell on a private D-Bus session with a temporary home
  and a separate nested compositor.
- Ran actual `omarchy plugin add --enable`, disable, enable, update, and remove.
  Verified that add loads hy3, reload restores movement bindings, update runs the
  new Lua module, and disable/removal unload hy3 without editing Hyprland files.
- Restarted the isolated shell while enabled and then removed the plugin.
- Loaded a separate hy3 instance, enabled the service, and confirmed it reported
  the conflict without unloading or replacing that instance.
- Ran three rapid disable/enable cycles and verified that tiling stayed active.
- Cancelled an uncached native build, then enabled again. The retry downloaded,
  compiled, and activated the plugin successfully.
- Added deterministic tests for re-enable during cleanup and kernel build-lock
  release after SIGTERM. These reproduce both service review findings.

## Publication review

Independent scenario reviews covered the installer, layout, and Omarchy service
lifecycle. The service review found two disable/re-enable bugs. Both were fixed
and have regression tests. No concrete high- or medium-severity findings remain
open after review and runtime verification.

- Fixed a first-install race that could replace an editor save made after the
  installer read the main configuration. Apply now checks the original input
  fingerprint before any write. A regression test confirms the edit survives.
- Fixed balancing being skipped while the focused window is floating.
- Fixed saved layout paths and module lookup when XDG_STATE_HOME is customized.
  The module gives that directory priority before the plugin version guard so
  fallback layouts also load correctly.
- Scanned tracked files and reachable Git history for embedded credentials,
  private keys, known token formats, and private machine paths. None were found.
  Public commit metadata uses GitHub's noreply email address.
- Reviewed network and command execution. The installer downloads pinned hy3
  source over HTTPS and checks its SHA-256 before unpacking or building. No
  unexpected uploads or telemetry were found in the reviewed code.
- Retained upstream GPL and Omarchy MIT notices. The README credits COSMIC as
  the intended behavior and states the limits of this independent implementation.
## Omarchy window controls in 0.3.1

- Built the pinned native source with the updated patch against Hyprland 0.56.2.
- Ran `python3 tests/session.py` in a disposable nested compositor. Verified
  centered 1:1 and 4:3 single-window ratios, tolerance, fullscreen transitions,
  adding and closing a second tile, disabling the ratio, and pseudotiling.
- Verified that Omarchy's Super+J binding remains registered and changes a split
  in both directions. Native Super+G groups retained usable geometry, accepted a
  second window, switched tabs by cycle and index, extracted and rejoined a
  window, and dissolved back into tiles.
- The existing movement, equal sizing, priority column, floating, reload,
  saved-layout, build mismatch, and installer rollback checks also passed.
- Ran `python3 tests/plugin_session.py` with a private Omarchy shell. The actual
  square-toggle command resized the window after the service reapplied the
  layout, and toggling off restored its size. Super+J remained registered.
  Add, enable, disable, update, reload, ownership conflict, and removal passed.
- All 16 installer and service unit tests passed. `omarchy plugin validate .`
  and `git diff --check` passed. An independent code review found no P1 or P2
  findings.
