import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile,unittest
from unittest.mock import Mock,patch
import pygame
from main import App
from release_info import VERSION
from support49 import snapshot

class Release51(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  # This unit test owns simulated devices; ignore hardware on the build PC.
  with patch('controls.sdl_controller.get_count',return_value=0):self.a=App(self.tmp.name)
 def tearDown(self):self.a.close();self.tmp.cleanup()
 def test_controller_removed_during_probe_is_safe(self):
  c=self.a.controls;pad=Mock();pad.attached.side_effect=pygame.error('unplugged');joy=Mock();c.pads={9:(pad,0)};c.joysticks={9:joy};c.enabled=True
  with patch('pygame.joystick.get_count',return_value=0):self.assertTrue(c.refresh(force=True))
  self.assertEqual(c.pads,{});self.assertEqual(c.joysticks,{});joy.quit.assert_called_once()
 def test_controller_keeps_joystick_alive_until_close(self):
  c=self.a.controls;joy=Mock();joy.get_instance_id.return_value=8;pad=Mock();pad.attached.return_value=True;c.enabled=True
  joy.get_init.return_value=True;joy.get_name.return_value='DualSense Wireless Controller'
  with patch('pygame.joystick.get_count',return_value=1),patch('controls.sdl_controller.is_controller',return_value=True),patch('controls.sdl_controller.Controller',return_value=pad),patch('pygame.joystick.Joystick',return_value=joy):
   c.refresh(force=True);c.refresh(force=True)
  self.assertIs(c.joysticks[8],joy);self.assertEqual(len(c.pads),1);c.close();self.assertEqual(c.joysticks,{})
 def test_version_caption_and_report_agree(self):
  self.assertIn(VERSION,pygame.display.get_caption()[0]);self.assertEqual(snapshot(self.a)['game_version'],VERSION)
