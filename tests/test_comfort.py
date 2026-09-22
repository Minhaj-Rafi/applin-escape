import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile
import unittest
import pygame
from main import App


class ComfortTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=App(self.tmp.name)

    def tearDown(self):
        self.app.close()
        self.tmp.cleanup()

    def test_old_animation_preference_does_not_override_low_motion_default(self):
        self.app.store.set('motion',True)
        self.app.close()
        self.app=App(self.tmp.name)
        self.assertFalse(self.app.comfort)
        self.assertFalse(self.app.motion)
        self.app.action('comfort')
        self.app.start(4)
        origin=(self.app.ox,self.app.oy,self.app.cell)
        self.app.game.player=self.app.game.exit
        self.app.visual_player=list(self.app.game.exit)
        self.app.camera()
        self.assertEqual(origin,(self.app.ox,self.app.oy,self.app.cell))
        self.app.action('overview')
        self.assertTrue(self.app.overview)
        self.app.action('motion')
        self.assertFalse(self.app.motion)

    def test_comfort_frames_are_static_without_gameplay_movement(self):
        self.app.action('comfort')
        self.app.start(4)
        self.app.t=0
        self.app.draw()
        first=pygame.image.tostring(self.app.canvas,'RGB')
        self.app.t=3.14
        self.app.draw()
        self.assertEqual(first,pygame.image.tostring(self.app.canvas,'RGB'))
        self.app.screen='menu'
        self.app.t=0
        self.app.draw()
        first=pygame.image.tostring(self.app.canvas,'RGB')
        self.app.t=7
        self.app.draw()
        self.assertEqual(first,pygame.image.tostring(self.app.canvas,'RGB'))

    def test_statuses_distinguish_actual_chase_stun_and_decoy(self):
        self.app.start(4)
        g=self.app.game
        for e in g.enemies:
            e.mood='chase'
        g.enemies[0].stunned=1
        g.enemies[1].mood='patrol'
        statuses=self.app.predator_statuses()
        self.assertEqual(sum(s=='CHASING' for _,s in statuses),3)
        self.assertEqual(len(statuses),5)
        self.assertEqual(statuses[0][1],'STUNNED')
        g.decoy_time=2
        self.assertEqual(sum(s=='CHASING' for _,s in self.app.predator_statuses()),0)
        self.app.draw()

    def test_comfort_setting_persists_and_exit_states_render(self):
        self.app.action('comfort')
        self.assertTrue(self.app.comfort)
        self.app.close()
        self.app=App(self.tmp.name)
        self.assertTrue(self.app.comfort)
        self.app.start(4)
        self.assertTrue(self.app.overview)
        self.assertFalse(self.app.motion)
        self.app.game.seeds.clear()
        self.app.draw()
        self.app.screen='settings'
        self.app.draw()
        for rect,_ in self.app.buttons:
            self.assertTrue(self.app.canvas.get_rect().contains(rect))

    def test_quiet_zone_holds_camera_and_has_no_independent_drift(self):
        self.app.start(4)
        self.app.action('overview')
        self.app.visual_player=[12.,8.]
        self.app.camera()
        origin=(self.app.ox,self.app.oy)
        self.app.visual_player=[13.,8.]
        self.app.camera()
        self.assertEqual(origin,(self.app.ox,self.app.oy))
        self.app.visual_player=[23.,15.]
        self.app.camera()
        moved=(self.app.ox,self.app.oy)
        self.assertNotEqual(origin,moved)
        for _ in range(10):
            self.app.camera()
        self.assertEqual(moved,(self.app.ox,self.app.oy))
        self.app.action('overview')
        self.assertTrue(self.app.overview)



if __name__=='__main__':
    unittest.main()
