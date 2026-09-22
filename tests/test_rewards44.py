import os
os.environ['SDL_VIDEODRIVER']='dummy'; os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile,unittest
import pygame
from main import App
from rewards44 import garden_stamps,garden_tasks,reward_rows,equipped
from garden_timers import crop_action
from home_progress import home_progress
from home_activities import care_state
from challenge_hall import combinations

class Rewards(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.a=App(self.tmp.name)
 def tearDown(self): self.a.close(); self.tmp.cleanup()
 def test_sanctuary_menu_has_no_duplicate_or_maze_links(self):
  a=self.a; a.action('home_hub'); a.draw()
  self.assertEqual([key for _,key in a.buttons],['home_tour','hub_tab:0','garden_collection','back'])
  a.action('hub_tab:0'); a.draw(); self.assertEqual(a.home_tab,0)
  a.action('back'); self.assertEqual(a.screen,'home_hub')
  a.action('back'); a.draw(); self.assertIn('challenge_hall',[key for _,key in a.buttons])
 def test_all_garden_stamps_without_maze_credit(self):
  a=self.a; p=home_progress(a.store); c=care_state(p)
  for kind in range(4):
   for watered in (False,True):
    for _ in range(6):
     crop_action(c,'plant',0,kind,100)
     if watered: crop_action(c,'water',0,kind,101)
     crop_action(c,'harvest',0,kind,2000)
  a.store.set('sanctuary_v4',p)
  self.assertEqual(len(garden_stamps(a.store)),len(garden_tasks()))
  self.assertEqual(len(garden_stamps(a.store)),36)
  self.assertTrue(reward_rows(a.store,'home')[3][2])
  self.assertFalse(reward_rows(a.store,'maze')[0][2])
  a.action('home_rewards'); a.action('equip_reward:3')
  self.assertEqual(equipped(a.store)[0],'Garden crown')
  a.action('completion_film'); self.assertEqual(a.screen,'completion_film'); a.draw()
  a.action('back'); self.assertEqual(a.screen,'reward_room')
 def test_locked_rewards_cannot_equip_or_play_and_full_maze_unlocks(self):
  a=self.a; a.action('maze_rewards'); a.action('equip_reward:5'); a.action('completion_film')
  self.assertEqual(a.screen,'reward_room'); self.assertEqual(equipped(a.store)[0],'Applin Trainer')
  book={f'{t}/{s}/{ab}/{int(co)}/{g}':{'clears':1,'seconds':10} for t,s,ab,co,g in combinations()}
  a.store.set('contract_book43',book); a.action('equip_reward:5')
  self.assertEqual(equipped(a.store)[0],'Master crown')
  self.assertEqual(garden_stamps(a.store),[])
  a.action('completion_film'); a.comfort=True; a.t=0; a.draw(); first=pygame.image.tostring(a.canvas,'RGB')
  a.t=5; a.draw(); self.assertEqual(first,pygame.image.tostring(a.canvas,'RGB'))
 def test_garden_collection_pagination_and_reward_return(self):
  a=self.a; a.action('garden_collection')
  for _ in range(16): a.draw(); a.action('garden_next')
  self.assertEqual(a.garden_page,0)
  a.action('home_rewards'); a.draw(); a.action('back'); self.assertEqual(a.screen,'garden_collection')

if __name__=='__main__': unittest.main()
