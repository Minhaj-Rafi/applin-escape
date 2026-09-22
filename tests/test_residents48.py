import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile,unittest
from main import App
from home_progress import home_progress
from home_activities import care_state,care_action
from residents48 import profile,complete_request,requests

class Residents48(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.a=App(self.tmp.name)
 def tearDown(self):self.a.close();self.tmp.cleanup()
 def test_requests_are_ordered_and_spend_once(self):
  p=home_progress(self.a.store);p['rescued']=1;c=care_state(p);fav=profile(0)[1]
  c['berry_types']={fav:2};c['berries']=2
  self.assertIn('previous',complete_request(p,0,1));self.assertEqual(c['berries'],2)
  c['chatted']=[0];self.assertIn('complete',complete_request(p,0,0))
  self.assertIn('complete',complete_request(p,0,1));self.assertEqual(c['berries'],0)
  self.assertIn('already',complete_request(p,0,1));self.assertEqual(c['berries'],0)
  self.assertIn('not met',complete_request(p,0,2))
  c['friends']={'0':3};c['grown_types']=[fav]
  self.assertIn('ribbon',complete_request(p,0,2));self.assertTrue(all(r[3] for r in requests(c,0)))
 def test_missing_berries_never_spent_and_resident_state_separate(self):
  p=home_progress(self.a.store);p['rescued']=2;c=care_state(p);c['chatted']=[0]
  complete_request(p,0,0);self.assertIn('not met',complete_request(p,0,1))
  self.assertFalse(any(r[3] for r in requests(c,1)))
 def test_personality_dialogue_persists_and_gift_prefers_favourite(self):
  p=home_progress(self.a.store);p['rescued']=2;c=care_state(p);fav=profile(1)[1]
  c['berry_types']={'Oran':2,fav:2};c['berries']=4;self.a.store.set('sanctuary_v4',p)
  first=care_action(self.a.store,'chat',1);second=care_action(self.a.store,'chat',1)
  self.assertNotEqual(first,second);self.assertIn(fav,first)
  care_action(self.a.store,'feed',1)
  c=home_progress(self.a.store)['care'];self.assertEqual(c['berry_types'][fav],1)
  self.assertEqual(c['friends']['1'],2)
 def test_profile_and_preview_navigation_and_no_accidental_apply(self):
  a=self.a;p=home_progress(a.store);p['rescued']=1;a.store.set('sanctuary_v4',p)
  a.action('home_activities');a.action('resident_profile:0');a.draw()
  self.assertEqual(a.home_tab,4)
  a.action('decor_preview');before=a.home_decor
  for i in range(9):
   a.draw();self.assertEqual(a.home_decor,before);a.action('decor_next')
  a.decor_preview48=8;a.action('decor_apply');self.assertEqual(a.home_decor,before)
  a.decor_preview48=0;a.action('decor_apply');self.assertEqual(a.home_decor,'Natural')
  a.action('back');self.assertEqual(a.screen,'home_activities')
