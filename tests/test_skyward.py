import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile
import unittest
import pygame
from main import App
from model import TIERS

class SkywardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=App(self.tmp.name)
    def tearDown(self):
        self.app.close()
        self.tmp.cleanup()
    def test_every_stage_starts_full_map(self):
        for tier in range(5):
            self.app.start(tier)
            self.assertTrue(self.app.overview)
            self.app.action('overview')
            self.assertFalse(self.app.overview)
            self.app.game.abandon()
    def test_flight_animation_does_not_change_path_positions(self):
        self.app.start(4)
        before=[e.pos for e in self.app.game.enemies]
        for frame in range(8):
            self.app.t=frame/10
            self.app.draw()
        self.assertEqual(before,[e.pos for e in self.app.game.enemies])
        for species in ('pidgeotto','spearow','murkrow','talonflame','cramorant'):
            a=self.app.sprites.get(species,80,0)
            b=self.app.sprites.get(species,80,2)
            self.assertNotEqual(pygame.image.tostring(a,'RGBA'),pygame.image.tostring(b,'RGBA'))
        self.app.action('characters')
        self.assertFalse(self.app.characters)
    def test_rebalanced_difficulty_all_five_stages(self):
        self.assertEqual([t.escapes for t in TIERS],[3,2,2,1,1])
        self.assertEqual([t.detection for t in TIERS],[12,16,20,24,30])
        self.assertEqual([t.enemy_delay for t in TIERS],[.28,.23,.19,.17,.155])

if __name__=='__main__':unittest.main()
