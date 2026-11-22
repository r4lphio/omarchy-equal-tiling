"""Exercise the layout cycle with equal tiling inside session.py's isolated compositor."""
import json
import subprocess
import time

MESSAGES = {'dwindle': 'layout.workspaceTiling', 'scrolling': 'layout.workspaceScrolling',
            'floating': 'layout.workspaceFloating'}
# Hyprland's name for the equal tiling layout. Omarchy's commands print it for a
# workspace with no saved mode, and "equal" for a saved equal tiling mode.
EQUAL = 'hy3'
FORWARD = ('dwindle', 'scrolling', 'floating', EQUAL)
BACK = ('floating', 'scrolling', 'dwindle', EQUAL)


class Modes:
    """Read and step layout modes with Omarchy's own commands."""

    def __init__(self, ctl, ev, env, notifications, layouts):
        self.ctl, self.ev, self.env = ctl, ev, env
        self.notifications, self.layouts = notifications, layouts

    def command(self, *args):
        return subprocess.run(args, env=self.env, text=True, capture_output=True,
                              check=True, timeout=30).stdout.strip()

    def cycle(self, *direction):
        # The command that Omarchy binds to Super+L, Super+Alt+L, and the display key.
        self.command('omarchy-hyprland-workspace-layout-toggle', *direction)

    def press(self, key):
        # The plugin's binding. It starts Omarchy's command without waiting for it.
        self.ev(f'test_bindings["{key}"]()')

    def current(self, *workspace):
        return self.command('omarchy-hyprland-workspace-layout-current', *workspace)

    def layout(self):
        # The layout that Hyprland really uses, not the name a saved file gives.
        return json.loads(self.ctl('activeworkspace', '-j'))['tiledLayout']

    def workspace(self, number):
        self.ev(f'hl.dispatch(hl.dsp.focus({{workspace="{number}"}}))')

    def saved(self, number):
        path = self.layouts / f'{number}.lua'
        return path.read_text() if path.exists() else None

    def notified(self, mode):
        # The stub in session.py records each notification's text.
        expected = ('Workspace layout set to equal tiling' if mode == EQUAL
                    else self.command('omarchy-i18n', MESSAGES[mode]))
        return self.notifications.read_text().splitlines()[-1:] == [expected]

    def reached(self, mode):
        """Wait for a step. Floating keeps the tiled layout that was there."""
        names = (EQUAL, 'equal') if mode == EQUAL else (mode,)
        settle(lambda: self.current() in names and self.notified(mode)
               and (mode == 'floating' or self.layout() == mode),
               lambda: (mode, self.current(), self.layout(), self.notifications.read_text()))


def settle(check, describe):
    # Steps run outside the compositor. Floating can also load Omarchy's
    # titlebar plugin, which reloads the config.
    deadline = time.monotonic() + 10
    while not check():
        assert time.monotonic() < deadline, describe()
        time.sleep(.2)


