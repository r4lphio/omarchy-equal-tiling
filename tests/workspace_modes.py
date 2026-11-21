"""Exercise Omarchy's workspace layout cycle inside session.py's isolated compositor."""
import json
import subprocess
import time

MESSAGES = {'dwindle': 'layout.workspaceTiling', 'scrolling': 'layout.workspaceScrolling',
            'floating': 'layout.workspaceFloating'}


class Modes:
    """Run Omarchy's own layout commands against the nested compositor."""

    def __init__(self, ctl, env, notifications):
        self.ctl, self.env, self.notifications = ctl, env, notifications

    def command(self, *args):
        return subprocess.run(args, env=self.env, text=True, capture_output=True,
                              check=True, timeout=30).stdout.strip()

    def cycle(self, *direction):
        # The command that Omarchy binds to Super+L, Super+Alt+L, and XF86Display.
        self.command('omarchy-hyprland-workspace-layout-toggle', *direction)

    def current(self, *workspace):
        return self.command('omarchy-hyprland-workspace-layout-current', *workspace)

    def layout(self):
        return json.loads(self.ctl('activeworkspace', '-j'))['tiledLayout']

    def notified(self, mode):
        # The stub in session.py records each notification's text.
        return self.notifications.read_text().splitlines()[-1] == self.command('omarchy-i18n', MESSAGES[mode])


def settle(check, describe):
    # Entering floating can load Omarchy's titlebar plugin, which reloads the config.
    deadline = time.monotonic() + 10
    while not check():
        assert time.monotonic() < deadline, describe()
        time.sleep(.2)


def check_modes(modes, ctl, ev, windows, focus, open_window, layouts):
    def workspace(number):
        ev(f'hl.dispatch(hl.dsp.focus({{workspace="{number}"}}))')

    def floating(labels):
        return [windows()[label]['floating'] for label in labels]

    descriptions = {bind['description'] for bind in json.loads(ctl('binds', '-j'))}
    assert 'Cycle workspace layout' in descriptions, descriptions
    assert 'Toggle equal tiling / scrolling' not in descriptions, descriptions
    assert modes.command('omarchy-hyprland-workspace-layout-default') == 'dwindle'

    workspace(4)
    tiles = ['M1', 'M2', 'M3']
    for label in tiles:
        open_window(label)
    ev('hl.dispatch(hl.plugin.hy3.change_group("h"))')

    def equal_tiles():
        # hy3 picks a row or a column from the shape of the nested window.
        ws = windows()
        sizes = [ws[label]['size'] for label in tiles]
        return (modes.layout() == 'hy3' and not any(floating(tiles))
                and all(max(size[axis] for size in sizes) - min(size[axis] for size in sizes) <= 2 for axis in (0, 1))
                and len({tuple(ws[label]['at']) for label in tiles}) == len(tiles))

    assert modes.current() == 'dwindle' and equal_tiles(), windows()
    for direction, steps in (((), ('scrolling', 'floating', 'dwindle')),
                             (('back',), ('floating', 'scrolling', 'dwindle'))):
        for mode in steps:
            modes.cycle(*direction)
            assert modes.current() == mode, (direction, mode, modes.current())
            assert modes.notified(mode), (mode, modes.notifications.read_text())
            if mode == 'floating':
                settle(lambda: all(floating(tiles)), windows)
                # The plugin's direction keys must leave floating windows to Hyprland.
                focus('M2')
                for key in ('SUPER + LEFT', 'SUPER + SHIFT + LEFT'):
                    # Hyprland reports "no window in that direction" as information.
                    result = ctl('eval', f'test_bindings["{key}"]()')
                    assert result == 'ok' or result.startswith('info:'), result
                assert all(floating(tiles)) and min(min(windows()[label]['size']) for label in tiles) > 100, windows()
            elif mode == 'scrolling':
                settle(lambda: modes.layout() == 'scrolling' and not any(floating(tiles)), windows)
            else:
                settle(equal_tiles, windows)
                # Tiling is the default, so Omarchy removes the workspace's own file.
                assert not (layouts / '4.lua').exists()
    print('PASS: Omarchy layout cycle reaches scrolling and floating and returns to equal tiles', flush=True)

    workspace(5)
    open_window('N1')
    ev('hl.dispatch(test_bindings["SUPER + G"])')
    open_window('N2')
    group = ['N1', 'N2']
    assert len(windows()['N2']['grouped']) == 2, windows()
    modes.cycle('back')
    settle(lambda: all(floating(group)), windows)
    modes.cycle()
    settle(lambda: modes.layout() == 'hy3' and not any(floating(group)), windows)
    assert len(windows()['N2']['grouped']) == 2 and min(windows()['N2']['size']) > 100, windows()
    print('PASS: a native window group floats and tiles again as one group', flush=True)

    # Saved files keep Omarchy's names. This plugin's older releases wrote 7.lua's format.
    (layouts / '6.lua').write_text('o.workspace_mode({ workspace = "6", mode = "dwindle" })\n')
    (layouts / '7.lua').write_text('hl.workspace_rule({workspace = "7", layout = (hl.plugin.hy3 and "hy3" or "dwindle")})\n')
    (layouts / '8.lua').write_text('o.workspace_mode({ workspace = "8", mode = "scrolling" })\n')
    assert ctl('reload') == 'ok'
    for number, mode, layout in ((6, 'dwindle', 'hy3'), (7, 'dwindle', 'hy3'), (8, 'scrolling', 'scrolling'),
                                 (9, 'dwindle', 'hy3')):
        workspace(number)
        settle(lambda: modes.layout() == layout, lambda: (number, modes.layout()))
        assert modes.current() == mode, (number, modes.current())
    assert not ctl('configerrors'), ctl('configerrors')
    print('PASS: saved modes and the default load as equal tiling after a reload', flush=True)


def check_stock_modes(modes, ev):
    """Without the plugin, the same saved files give Omarchy's stock layouts."""
    for number in (6, 7, 9):
        ev(f'hl.dispatch(hl.dsp.focus({{workspace="{number}"}}))')
        assert modes.current() == 'dwindle' and modes.layout() == 'dwindle', (number, modes.layout())
    modes.cycle()
    assert modes.current() == 'scrolling' and modes.layout() == 'scrolling'
    modes.cycle('back')
    assert modes.current() == 'dwindle' and modes.layout() == 'dwindle'


def check_late_load(modes, ctl, ev, library, stamp, module):
    """Load the library after the config, in the order the Omarchy service uses."""
    def lua(path):
        return json.dumps(str(path))

    assert ctl('plugin', 'load', str(library)) == 'ok'
    ev(f'assert(loadfile({lua(module)}))({{loaded=true, plugin_path={lua(library)}, stamp_path={lua(stamp)}}})')
    ev('package.loaded["default.hypr.workspace-layouts"] = nil; require("default.hypr.workspace-layouts")')
    for number in (9, 7, 6):
        ev(f'hl.dispatch(hl.dsp.focus({{workspace="{number}"}}))')
        assert modes.current() == 'dwindle' and modes.layout() == 'hy3', (number, modes.layout())
