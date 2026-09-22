import os
os.environ['SDL_VIDEODRIVER']='dummy'; os.environ['SDL_AUDIODRIVER']='dummy'
import copy,tempfile,unittest
from types import SimpleNamespace
from main import App
from home_progress import home_progress,credit_home,decorations
from home_activities import care_state,care_action
from home_mastery46 import deliver,advanced_tasks,home_milestones
from rewards44 import reward_rows

class Mastery46(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.a=App(self.tmp.name)
 def tearDown(self): self.a.close(); self.tmp.cleanup()
 def test_delivery_is_atomic_and_spends_exact_recipe(self):
  p=home_progress(self.a.store); c=care_state(p); c['berry_types']={'Oran':6,'Pecha':1}; c['berries']=7
  before=copy.deepcopy(p); self.assertIn('Nothing was spent',deliver(p,0));self.assertEqual(before,p)
  c['berry_types']['Pecha']=2;c['berries']=8
  self.assertIn('delivered',deliver(p,0));self.assertEqual(c['berries'],0);self.assertEqual(c['projects46'],{'0':1})
  deliver(p,0);self.assertEqual(c['projects46'],{'0':1})
 def test_resident_gate_and_decorations(self):
  p=home_progress(self.a.store);c=care_state(p);c['berry_types']={n:100 for n in ('Oran','Pecha','Cheri','Sitrus')};c['berries']=400
  self.assertIn('residents',deliver(p,5));self.assertEqual(c['berries'],400)
  p['rescued']=20;c['friends']={str(i):3 for i in range(8)}
  for i in range(6): deliver(p,i)
  self.assertIn('Market stall',decorations(p));self.assertIn('Welcome gazebo',decorations(p))
  self.assertEqual(len(home_milestones(p)),16)
 def test_mixed_beds_count_once_and_require_variety(self):
  p=home_progress(self.a.store);c=care_state(p)
  c['crops']=[{'kind':i,'ready_at':0,'watered':False} for i in range(3)]
  self.a.store.set('sanctuary_v4',p)
  care_action(self.a.store,'harvest',0);care_action(self.a.store,'harvest',1)
  self.assertEqual(home_progress(self.a.store)['care']['mixed_beds46'],1)
 def test_rescue_receipts_and_difficulty_conditions(self):
  g=SimpleNamespace(store=self.a.store,mode='practice',state='cleared',stage_id='one',tier=4,rescued=2,skill='Expert',hits=0)
  credit_home(g);credit_home(g)
  m=home_progress(self.a.store)['rescue_mastery46'];self.assertEqual(m,{'biomes':[4],'expert':1,'careful':1})
  g.stage_id='two';g.skill='Relaxed';credit_home(g)
  self.assertEqual(home_progress(self.a.store)['rescue_mastery46'],m)
  g.stage_id='tutorial';g.mode='tutorial/Expert';g.skill='Expert';credit_home(g)
  self.assertEqual(home_progress(self.a.store)['rescue_mastery46'],m)
 def test_full_mastery_reachable_without_changing_old_rewards(self):
  p=home_progress(self.a.store);p['rescued']=100;c=care_state(p)
  c.update(harvests=160,friends={str(i):3 for i in range(35)},mixed_beds46=8,projects46={str(i):4 for i in range(6)})
  c['harvest_methods44']={n:{'Any harvest':32,'Watered':16,'Natural':16} for n in ('Oran','Pecha','Cheri','Sitrus')}
  p['rescue_mastery46']={'biomes':list(range(5)),'expert':15,'careful':10}
  self.assertTrue(all(t['current']>=t['target'] for t in advanced_tasks(p)))
  self.assertIn('Sanctuary monument',decorations(p))
  self.a.store.set('sanctuary_v4',p)
  self.a.reward_domain='home';self.a.screen='completion_film';self.a.draw()
 def test_filters_pin_and_screen_button_geometry(self):
  a=self.a;a.action('garden_collection');a.garden_filter=3;a.draw();self.assertEqual(len(a.filtered_home_tasks()),24)
  a.action('pin_home:72');a.action('home_hub');a.draw();self.assertEqual(a.store.get('pinned_home46',''),'72')
  a.action('hub_tab:0')
  for tab in (0,1,2,3):
   a.home_tab=tab;a.draw()
   for i,(r,k) in enumerate(a.buttons):
    for r2,k2 in a.buttons[i+1:]: self.assertFalse(r.colliderect(r2),(tab,k,k2))
  for decor in ('Market stall','Welcome gazebo','Sanctuary monument'):
   a.home_decor=decor;a.screen='sanctuary';a.draw()
