import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile,unittest
from unittest.mock import patch
import pygame
from controls import Controls,RawPad
from model import Store

class FakeJoy:
 def __init__(self,name='DualSense Wireless Controller'):self.name=name;self.buttons=set();self.hat=(0,0);self.axes=[0.,0.];self.live=True
 def get_name(self):return self.name
 def get_attached(self):return self.live
 def get_numbuttons(self):return 16
 def get_button(self,i):return i in self.buttons
 def get_numhats(self):return 1
 def get_hat(self,i):return self.hat
 def get_numaxes(self):return 2
 def get_axis(self,i):return self.axes[i]
 def get_instance_id(self):return 71
 def get_init(self):return True
 def quit(self):self.live=False

class Controller53(unittest.TestCase):
 def setUp(self):pygame.init();self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def test_unmapped_dualsense_face_buttons_stick_and_dpad(self):
  joy=FakeJoy();pad=RawPad(joy)
  joy.buttons={1};self.assertTrue(pad.get_button(pygame.CONTROLLER_BUTTON_A))
  joy.buttons={0};self.assertTrue(pad.get_button(pygame.CONTROLLER_BUTTON_X))
  joy.buttons=set();joy.hat=(0,1);self.assertTrue(pad.get_button(pygame.CONTROLLER_BUTTON_DPAD_UP))
  joy.axes[0]=.8;self.assertGreater(pad.get_axis(pygame.CONTROLLER_AXIS_LEFTX),20000)
 def test_polling_emits_one_edge_and_supports_raw_fallback(self):
  with patch('pygame.joystick.get_count',return_value=0):c=Controls(self.store)
  c.enabled=True
  joy=FakeJoy();pad=RawPad(joy);c.pads={71:(pad,0)};c.joysticks={71:joy};c.button_states={71:set()};c.device_names={71:joy.name}
  with patch('pygame.joystick.get_count',return_value=1):
   joy.buttons={1};first=c.poll_events();second=c.poll_events()
  self.assertEqual([(e.instance_id,e.button) for e in first],[(71,pygame.CONTROLLER_BUTTON_A)])
  self.assertEqual(second,[]);c.close()
 def test_disconnect_is_reported_without_device_event_queue(self):
  with patch('pygame.joystick.get_count',return_value=0):c=Controls(self.store)
  c.enabled=True
  joy=FakeJoy();pad=RawPad(joy);c.pads={71:(pad,0)};c.joysticks={71:joy};c.button_states={71:set()}
  joy.live=False
  with patch('pygame.joystick.get_count',return_value=0):events=c.poll_events()
  self.assertEqual(len(events),1);self.assertEqual(events[0].type,pygame.CONTROLLERDEVICEREMOVED);self.assertEqual(c.pads,{})
