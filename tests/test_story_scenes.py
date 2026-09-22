"""Regression checks for the reported restored-garden crash and scene navigation."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile
import unittest
from unittest.mock import patch
import pygame
from main import App
from sanctuary import CHAPTERS,PLOTS
from home_progress import home_progress


class StoryScenes(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.app=App(self.tmp.name)
    def tearDown(self):
        self.app.close(); self.tmp.cleanup()
    def progress(self,restored):
        self.app.store.set('sanctuary_v4',{'restored':restored,'rescued':0,'receipts':[],'chapters':[]})
    def click(self,action):
        a=self.app; a.draw()
        rect=next(r for r,key in a.buttons if key==action)
        pygame.event.clear()
        with patch.object(a,'mouse',return_value=rect.center):
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=rect.center))
            a.events()

    def test_all_gardens_mouse_click_restored_and_waiting(self):
        a=self.app; a.action('sanctuary')
        for restored in ([],list(range(5))):
            self.progress(restored)
            for i in range(5):
                self.click(f'home_plot:{i}')
                self.assertEqual(a.screen,'sanctuary'); self.assertEqual(a.home_selected,i)
                self.assertIn(CHAPTERS[i].goal if restored else 'clear this biome',a.home_notice)

    def test_restored_gardens_keyboard_and_controller_interaction(self):
        a=self.app; self.progress(list(range(5))); a.action('sanctuary')
        for i,pos in enumerate(PLOTS):
            a.home_pos=list(pos)
            pygame.event.clear()
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=a.controls.keys[0][5])); a.events()
            self.assertIn(CHAPTERS[i].goal,a.home_notice)
            a.home_selected=None
            a.control_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN,instance_id=44,button=a.controls.pad_buttons[1]))
            self.assertEqual(a.home_selected,i)

    def test_invalid_garden_indices_are_ignored(self):
        for action in ('home_plot:-1','home_plot:5','home_plot:banana','home_plot:','memory:99','memory:-1'):
            self.app.action(action)
        self.assertIsNone(self.app.home_selected)

    def test_memories_do_not_change_saved_run_or_roll_shiny(self):
        a=self.app; a.coop=True; a.action('story'); a.action('story_begin'); a.action('pause'); a.save_expedition()
        saved=a.store.get('active_expedition',None); before=a.game.snapshot()
        self.progress(list(range(5))); a.action('sanctuary')
        with patch('home_progress.secrets.randbelow',side_effect=AssertionError('memory rerolled')):
            for i in range(5):
                self.click(f'home_plot:{i}'); self.click(f'memory:{i}')
                self.assertTrue(a.story_replay)
                for _ in range(4): a.action('story_forward'); a.draw()
                self.assertEqual(a.story_page,2)
                for _ in range(4): a.action('story_previous'); a.draw()
                self.assertEqual(a.story_page,0)
                a.action('story_begin'); self.assertEqual(a.screen,'story')
                a.action('back'); self.assertEqual(a.screen,'sanctuary')
        self.assertEqual(a.store.get('active_expedition',None),saved)
        self.assertEqual(a.game.snapshot(),before)
        a.action('story'); self.assertFalse(a.story_replay)

    def test_locked_memory_and_last_chapter_next_are_safe(self):
        a=self.app; a.action('sanctuary'); a.action('memory:0'); self.assertEqual(a.screen,'sanctuary')
        a.story_mode=True; a.start(4,'campaign'); a.action('next'); self.assertEqual(a.screen,'sanctuary')

    def test_all_fifteen_scenes_render_and_comfort_is_static(self):
        a=self.app; a.action('story'); a.comfort=True
        pictures=set()
        for tier in range(5):
            for page in range(3):
                a.story_chapter=tier; a.story_page=page; a.t=0; a.draw()
                first=pygame.image.tostring(a.canvas,'RGB')
                pictures.add(first)
                a.t=5; a.draw()
                self.assertEqual(first,pygame.image.tostring(a.canvas,'RGB'))
        self.assertEqual(len(pictures),15)
        a.comfort=False; a.characters=True; a.t=1; a.draw()
        self.assertNotEqual(first,pygame.image.tostring(a.canvas,'RGB'))

if __name__=='__main__': unittest.main()
