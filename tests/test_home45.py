import os
os.environ['SDL_VIDEODRIVER']='dummy'; os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile,unittest
from datetime import date
from main import App
from home_progress import home_progress
from home_activities import care_state,care_action
from rewards44 import record_interaction,sanctuary_tasks,reward_rows

class Home45(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.a=App(self.tmp.name)
 def tearDown(self): self.a.close(); self.tmp.cleanup()
 def test_menu_buttons_do_not_overlap(self):
  a=self.a; a.screen='menu'; a.draw()
  for i,(r,k) in enumerate(a.buttons):
   for r2,k2 in a.buttons[i+1:]: self.assertFalse(r.colliderect(r2),(k,k2))
 def test_live_notice_ticks_and_becomes_ripe(self):
  a=self.a; a.care_notice='Still growing: old'; a.care_timer_bed=0
  care={'berries':0,'crops':[{'kind':0,'ready_at':200,'watered':True},None,None]}
  self.assertIn('1:40',a.live_care_notice(care,100))
  self.assertIn('1:39',a.live_care_notice(care,101))
  self.assertTrue(a.live_care_notice(care,200).startswith('Ready to harvest'))
 def test_streak_same_day_gap_and_backwards_clock(self):
  care={}
  for d in (1,1,2,3): record_interaction(care,date(2026,9,d))
  self.assertEqual(care['visits45']['best'],3)
  self.assertEqual(care['visits45']['days'],3)
  record_interaction(care,date(2026,9,5)); record_interaction(care,date(2026,9,2))
  self.assertEqual(care['visits45']['streak'],1); self.assertEqual(care['visits45']['best'],3)
 def test_all_categories_and_persistence(self):
  a=self.a; p=home_progress(a.store); p['rescued']=30; p['restored']=list(range(5)); c=care_state(p)
  c.update(harvests=30,friends={str(i):3 for i in range(10)},chatted=list(range(10)),feeds45=20,grown_types=['Oran','Pecha','Cheri','Sitrus'])
  c['harvest_methods44']={n:{m:6 for m in ('Any harvest','Watered','Natural')} for n in c['grown_types']}
  for d in range(1,15): record_interaction(c,date(2026,9,d))
  a.store.set('sanctuary_v4',p)
  tasks=sanctuary_tasks(a.store); self.assertEqual(len(tasks),96)
  self.assertTrue(all(t['current']>=t['target'] for t in tasks[:72]))
  self.assertTrue(reward_rows(a.store,'home')[-1][2])
  a.action('home_rewards'); a.action('completion_film'); a.draw()
 def test_chat_counts_but_opening_menu_does_not(self):
  a=self.a; a.action('home_hub')
  self.assertNotIn('visits45',home_progress(a.store).get('care',{}))
  p=home_progress(a.store); p['rescued']=1; a.store.set('sanctuary_v4',p)
  care_action(a.store,'chat',0)
  self.assertEqual(home_progress(a.store)['care']['visits45']['days'],1)
