import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile,unittest
from unittest.mock import patch
import pygame
from main import App

class ChallengeCode531(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.app=App(self.tmp.name)
 def tearDown(self):self.app.close();self.tmp.cleanup()
 def test_shared_code_persists_but_direct_entry_opens_blank(self):
  a=self.app;a.start();code=a.game.code;a.action('pause')
  with patch.object(a,'_copy_challenge_text',return_value=True):a.action('copy_code')
  self.assertEqual(a.screen,'challenge');self.assertEqual(a.challenge_input,code)
  self.assertEqual(a.challenge_selection(),(0,len(code)))
  self.assertEqual(a.store.get('last_shared_code43',''),code)
  a.action('back');a.action('challenge')
  self.assertEqual(a.challenge_input,'');self.assertTrue(a.challenge_focus)
  a.action('challenge_latest')
  self.assertEqual(a.challenge_input,code);self.assertEqual(a.challenge_selection(),(0,len(code)))
 def test_copy_paste_select_and_replace(self):
  a=self.app;a.screen='challenge';a.challenge_focus=True;a._set_challenge_text('AE52-1-ABCDEF-000000',select=True)
  copied=[]
  with patch.object(a,'_copy_challenge_text',side_effect=lambda value:copied.append(value) or True):a.action('challenge_copy')
  self.assertEqual(copied,[a.challenge_input])
  a._set_challenge_text('AE52-',select=False);a.challenge_anchor=0;a.challenge_cursor=5
  with patch.object(a,'_read_challenge_clipboard',return_value='AE42-2-1234-000000'):a.action('challenge_paste')
  self.assertEqual(a.challenge_input,'AE42-2-1234-000000')
  self.assertEqual(a.challenge_selection(),(len(a.challenge_input),len(a.challenge_input)))
 def test_keyboard_and_mouse_selection(self):
  a=self.app;a.screen='challenge';a._set_challenge_text('AE52-1-ABCDEF-000000')
  a.challenge_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_a,unicode='a',mod=pygame.KMOD_CTRL))
  self.assertEqual(a.challenge_selection(),(0,len(a.challenge_input)))
  a.challenge_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_BACKSPACE,unicode='',mod=0))
  self.assertEqual(a.challenge_input,'')
  a._set_challenge_text('AE52-TEST')
  with patch.object(a,'canvas_point',side_effect=lambda p:p):
   a.challenge_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(80,240),clicks=1))
   a.challenge_event(pygame.event.Event(pygame.MOUSEMOTION,pos=(140,240),buttons=(1,0,0)))
   a.challenge_event(pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=(140,240)))
  lo,hi=a.challenge_selection();self.assertEqual(lo,0);self.assertGreater(hi,0)

if __name__=='__main__':unittest.main()
