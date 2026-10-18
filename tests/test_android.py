import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['APPLIN_TEST_MODE'] = '1'

import tempfile
import time
import unittest

import pygame

from main import App
from network_coop import LanClient, LanHost


def wait_for(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(.02)
    return False


class FakeTransport:
    connected = True
    status = 'Connected.'
    def __init__(self):
        self.messages = []
    def send(self, kind, **values):
        self.messages.append({'type': kind, **values})
        return True
    def poll(self):
        return []
    def close(self):
        self.connected = False


class AndroidInterface(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = App(self.tmp.name)

    def tearDown(self):
        self.app.close()
        self.tmp.cleanup()

    def test_nearby_screens_render_and_have_no_overlapping_buttons(self):
        self.app.android = True
        for screen in ('nearby_coop', 'remote_code', 'remote_lobby'):
            self.app.screen = screen
            self.app.remote_role = 'guest'
            self.app.draw()
            for i, (left, _) in enumerate(self.app.buttons):
                for right, _ in self.app.buttons[i+1:]:
                    self.assertFalse(left.colliderect(right), (screen, left, right))
        for screen in ('help', 'settings', 'controls', 'adventure'):
            self.app.screen = screen
            self.app.draw()
            self.assertTrue(self.app.buttons)

    def test_android_text_input_enters_challenge_code(self):
        self.app.android = True
        self.app.screen = 'challenge'
        self.app.challenge_focus = True
        event = pygame.event.Event(pygame.TEXTINPUT, text='AE52-1-ABC')
        self.assertTrue(self.app.challenge_event(event))
        self.assertEqual(self.app.challenge_input, 'AE52-1-ABC')

    def test_touch_pad_moves_and_releases(self):
        self.app.start(0)
        self.app.touch.enabled = True
        self.app.move_timer = 0
        before = self.app.game.steps
        point = self.app.touch.layout(self.app)['directions']['right'][0].center
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))
        self.app.events()
        self.assertGreaterEqual(self.app.game.steps, before)
        self.assertEqual(self.app.touch.direction(), (1, 0))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=point))
        self.app.events()
        self.assertIsNone(self.app.touch.direction())

    def test_sliding_thumb_changes_direction(self):
        self.app.start(0)
        self.app.touch.enabled = True
        layout = self.app.touch.layout(self.app)
        width, height = self.app.window.get_size()
        def finger(kind, name):
            x, y = layout['directions'][name][0].center
            return pygame.event.Event(kind, finger_id=3, x=x/width, y=y/height, dx=0, dy=0)
        self.app.touch.handle(self.app, finger(pygame.FINGERDOWN, 'left'))
        self.assertEqual(self.app.touch.direction(), (-1, 0))
        self.assertEqual(self.app.touch.handle(self.app, finger(pygame.FINGERMOTION, 'up')), ('move', (0, -1)))
        self.assertEqual(self.app.touch.direction(), (0, -1))
        self.app.touch.handle(self.app, finger(pygame.FINGERUP, 'up'))
        self.assertIsNone(self.app.touch.direction())

    def test_touch_layout_fits_phones_tablets_and_foldables(self):
        from mobile_ui import TouchPad
        # (window pixels, Android density, cutout insets, expect side columns)
        devices = {
            '20:9 phone': ((2400, 1080), 2.625, (0, 0, 0, 0), True),
            '20:9 phone with notch': ((2400, 1080), 2.625, (96, 0, 0, 0), True),
            'small 20:9 phone': ((1600, 720), 2.0, (0, 0, 0, 0), True),
            '16:9 phone': ((1920, 1080), 2.625, (0, 0, 0, 0), False),
            '16:10 tablet': ((1920, 1200), 1.5, (0, 0, 0, 0), False),
            '4:3 tablet': ((2048, 1536), 2.0, (0, 0, 0, 0), False),
            'foldable inner screen': ((2208, 1768), 2.625, (0, 0, 0, 0), False),
            'low-density 16:10 tablet': ((1280, 800), 1.0, (0, 0, 0, 0), False),
        }
        for name, ((width, height), dp, insets, sidebars) in devices.items():
            layout = TouchPad.build_layout(width, height, dp, insets)
            self.assertEqual(layout['sidebars'], sidebars, name)
            controls = [rect for rect, _ in layout['directions'].values()] + list(layout['actions'].values())
            screen = pygame.Rect(0, 0, width, height)
            safe = pygame.Rect(insets[0], insets[1], width-insets[0]-insets[2], height-insets[1]-insets[3])
            for i, rect in enumerate(controls):
                self.assertTrue(safe.contains(rect), (name, rect))
                self.assertGreaterEqual(rect.w, 48*dp, (name, rect))
                for other in controls[i+1:]:
                    self.assertFalse(rect.colliderect(other), (name, rect, other))
                if sidebars:
                    self.assertFalse(rect.colliderect(layout['area']), (name, rect))
            area = layout['area']
            full = min(width/1280, height/840)
            self.assertGreaterEqual(min(area.w/1280, area.h/840), full*.85 - 1e-9, name)
            self.assertTrue(screen.contains(area), name)

    def test_portrait_layout_puts_game_on_top_and_controls_below(self):
        from mobile_ui import TouchPad, PORTRAIT_PIECES, PORTRAIT_SIZE
        devices = {
            '20:9 phone': ((1080, 2400), 2.625, (0, 0, 0, 0)),
            'phone with notch': ((1080, 2400), 2.625, (0, 96, 0, 63)),
            'small phone': ((720, 1600), 2.0, (0, 0, 0, 0)),
            'narrow low-density phone': ((480, 854), 1.5, (0, 0, 0, 0)),
            '16:9 phone': ((1080, 1920), 2.625, (0, 0, 0, 0)),
            'tablet': ((1600, 2560), 2.0, (0, 0, 0, 0)),
            '4:3 tablet': ((1536, 2048), 2.0, (0, 0, 0, 0)),
            'foldable': ((1768, 2208), 2.625, (0, 0, 0, 0)),
        }
        for name, ((width, height), dp, insets) in devices.items():
            layout = TouchPad.build_layout(width, height, dp, insets)
            self.assertTrue(layout['portrait'], name)
            area = layout['area']
            self.assertEqual(area.top, insets[1], name)
            self.assertAlmostEqual(area.w/area.h, PORTRAIT_SIZE[0]/PORTRAIT_SIZE[1], places=2)
            # The game picture fills most of the width and over half the usable height.
            self.assertGreater(area.h, (height-insets[1]-insets[3])*.5, name)
            unit = area.w/PORTRAIT_SIZE[0]
            pieces = [pygame.Rect(area.x+dx*unit, area.y+dy*unit, src[2]*unit, src[3]*unit)
                      for src, (dx, dy) in PORTRAIT_PIECES]
            controls = [rect for rect, _ in layout['directions'].values()] + list(layout['actions'].values())
            safe = pygame.Rect(0, insets[1], width, height-insets[1]-insets[3])
            for i, rect in enumerate(controls):
                self.assertEqual(rect.collidelist(pieces), -1, (name, rect))
                self.assertTrue(safe.contains(rect), (name, rect))
                self.assertGreaterEqual(min(rect.w, rect.h), 48*dp - 1, (name, rect))
                for other in controls[i+1:]:
                    self.assertFalse(rect.colliderect(other), (name, rect, other))
            size, logical_dp, logical_insets = TouchPad.logical_window(width, height, dp, insets)
            logical_area = TouchPad.build_layout(*size, logical_dp, logical_insets)['area']
            self.assertAlmostEqual(logical_area.w/PORTRAIT_SIZE[0], 1, delta=.01)

    def test_portrait_taps_reach_the_split_hud(self):
        from mobile_ui import TouchPad
        size, self.app.touch_dp, self.app.touch_insets = TouchPad.logical_window(1080, 2400, 2.625)
        self.app.window = pygame.display.set_mode(size)
        self.app.touch.enabled = True
        self.app.start(0)
        self.app.draw()
        pieces = self.app.present_pieces()
        self.assertEqual(len(pieces), 3)
        for src, dst in pieces:
            x, y = self.app.canvas_point(dst.center)
            self.assertAlmostEqual(x, src.centerx, delta=1)
            self.assertAlmostEqual(y, src.centery, delta=1)

    def test_map_button_toggles_full_map(self):
        self.app.start(0)
        before = self.app.overview
        self.app._mobile_command('map')
        self.assertNotEqual(self.app.overview, before)

    def test_gpu_window_holds_game_at_one_to_one(self):
        from mobile_ui import TouchPad
        for (width, height), dp in (((2400, 1080), 2.625), ((1600, 720), 2.0), ((1920, 1080), 2.625),
                                    ((2048, 1536), 2.0), ((2208, 1768), 2.625)):
            size, logical_dp, insets = TouchPad.logical_window(width, height, dp)
            self.assertAlmostEqual(size[0]/size[1], width/height, places=2)
            area = TouchPad.build_layout(*size, logical_dp, insets)['area']
            self.assertAlmostEqual(min(area.w/1280, area.h/840), 1, delta=.01)

    def test_tilt_sensors_are_not_controllers(self):
        from controls import is_motion_sensor
        self.assertTrue(is_motion_sensor('Android Accelerometer'))
        self.assertTrue(is_motion_sensor('Gyroscope'))
        self.assertFalse(is_motion_sensor('Xbox Wireless Controller'))
        self.assertFalse(is_motion_sensor(None))
        self.assertEqual(os.environ.get('SDL_ACCELEROMETER_AS_JOYSTICK'), '0')

    def test_touch_direction_beats_other_held_input(self):
        self.app.start(0)
        self.app.touch.enabled = True
        self.app.touch.held['finger'] = (0, 1)
        self.app.controls.held = lambda *_: [(1, 0)]
        moves = []
        from unittest import mock
        with mock.patch.object(type(self.app.game), 'move', lambda game, d: moves.append(d) or True):
            self.app.move_timer = 0
            self.app.update(.01)
        del self.app.controls.held
        self.assertEqual(moves[0], (0, 1))

    def test_phones_follow_applin_up_close(self):
        self.app.android = True
        self.app.start(2)
        self.assertFalse(self.app.overview)
        self.assertEqual(self.app.cell, 48)

    def test_menus_use_full_screen_and_play_uses_touch_area(self):
        self.app.touch.enabled = True
        self.app.screen = 'menu'
        self.assertEqual(self.app.touch.canvas_area(self.app, *self.app.window.get_size()),
                         pygame.Rect((0, 0), self.app.window.get_size()))
        self.app.start(0)
        left, top, scale = self.app.canvas_rect()
        x, y = self.app.canvas_point((left+640*scale, top+420*scale))
        self.assertAlmostEqual(x, 640, places=3)
        self.assertAlmostEqual(y, 420, places=3)
        self.app.draw()

    def test_compressed_snapshot_restores_exact_remote_state(self):
        self.app.coop = True
        self.app.start(2)
        transport = FakeTransport()
        self.app.remote_transport = transport
        self.app.remote_role = 'host'
        self.app.game.move((1, 0))
        self.app._send_remote_state(True)
        message = transport.messages[-1]
        self.assertEqual(message['type'], 'start')
        self.assertIsInstance(message['snapshot'], str)
        self.assertLess(len(message['snapshot']), 16000)
        with tempfile.TemporaryDirectory() as other:
            guest = App(other)
            try:
                guest.remote_role = 'guest'
                guest._apply_remote_state(message)
                self.assertEqual(guest.game.stage_id, self.app.game.stage_id)
                self.assertEqual(guest.game.player, self.app.game.player)
                self.assertEqual([e.pos for e in guest.game.enemies],
                                 [e.pos for e in self.app.game.enemies])
                self.assertEqual(guest.game.shiny, self.app.game.shiny)
                guest.remote_transport = FakeTransport()
                charges = guest.game.escapes
                guest.action('escape')
                self.assertEqual(guest.game.escapes, charges)
                self.assertEqual(guest.remote_transport.messages[-1]['action'], 'escape')
            finally:
                guest.close()


