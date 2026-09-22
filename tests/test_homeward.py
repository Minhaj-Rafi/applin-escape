import json
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import tempfile
import unittest
from unittest.mock import patch
import pygame
from model import Store, neighbors, path_to, distances
from expedition import Session, COSMETICS, decode, encode
from home_progress import roll_shiny, SHINY_ODDS, home_progress, decorations, credit_home
from biome_art import landmark
from main import App


class ShinyRules(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.store=Store(self.tmp.name)
    def tearDown(self): self.store.close(); self.tmp.cleanup()

    def test_independent_rolls_allow_neither_one_or_both(self):
        for rolls,expected in (([1,2],[False,False]),([0,1],[True,False]),([1,0],[False,True]),([0,0],[True,True])):
            with patch('home_progress.secrets.randbelow',side_effect=rolls) as rng:
                self.assertEqual(roll_shiny(True),expected)
                self.assertEqual(rng.call_count,2)
                self.assertEqual(rng.call_args.args,(SHINY_ODDS,))
        with patch('home_progress.secrets.randbelow',return_value=0) as rng:
            self.assertEqual(roll_shiny(False),[True,False]); self.assertEqual(rng.call_count,1)
        self.assertEqual(SHINY_ODDS,256)
        self.assertNotIn('Shiny',COSMETICS)

    def test_save_continue_never_rerolls_and_legacy_is_normal(self):
        with patch('home_progress.secrets.randbelow',side_effect=[0,0]): g=Session(self.store,coop=True)
        data=json.loads(json.dumps(g.snapshot()))
        with patch('home_progress.secrets.randbelow',side_effect=AssertionError('rerolled')):
            h=Session.restore(self.store,data)
        self.assertEqual(h.shiny,[True,True])
        attrs=decode(data['attrs']); attrs.pop('shiny'); data['attrs']=encode(attrs)
        with patch('home_progress.secrets.randbelow',side_effect=AssertionError('legacy rerolled')):
            h=Session.restore(self.store,data)
        self.assertEqual(h.shiny,[False,False])

    def test_challenge_code_cannot_copy_shiny_colour(self):
        with patch('home_progress.secrets.randbelow',return_value=0): g=Session(self.store)
        with patch('home_progress.secrets.randbelow',return_value=1): h=Session(self.store,code=g.code)
        self.assertEqual(g.grid,h.grid); self.assertEqual(g.code,h.code)
        self.assertTrue(g.shiny[0]); self.assertFalse(h.shiny[0])

    def test_sanctuary_credit_is_idempotent_and_requires_clear(self):
        g=Session(self.store); g.rescued=2
        credit_home(g); self.assertEqual(home_progress(self.store)['rescued'],0)
        g.story_run=True; g.finish('cleared')
        credit_home(g); g.finish('cleared')
        p=home_progress(self.store)
        self.assertEqual(p['rescued'],2); self.assertEqual(p['chapters'],[0]); self.assertEqual(p['restored'],[0])
        h=Session.restore(self.store,g.snapshot()); credit_home(h)
        self.assertEqual(home_progress(self.store)['rescued'],2)
        t=Session(self.store,mode='tutorial'); t.rescued=2; t.finish('cleared')
        self.assertEqual(home_progress(self.store)['rescued'],2)


class HomewardFlows(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.app=App(self.tmp.name)
    def tearDown(self): self.app.close(); self.tmp.cleanup()

    def press_interact(self,partner=False):
        key=self.app.controls.keys[int(partner)][5]
        pygame.event.clear(); pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=key)); self.app.events()

    def win(self):
        g=self.app.game; g.invulnerable=999; g.partner['invulnerable']=999
        for target in sorted(g.rescues)+sorted(g.seeds)+[g.exit]:
            for p in path_to(g.grid,g.player,target)[1:]: g.move((p[0]-g.player[0],p[1]-g.player[1]))
        if g.coop:
            for p in path_to(g.grid,g.partner['pos'],g.exit)[1:]: g.move_partner((p[0]-g.partner['pos'][0],p[1]-g.partner['pos'][1]))
        self.app.consume_events()
        self.assertEqual(g.state,'cleared')

    def test_complete_story_carries_shiny_and_restores_home(self):
        a=self.app; a.coop=True
        a.action('story'); self.assertEqual(a.screen,'story')
        with patch('home_progress.secrets.randbelow',side_effect=[0,1]): a.action('story_begin')
        for tier in range(5):
            self.assertEqual(a.game.tier,tier); self.assertEqual(a.game.shiny,[True,False])
            self.win(); a.draw()
            if tier<4:
                a.action('next'); self.assertEqual(a.screen,'story'); a.draw()
                with patch('home_progress.secrets.randbelow',side_effect=AssertionError('chapter reroll')):
                    a.action('story_begin')
        self.assertEqual(a.result_primary(),'sanctuary')
        a.action(a.result_primary()); a.draw()
        progress=home_progress(a.store)
        self.assertEqual(progress['restored'],list(range(5)))
        self.assertEqual(progress['chapters'],list(range(5)))
        self.assertEqual(progress['rescued'],10)
        self.assertIn('Fountain',decorations(progress))

    def test_plain_expedition_and_save_keep_run_colour_retry_rerolls(self):
        a=self.app
        with patch('home_progress.secrets.randbelow',return_value=0): a.action('campaign')
        self.win()
        with patch('home_progress.secrets.randbelow',side_effect=AssertionError('stage reroll')): a.action('next')
        self.assertEqual(a.game.shiny,[True,False])
        a.action('save_menu')
        with patch('home_progress.secrets.randbelow',side_effect=AssertionError('save reroll')): a.action('continue')
        self.assertEqual(a.game.shiny,[True,False])
        with patch('home_progress.secrets.randbelow',return_value=1): a.action('retry')
        self.assertEqual(a.game.shiny,[False,False])

    def test_story_resume_keeps_story_flow(self):
        a=self.app; a.action('story'); a.action('story_begin'); self.win()
        a.action('menu'); a.action('continue')
        self.assertTrue(a.story_mode); a.action('next'); self.assertEqual(a.screen,'story')

    def test_shiny_overrides_styles_and_partner_palette_only_for_run(self):
        a=self.app; a.coop=True; a.start()
        a.cosmetic='Blossom'; a.game.shiny=[True,True]
        one=a.hero_sprite(80,0,(1,0)); two=a.hero_sprite(80,0,(1,0),True)
        self.assertEqual(pygame.image.tostring(one,'RGBA'),pygame.image.tostring(two,'RGBA'))
        a.game.shiny=[False,False]
        regular=a.hero_sprite(80,0,(1,0))
        self.assertNotEqual(pygame.image.tostring(one,'RGBA'),pygame.image.tostring(regular,'RGBA'))
        self.assertNotIn('Shiny',a.unlocked_cosmetics())

    def test_fruit_and_bell_controls_really_change_enemy_movement(self):
        a=self.app
        for tier in (0,2):
            a.start(tier); g=a.game; target=g.interactables[0]; g.player=target; g.invulnerable=999
            e=g.enemies[0]
            choices=distances(g.grid,[target]); e.pos=next(p for p,d in choices.items() if d==7)
            e.timer=0; e.attack=[]; e.warning=0; e.stunned=0; e.recovery=0
            # Isolate lure flight from a randomly triggered swoop/recovery during its startup delay.
            e.attack_cd=99
            # Other birds can legitimately block a one-cell path; test one pursuer.
            g.enemies=[e]
            e.timer=.85 if tier==0 else .15
            self.press_interact()
            self.assertGreater(g.lure_pending,0)
            for _ in range(35): a.update(.05)
            self.assertEqual(e.mood,'lured')
            self.assertLess(distances(g.grid,[target])[e.pos],7)

    def test_ruin_wheel_key_swaps_passability_and_refreshes_graphics(self):
        a=self.app; a.start(3); g=a.game; g.player=g.switch; g.invulnerable=999
        old,new=g.ruin_gates
        for e in g.enemies: e.timer=999
        self.press_interact(); self.assertTrue(g.ruin_request)
        for _ in range(35): a.update(.05)
        self.assertEqual(g.grid[old[1]][old[0]],1); self.assertEqual(g.grid[new[1]][new[0]],0)
        self.assertEqual(a.render_revision,g.board_revision)
        a.draw()

    def test_tide_changes_in_app_loop_without_trapping_partner(self):
        a=self.app; a.coop=True; a.start(1); g=a.game
        g.invulnerable=g.partner['invulnerable']=999
        for e in g.enemies: e.timer=999
        g.elapsed=9.9; g.partner['pos']=g.bridge[0]
        for _ in range(10): a.update(.05)
        self.assertTrue(g.bridge_open)
        g.partner['pos']=(1,1); a.update(.05)
        self.assertFalse(g.bridge_open)
        self.assertEqual(a.render_revision,g.board_revision)
        a.draw()

    def test_wind_key_moves_player_three_cells_and_preserves_charge(self):
        a=self.app; a.start(4); g=a.game; lane=g.wind_lanes[0]
        g.player=lane['cells'][0]; charges=g.escapes
        self.press_interact()
        self.assertEqual(g.player,lane['cells'][3]); self.assertEqual(g.escapes,charges)
        self.assertGreater(g.invulnerable,0)

    def test_guide_and_home_navigation_and_rendering(self):
        a=self.app; a.start(); a.action('biome_guide'); self.assertEqual(a.screen,'biome_guide'); a.draw()
        a.action('back'); self.assertEqual(a.screen,'paused')
        a.action('save_menu'); a.action('sanctuary'); a.draw(); a.action('home_plot:0')
        self.assertIn('Bramblebrook',a.home_notice)
        a.action('back'); self.assertEqual(a.screen,'menu')
        for screen in ('biome_guide','story','sanctuary'):
            a.screen=screen; a.draw(); self.assertTrue(a.buttons)

    def test_landmarks_have_distinct_silhouettes_and_survive_every_palette(self):
        sprites=[landmark(kind,32) for kind in ('fruit','tide','bell','wheel','wind')]
        self.assertEqual(len({pygame.image.tostring(s,'RGBA') for s in sprites}),5)
        from world import BIOMES
        for s in sprites:
            self.assertGreater(pygame.mask.from_surface(s).count(),240)
            for biome in BIOMES:
                background=biome['path']
                contrast=sum(1 for x in range(32) for y in range(32) if s.get_at((x,y)).a>200 and max(abs(s.get_at((x,y))[i]-background[i]) for i in range(3))>65)
                self.assertGreater(contrast,100)


if __name__=='__main__': unittest.main()
