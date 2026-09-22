import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from array import array
import tempfile
import unittest
import wave
from pathlib import Path
import pygame
from main import App
from model import path_to


class Interface(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = App(self.tmp.name)

    def tearDown(self):
        self.app.close()
        self.tmp.cleanup()

    def test_screens_and_all_tiers_render(self):
        for screen in ('menu', 'help', 'settings', 'records'):
            self.app.screen = screen
            self.app.draw()
            self.assertTrue(self.app.buttons)
        for tier in range(5):
            self.app.start(tier)
            for screen in ('play', 'paused', 'result'):
                self.app.screen = screen
                self.app.draw()
            self.app.game.abandon()

    def test_keyboard_pause_focus_loss_and_escape(self):
        self.app.start(0)
        pygame.event.clear()
        self.app.update(.05)
        before = self.app.game.elapsed
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p))
        self.app.events()
        self.assertEqual(self.app.screen, 'paused')
        self.app.update(1)
        self.assertEqual(self.app.game.elapsed, before)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.app.events()
        self.assertEqual(self.app.screen, 'play')
        charges = self.app.game.escapes
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.app.events()
        self.assertEqual(self.app.game.escapes, charges-1)
        pygame.event.post(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.app.events()
        self.assertEqual(self.app.screen, 'paused')

    def test_complete_campaign_and_result_actions(self):
        self.app.action('campaign')
        for tier in range(5):
            g = self.app.game
            g.invulnerable = 999
            for target in sorted(g.seeds)+[g.exit]:
                for cell in path_to(g.grid, g.player, target)[1:]:
                    g.move((cell[0]-g.player[0], cell[1]-g.player[1]))
            self.app.consume_events()
            self.assertEqual(self.app.screen, 'result')
            self.app.draw()
            self.app.action(self.app.result_primary())
        self.assertEqual(self.app.screen, 'menu')
        self.assertEqual(len(self.app.campaign_results), 5)
        self.assertEqual(self.app.store.summary()[1], 5)

    def test_audio_assets_and_mixer_load(self):
        self.assertTrue(self.app.audio.available)
        for path in (Path(__file__).resolve().parents[1]/'assets'/'audio').glob('*.wav'):
            with wave.open(str(path)) as wav:
                self.assertEqual(wav.getframerate(), 22050)
                data = array('h', wav.readframes(wav.getnframes()))
                self.assertGreater(max(data), 100)
                self.assertLess(max(data), 32767)
        self.app.audio.play('escape')
        self.app.action('music')
        self.assertEqual(self.app.audio.music, self.app.store.get('music', None))


if __name__ == '__main__':
    unittest.main()
