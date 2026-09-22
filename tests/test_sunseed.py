import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile
import unittest
import pygame
from main import App
from art import seed,berry

class SunseedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=App(self.tmp.name)
    def tearDown(self):
        self.app.close()
        self.tmp.cleanup()
    def test_shrine_opens_gradually_and_pauses(self):
        self.app.start(4)
        self.app.game.invulnerable=99
        self.assertEqual(self.app.shrine_open,0)
        self.app.game.seeds.clear()
        self.app.update(.05)
        self.assertGreater(self.app.shrine_open,0)
        self.assertLess(self.app.shrine_open,1)
        self.app.screen='paused'
        before=self.app.shrine_open
        self.app.update(.5)
        self.assertEqual(self.app.shrine_open,before)
        self.app.screen='play'
        for _ in range(24): self.app.update(.05)
        self.assertEqual(self.app.shrine_open,1)
        self.app.draw()
        self.app.action('comfort')
        self.app.draw()
    def test_pickups_have_distinct_silhouettes_and_colours(self):
        a=pygame.Surface((40,40),pygame.SRCALPHA)
        b=pygame.Surface((40,40),pygame.SRCALPHA)
        seed(a,(20,20),8)
        berry(b,(20,20),8)
        self.assertNotEqual(pygame.image.tostring(a,'RGBA'),pygame.image.tostring(b,'RGBA'))
        self.assertNotEqual(pygame.mask.from_surface(a).count(),pygame.mask.from_surface(b).count())

if __name__=='__main__':unittest.main()