class NearbyNetwork(unittest.TestCase):
    def test_lan_code_authentication_and_bidirectional_messages(self):
        host = LanHost('Test host', port=0, code='2468')
        client = LanClient('127.0.0.1', host.port, '2468')
        try:
            self.assertTrue(wait_for(lambda: host.connected and client.connected))
            self.assertTrue(client.send('command', action='move', direction=[1, 0]))
            messages = []
            self.assertTrue(wait_for(lambda: bool(messages.extend(host.poll()) or messages)))
            self.assertEqual(messages[-1]['action'], 'move')
            self.assertTrue(host.send('state', screen='play', snapshot='example'))
            replies = []
            self.assertTrue(wait_for(lambda: bool(replies.extend(client.poll()) or any(m['type']=='state' for m in replies))))
            self.assertTrue(any(message['type'] == 'state' for message in replies))
        finally:
            client.close()
            host.close()

    def test_wrong_lobby_code_is_rejected(self):
        host = LanHost('Test host', port=0, code='2468')
        client = LanClient('127.0.0.1', host.port, '9999')
        try:
            self.assertTrue(wait_for(lambda: client.peer is not None))
            self.assertTrue(wait_for(lambda: not client.connected, timeout=9))
            self.assertFalse(host.connected)
        finally:
            client.close()
            host.close()


if __name__ == '__main__':
    unittest.main()
