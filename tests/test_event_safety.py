import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile,unittest
from unittest.mock import patch
import pygame
from main import App
from event_safety import RAW_JOYSTICK_EVENTS,CONTROLLER_EVENTS,read_events

def failure():
 try: raise KeyError(0)
 except KeyError as cause:
  exc=SystemError('<built-in function get> returned a result with an exception set');exc.__cause__=cause;return exc

class EventSafety(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.a=App(self.tmp.name)
 def tearDown(self):self.a.close();self.tmp.cleanup()
 def test_raw_events_blocked_keyboard_and_quit_work(self):
  self.assertTrue(all(pygame.event.get_blocked(t) for t in RAW_JOYSTICK_EVENTS))
  self.assertTrue(all(pygame.event.get_blocked(t) for t in CONTROLLER_EVENTS))
  pygame.event.post(pygame.event.Event(pygame.QUIT));self.a.events();self.assertFalse(self.a.running)
 def test_exact_failure_pauses_preserves_save_and_recovers(self):
  self.a.start(0);g=self.a.game;g.steps=7
  with patch('pygame.event.get',side_effect=failure()):self.a.events()
  self.assertEqual(self.a.screen,'paused');self.assertFalse(self.a.controls.enabled)
  self.assertEqual(g.steps,7);self.assertIsNotNone(self.a.store.get('active_expedition',None))
  pygame.event.post(pygame.event.Event(pygame.QUIT));self.a.events();self.assertFalse(self.a.running)
 def test_unrelated_and_repeated_failures_not_hidden(self):
  with patch('pygame.event.get',side_effect=SystemError('different bug')):
   with self.assertRaises(SystemError):read_events(self.a)
  self.a.input_recovered=True
  with patch('pygame.event.get',side_effect=failure()):
   with self.assertRaises(SystemError):read_events(self.a)
 def test_keyboard_only_startup(self):
  from controls import Controls
  with patch.dict(os.environ,{'APPLIN_KEYBOARD_ONLY':'1'}):c=Controls(self.a.store)
  self.assertFalse(c.enabled);self.assertEqual(c.pads,{})
  pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_p));self.assertTrue(any(e.type==pygame.KEYDOWN for e in pygame.event.get()))