def check_modes(modes, ctl, ev, windows, focus, open_window):
    def floating(labels):
        return [windows()[label]['floating'] for label in labels]

    for key in ('SUPER + L', 'SUPER + ALT + L', 'XF86Display'):
        ev(f'assert(type(test_bindings["{key}"]) == "function")')
    # Equal tiling is the default without a file that would outlive the plugin.
    assert modes.command('omarchy-hyprland-workspace-layout-default') == EQUAL
    assert modes.saved('default') is None

    modes.workspace(4)
    tiles = ['M1', 'M2', 'M3']
    for label in tiles:
        open_window(label)

    def equal_tiles():
        # hy3 picks a row or a column from the shape of the nested window.
        ws = windows()
        sizes = [ws[label]['size'] for label in tiles]
        return (not any(floating(tiles))
                and all(max(size[axis] for size in sizes) - min(size[axis] for size in sizes) <= 2 for axis in (0, 1))
                and len({tuple(ws[label]['at']) for label in tiles}) == len(tiles))

    assert modes.current() == EQUAL and modes.layout() == EQUAL and equal_tiles(), windows()
    for key, steps in (('SUPER + L', FORWARD), ('SUPER + ALT + L', BACK)):
        for mode in steps:
            modes.press(key)
            modes.reached(mode)
            if mode == 'floating':
                settle(lambda: all(floating(tiles)), windows)
                # The plugin's direction keys must leave floating windows to Hyprland.
                focus('M2')
                for arrow in ('SUPER + LEFT', 'SUPER + SHIFT + LEFT'):
                    # Hyprland reports "no window in that direction" as information.
                    result = ctl('eval', f'test_bindings["{arrow}"]()')
                    assert result == 'ok' or result.startswith('info:'), result
                assert all(floating(tiles)) and min(min(windows()[label]['size']) for label in tiles) > 100, windows()
            elif mode == EQUAL:
                settle(equal_tiles, windows)
                # Equal tiling is the default, so the workspace has no file of its own.
                assert modes.saved(4) is None, modes.saved(4)
            else:
                settle(lambda: not any(floating(tiles)), windows)
                assert f'mode = "{mode}"' in modes.saved(4), modes.saved(4)
    print('PASS: layout cycle steps through equal tiling, stock dwindle, scrolling, and floating, both ways', flush=True)

    modes.workspace(5)
    open_window('N1')
    ev('hl.dispatch(test_bindings["SUPER + G"])')
    open_window('N2')
    group = ['N1', 'N2']
    assert len(windows()['N2']['grouped']) == 2, windows()
    modes.press('SUPER + ALT + L')
    modes.reached('floating')
    settle(lambda: all(floating(group)), windows)
    modes.press('XF86Display')
    modes.reached(EQUAL)
    settle(lambda: not any(floating(group)), windows)
    assert len(windows()['N2']['grouped']) == 2 and min(windows()['N2']['size']) > 100, windows()
    print('PASS: a native window group floats and tiles again as one group', flush=True)

    # Like Omarchy's command, the cycle leaves a named workspace alone.
    ev('hl.dispatch(hl.dsp.focus({workspace="name:eq"}))')
    before = sorted(path.name for path in modes.layouts.glob('*.lua'))
    modes.press('SUPER + L')
    time.sleep(1)
    assert modes.layout() == EQUAL and sorted(path.name for path in modes.layouts.glob('*.lua')) == before

    # Saved files after a reload. This plugin's 0.3 releases wrote 7.lua's format.
    modes.workspace(4)
    modes.press('SUPER + L')
    modes.reached('dwindle')
    (modes.layouts / '6.lua').write_text('o.workspace_mode({ workspace = "6", mode = "equal" })\n')
    (modes.layouts / '7.lua').write_text('hl.workspace_rule({workspace = "7", layout = (hl.plugin.hy3 and "hy3" or "dwindle")})\n')
    (modes.layouts / '8.lua').write_text('o.workspace_mode({ workspace = "8", mode = "scrolling" })\n')

    def reloaded():
        assert ctl('reload') == 'ok'
        for number, mode, name in ((4, 'dwindle', 'dwindle'), (6, EQUAL, 'equal'), (7, EQUAL, EQUAL),
                                   (8, 'scrolling', 'scrolling'), (9, EQUAL, EQUAL)):
            modes.workspace(number)
            settle(lambda: modes.layout() == mode and modes.current() == name,
                   lambda: (number, modes.layout(), modes.current()))
        assert not ctl('configerrors'), ctl('configerrors')

    reloaded()
    print('PASS: saved modes, old files, and the equal tiling default keep their layouts after a reload', flush=True)

    # A default layout that is saved in Omarchy stays in charge. Equal tiling is
    # then a saved mode of the workspace.
    (modes.layouts / 'default.lua').write_text('o.workspace_mode({ default = "scrolling" })\n')
    assert ctl('reload') == 'ok'
    modes.workspace(11)
    settle(lambda: modes.layout() == 'scrolling' and modes.current() == 'scrolling', modes.layout)
    for mode in ('floating', EQUAL, 'dwindle', 'scrolling'):
        modes.press('SUPER + L')
        modes.reached(mode)
        saved = modes.saved(11)
        # Stepping onto Omarchy's default removes the workspace's own file.
        name = 'equal' if mode == EQUAL else mode
        assert (saved is None) if mode == 'scrolling' else (f'mode = "{name}"' in saved), (mode, saved)
    (modes.layouts / 'default.lua').unlink()
    reloaded()
    print('PASS: a default layout saved in Omarchy stays the default, with equal tiling as a saved mode', flush=True)


def check_stock_modes(modes, ctl):
    """Without the plugin, saved state gives stock layouts and Omarchy's own cycle."""
    assert not ctl('configerrors'), ctl('configerrors')
    for number in (4, 6, 7, 9):
        modes.workspace(number)
        assert modes.layout() == 'dwindle', (number, modes.layout())
    # A saved equal tiling mode is an unknown name to Omarchy. It steps to its first mode.
    modes.workspace(6)
    for direction, steps in (((), ('dwindle', 'scrolling', 'floating', 'dwindle')), (('back',), ('floating',))):
        for mode in steps:
            modes.cycle(*direction)
            modes.reached(mode)
    modes.cycle()
    modes.reached('dwindle')


def check_late_load(modes, ctl, ev, library, stamp, module):
    """Load the library after the config, in the order the Omarchy service uses."""
    def lua(path):
        return json.dumps(str(path))

    # Omarchy loaded this saved mode before the library gave it a layout.
    saved = 'o.workspace_mode({ workspace = "6", mode = "equal" })'
    (modes.layouts / '6.lua').write_text(saved + '\n')
    ev(saved)
    modes.workspace(6)
    assert modes.layout() == 'dwindle'
    assert ctl('plugin', 'load', str(library)) == 'ok'
    ev(f'assert(loadfile({lua(module)}))({{loaded=true, plugin_path={lua(library)}, stamp_path={lua(stamp)}}})')
    ev('package.loaded["default.hypr.workspace-layouts"] = nil; require("default.hypr.workspace-layouts")')
    for number, mode, name in ((9, EQUAL, EQUAL), (7, EQUAL, EQUAL), (6, EQUAL, 'equal'), (4, 'dwindle', 'dwindle')):
        modes.workspace(number)
        settle(lambda: modes.layout() == mode and modes.current() == name,
               lambda: (number, modes.layout(), modes.current()))
    # The module followed the saved modes: back from Omarchy's first mode is equal tiling.
    modes.press('SUPER + ALT + L')
    modes.reached(EQUAL)
    assert modes.saved(4) is None
