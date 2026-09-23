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
        canvas_point = self.app.touch.directions['right'][0].center
        width, height = self.app.window.get_size()
        scale = min(width/1280, height/840)
        point = ((width-1280*scale)/2+canvas_point[0]*scale,
                 (height-840*scale)/2+canvas_point[1]*scale)
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))
        self.app.events()
        self.assertGreaterEqual(self.app.game.steps, before)
        self.assertEqual(self.app.touch.direction(), (1, 0))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=point))
        self.app.events()
        self.assertIsNone(self.app.touch.direction())

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
