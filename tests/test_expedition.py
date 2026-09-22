import json
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import tempfile
import unittest
import pygame
from model import Store, neighbors, path_to, distances, TIERS
from expedition import Session, ABILITIES, SKILLS, parse_code
from main import App


class ExpeditionRules(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=Store(self.tmp.name)
    def tearDown(self):
        self.store.close(); self.tmp.cleanup()
    def game(self,**kw): return Session(self.store,**kw)
    def travel(self,g,target,partner=False):
        start=g.partner['pos'] if partner else g.player
        for p in path_to(g.grid,start,target)[1:]:
            pos=g.partner['pos'] if partner else g.player
            (g.move_partner if partner else g.move)((p[0]-pos[0],p[1]-pos[1]))

    def test_challenge_replays_objectives_and_keeps_history(self):
        g=self.game(tier=4,skill='Expert',ability='Camouflage',coop=True)
        count=self.store.summary()[0]
        h=self.game(code=g.code)
        self.assertEqual((h.grid,h.seeds,h.berries,h.rescues,h.ledge,h.switch,h.bridge),
                         (g.grid,g.seeds,g.berries,g.rescues,g.ledge,g.switch,g.bridge))
        self.assertEqual(h.code,g.code)
        self.assertEqual(self.store.summary()[0],count)
        for invalid in ('',g.code[:-1]+'!','BAD'+g.code[g.code.index('-'):]):
            with self.assertRaises(ValueError): parse_code(invalid)

    def test_save_restores_random_state_and_future_chase(self):
        g=self.game(tier=4,coop=True)
        g.invulnerable=100
        for _ in range(60): g.update(.05)
        data=json.loads(json.dumps(g.snapshot()))
        h=Session.restore(self.store,data)
        for _ in range(120):
            g.update(.05); h.update(.05)
        self.assertEqual(g.snapshot(),h.snapshot())

    def test_all_rulesets_reachable_and_start_safe(self):
        for tier in range(5):
            for skill in SKILLS:
                g=self.game(tier=tier,skill=skill)
                reachable=distances(g.grid,[g.player])
                self.assertTrue((g.seeds|g.rescues|g.berries|{g.exit,g.switch}) <= reachable.keys())
                self.assertTrue(all(reachable[e.pos]>=16 for e in g.enemies))
                self.assertEqual(g.initial_dew,len(g.dew))
                self.assertTrue(g.hidden_cells)

    def test_abilities_charge_cooldown_and_wall_boundaries(self):
        for ability in ABILITIES:
            g=self.game(ability=ability)
            g.direction=next((p[0]-1,p[1]-1) for p in neighbors(g.grid,g.player))
            before=g.escapes
            self.assertTrue(g.escape(),ability)
            self.assertEqual(g.escapes,before-1)
            self.assertFalse(g.escape())
            self.assertEqual(g.grid[g.player[1]][g.player[0]],0)
            if ability=='Quick Dash': self.assertLessEqual(g.steps,4)
            if ability=='Camouflage':
                g.invulnerable=0; g.enemies[0].pos=g.player
                self.assertFalse(g.collision())
            if ability=='Decoy Apple': self.assertEqual(g.decoy_time,7)

    def test_blocked_dash_preserves_charge_and_winning_dash_is_accounted(self):
        g=self.game(ability='Quick Dash')
        g.direction=(-1,0)
        self.assertFalse(g.escape())
        self.assertEqual(g.escapes_used,0)
        p=next(neighbors(g.grid,g.exit))
        g.player=p; g.direction=(g.exit[0]-p[0],g.exit[1]-p[1]); g.seeds.clear()
        g.escape()
        self.assertEqual(g.state,'cleared')
        self.assertEqual(self.store.records()[0][4],1)

    def test_bridge_closes_only_after_everyone_leaves(self):
        g=self.game(coop=True)
        g.player=g.switch; g.collect()
        self.assertTrue(g.bridge_open)
        bridge=g.bridge[0]
        g.player=bridge; g.invulnerable=100; g.bridge_time=.01
        g.update(.05)
        self.assertTrue(g.bridge_open)
        g.player=(1,1); g.partner['pos']=bridge
        g.update(.05)
        self.assertTrue(g.bridge_open)
        g.partner['pos']=(1,1)
        for e in g.enemies: e.pos=e.spawn; e.timer=100
        g.update(.05)
        self.assertFalse(g.bridge_open)
        self.assertEqual(g.grid[bridge[1]][bridge[0]],1)
        self.assertIn(g.exit,distances(g.grid,[g.player]))

    def test_ledge_is_one_way_and_partner_collects_on_landing(self):
        g=self.game(coop=True,seed_source=lambda: 20260921)
        # Isolate the ledge from nearby biome interactions and enemy collisions.
        g.interactables=[]; g.enemies=[]
        _,a,b=g.ledge
        g.player=b
        self.assertFalse(g.interact())
        g.partner['pos']=a
        g.berries.add(b)
        self.assertTrue(g.interact(partner=True))
        self.assertEqual(g.partner['pos'],b)
        self.assertNotIn(b,g.berries)
        self.assertEqual(g.slow_time,6)
        self.assertEqual(g.player,b)

    def test_partner_ability_does_not_teleport_primary(self):
        for ability in ABILITIES:
            g=self.game(coop=True,ability=ability)
            g.partner['direction']=next((p[0]-1,p[1]-1) for p in neighbors(g.grid,(1,1)))
            old=g.player
            self.assertTrue(g.escape_partner())
            self.assertEqual(g.player,old)
            self.assertEqual(g.active_player,0)
            self.assertEqual(g.escapes_used,1)

    def test_coop_victory_requires_both_and_records_one_result(self):
        g=self.game(coop=True)
        g.invulnerable=g.partner['invulnerable']=999
        for target in sorted(g.seeds): self.travel(g,target)
        self.travel(g,g.exit)
        self.assertEqual(g.state,'playing')
        self.travel(g,g.exit,partner=True)
        self.assertEqual(g.state,'cleared')
        self.assertEqual(len(self.store.records()),1)
        self.assertIn('Better together',self.store.get('achievements',[]))

    def test_downed_partner_rescue_and_recovery(self):
        g=self.game(coop=True)
        g.partner.update(pos=g.player,down=True,revive=8)
        g.collect()
        self.assertFalse(g.partner['down'])
        g.partner.update(pos=g.exit,down=True,revive=.01)
        g.update(.05)
        self.assertFalse(g.partner['down'])
        self.assertEqual(g.partner['pos'],(1,1))

    def test_swoop_warns_then_follows_legal_committed_path(self):
        g=self.game(tier=4)
        e=g.enemies[0]
        route=path_to(g.grid,g.player,e.pos)
        e.pos=route[min(4,len(route)-1)]
        e.timer=e.attack_cd=0
        g.elapsed=10; g.invulnerable=100
        g.update(.01)
        self.assertGreater(e.warning,0)
        origin=e.pos; committed=e.attack[:]
        g.player=g.exit
        g.update(.3)
        self.assertEqual(e.pos,origin)
        for _ in range(80):
            previous=[bird.pos for bird in g.enemies]
            g.update(.025)
            for bird,old in zip(g.enemies,previous):
                self.assertTrue(bird.pos==old or bird.pos in neighbors(g.grid,old))
        self.assertTrue(committed)

    def test_tutorial_teaches_actions_without_health_loss(self):
        g=self.game(mode='tutorial')
        g.enemies[0].pos=g.player; g.invulnerable=0
        self.assertFalse(g.collision())
        self.travel(g,next(iter(g.hidden_cells)))
        g.update(.05)
        g.escape(); g.update(.05)
        for target in sorted(g.seeds): self.travel(g,target); g.update(.05)
        self.travel(g,g.exit)
        self.assertEqual(g.state,'cleared')
        self.assertTrue(self.store.get('tutorial_complete',False))
        self.assertEqual(self.store.get('achievements',[]),[])

    def test_rescue_rewards_and_records_are_separated(self):
        for skill in ('Relaxed','Expert'):
            g=self.game(skill=skill)
            g.invulnerable=999
            for target in sorted(g.rescues)+sorted(g.seeds)+[g.exit]: self.travel(g,target)
            self.assertEqual(g.state,'cleared')
        self.assertIn('Rescue ranger',self.store.get('achievements',[]))
        self.assertEqual(len(self.store.get('personal_bests',{})),2)


class ExpeditionInterface(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.app=App(self.tmp.name)
    def tearDown(self): self.app.close(); self.tmp.cleanup()

    def test_new_screens_and_every_biome_coop_render(self):
        a=self.app
        for screen in ('adventure','challenge','journal','settings'):
            a.screen=screen; a.draw(); self.assertTrue(a.buttons)
        a.coop=True
        for tier in range(5):
            a.start(tier)
            self.assertEqual(a.screen,'play',a.error)
            a.game.enemies[0].direction=(0,1)
            a.game.enemies[0].warning=.7
            a.game.enemies[0].attack=[a.game.enemies[0].pos]
            a.draw(); a.update(.05); a.draw()
            self.assertTrue(a.overview)

    def test_save_menu_continue_restores_position_and_rules(self):
        a=self.app; a.coop=True; a.ability='Camouflage'; a.start(3)
        a.game.escape(); a.update(.05)
        snapshot=a.game.snapshot()
        a.action('save_menu'); self.assertIsNone(a.game)
        a.action('continue')
        self.assertEqual(a.game.snapshot(),snapshot)
        self.assertEqual(a.screen,'play')

    def test_saved_campaign_result_can_continue_next_biome(self):
        a=self.app; a.action('campaign'); g=a.game
        g.seeds.clear(); g.player=g.exit; g.collect(); a.consume_events()
        a.action('menu'); a.action('continue')
        self.assertEqual(a.screen,'result')
        self.assertEqual(len(a.campaign_results),1)
        a.action('next')
        self.assertEqual(a.game.tier,1)

    def test_particles_disabled_preserves_character_animation(self):
        a=self.app; a.start(); a.action('particles')
        a.game.events.append(('seed',a.game.player)); a.consume_events()
        self.assertTrue(a.characters); self.assertFalse(a.particles)

    def test_keyboard_players_move_independently(self):
        a=self.app; a.coop=True; a.start(); a.move_timer=a.partner_timer=0
        g=a.game; p=next(neighbors(g.grid,g.player)); direction=(p[0]-1,p[1]-1)
        key={(1,0):pygame.K_RIGHT,(0,1):pygame.K_DOWN}[direction]
        pygame.event.clear(); pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=key))
        a.events()
        self.assertEqual(g.player,(1,1)); self.assertEqual(g.partner['pos'],p)

    def test_challenge_entry_works_and_does_not_toggle_hotkeys(self):
        a=self.app; a.start(); code=a.game.code; a.action('pause'); a.action('copy_code')
        a.challenge_input=code
        pygame.event.clear(); pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN,unicode='\r',mod=0))
        a.events()
        self.assertEqual(a.game.mode,'challenge'); self.assertEqual(a.game.code,code)

    def test_audio_adapts_and_music_off_silences_layer(self):
        a=self.app; a.start(4)
        self.assertEqual(len(a.audio.danger_layers),5)
        a.audio.set_danger(True)
        self.assertTrue(a.audio.danger_channel.get_busy())
        a.action('music')
        self.assertEqual(a.audio.danger_channel.get_volume(),0)
        a.audio.set_danger(False)


if __name__=='__main__': unittest.main()
