"""Expedition rules for v3.0. Original base rules remain in model.py."""
from dataclasses import replace
from biome_rules import BiomeRules
import hashlib
import random
import secrets
from home_progress import roll_shiny, credit_home
from challenge_hall import GOALS,credit_contract
from model import Session as BaseSession, Enemy, TIERS, DIRS, distances, neighbors, path_to

ABILITIES = ('Leaf Slip', 'Quick Dash', 'Decoy Apple', 'Camouflage')
SKILLS = ('Relaxed', 'Standard', 'Expert')
COSMETICS = ('Orchard', 'Golden', 'Moonleaf', 'Blossom')
TUTORIAL = (
    'Move 6 steps with your movement keys or left stick. The map stays still.',
    'Walk into tall grass. Its leaves help hide you from distant birds.',
    'Stand beside a fruit branch and press Interact to distract a bird.',
    'Try your escape ability (see the HUD). Practice charges refill here.',
    'Collect a gold sun seed. Follow the gold diamond on the map.',
    'Collect the remaining seeds, then enter the glowing shrine.',
)


def encode(value):
    if isinstance(value, tuple): return {'tuple': [encode(v) for v in value]}
    if isinstance(value, set): return {'set': [encode(v) for v in sorted(value)]}
    if isinstance(value, list): return [encode(v) for v in value]
    if isinstance(value, dict): return {k: encode(v) for k, v in value.items()}
    return value


def decode(value):
    if isinstance(value, list): return [decode(v) for v in value]
    if isinstance(value, dict):
        if set(value) == {'tuple'}: return tuple(decode(v) for v in value['tuple'])
        if set(value) == {'set'}: return set(decode(v) for v in value['set'])
        return {k: decode(v) for k, v in value.items()}
    return value


def challenge_code(tier, seed, skill, ability, coop, legacy=False, rules=42):
    body = f'{"AE3" if legacy else "AE31" if rules==31 else "AE42"}-{tier+1}-{seed:016X}-{SKILLS.index(skill)}{ABILITIES.index(ability)}{int(coop)}'
    return body + '-' + hashlib.sha256(body.encode()).hexdigest()[:6].upper()


def parse_code(code):
    code=code.strip().upper()
    if code.startswith('AC1-'):
        wrapper=code.split('-',2)
        if len(wrapper)!=3 or wrapper[1] not in tuple(str(i) for i in range(len(GOALS))): raise ValueError('Invalid contract code.')
        code=wrapper[2]
    parts = code.split('-')
    try:
        prefix, tier, seed, options, checksum = parts
        body = '-'.join(parts[:-1])
        if prefix not in ('AE3','AE31','AE42') or len(seed) != 16 or len(options) != 3: raise ValueError
        if hashlib.sha256(body.encode()).hexdigest()[:6].upper() != checksum: raise ValueError
        tier, seed = int(tier)-1, int(seed, 16)
        if tier not in range(5) or options[2] not in '01': raise ValueError
        return tier, seed, SKILLS[int(options[0])], ABILITIES[int(options[1])], options[2] == '1'
    except (ValueError, IndexError):
        raise ValueError('Invalid challenge code. Paste the complete AE42, AE31 or legacy AE3 code.') from None


class ReplayStore:
    """A deliberate replay does not consume or erase normal map history."""
    def claim(self, layout, seed, tier):
        return hashlib.sha256(layout.encode()).hexdigest()


class Session(BiomeRules, BaseSession):
    def __init__(self, store, tier=0, mode='practice', seed_source=None,
                 skill='Standard', ability='Leaf Slip', coop=False, code=None, shiny_state=None, contract=None):
        replay_seed = None
        if code and code.strip().upper().startswith('AC1-'):
            parse_code(code)
            _,goal,code=code.strip().upper().split('-',2); contract=GOALS[int(goal)]
        self.contract=contract if contract in GOALS else None
        if code:
            tier, replay_seed, skill, ability, coop = parse_code(code)
            mode = 'challenge'
        super().__init__(ReplayStore() if code else store, tier, mode,
                         (lambda: replay_seed) if code else seed_source)
        self.store = store
        self.skill, self.ability, self.coop = skill, ability, coop
        self.code = challenge_code(tier, self.seed, skill, ability, coop, legacy=bool(code and code.strip().upper().startswith('AE3-')),rules=31 if code and code.strip().upper().startswith('AE31-') else 42)
        if self.contract: self.code=f'AC1-{GOALS.index(self.contract)}-'+self.code
        self.shiny = list(shiny_state) if shiny_state is not None else roll_shiny(coop)
        if not coop: self.shiny[1]=False
        self.stage_id=secrets.token_hex(16)
        self.story_run=False
        self.active_player = 0
        self.camouflage = 0.0
        self.finale = False
        self.finale_warning = 0.0
        self.tutorial_step = 0
        self.rescued = 0
        self.exit_wait = False
        self.board_revision = 0
        self.bridge_time = 0.0
        self.bridge_open = False
        self.config = replace(self.config, hearts=self.config.hearts + (1 if skill == 'Relaxed' else 0))
        self.health = self.config.hearts
        if skill == 'Relaxed': self.escapes += 2
        factor = {'Relaxed': 1.30, 'Standard': .95, 'Expert': .77}[skill]
        for enemy in self.enemies:
            enemy.delay *= factor
            enemy.warning = 0.0
            enemy.attack = []
            enemy.attack_cd = 2.0
            enemy.recovery = 0.0
        self.partner = {'pos': (1, 1), 'direction': (1, 0), 'invulnerable': 2.2,
                        'camouflage': 0.0, 'down': False, 'revive': 0.0, 'steps': 0}
        reserved = self.seeds | self.berries | {self.player, self.exit} | {e.pos for e in self.enemies}
        start_dist = distances(self.grid, [self.player])
        free = [p for p in self.floors if p not in reserved and start_dist[p] > 5]
        self.rng.shuffle(free)
        self.rescues = set(free[:2])
        self.switch = free[2]
        self.dew -= self.rescues | {self.switch}
        self.initial_dew = len(self.dew)
        # Optional crossings only: closing them cannot disconnect the original maze.
        crossings = []
        for y in range(2, self.config.height-2):
            for x in range(2, self.config.width-2):
                if self.grid[y][x]:
                    for dx, dy in ((1, 0), (0, 1)):
                        a, b = (x-dx, y-dy), (x+dx, y+dy)
                        if a in self.floors and b in self.floors:
                            crossings.append(((x, y), a, b))
        self.rng.shuffle(crossings)
        self.bridge = crossings[0] if crossings else None
        self.ledge = next((c for c in crossings[1:] if c[0] != self.bridge[0]), None) if self.bridge else None
        self.init_biome_rules(legacy=bool(code and code.strip().upper().startswith('AE3-')))
        if not code or code.strip().upper().startswith('AE42-'): self.rules_version=42
        from team_beacons50 import initialize
        initialize(self)
        self.berries_collected=0
        self.previous_best={}
        self.tutorial_seen_grass = False
        self.tutorial_seed = False
        if mode == 'tutorial':
            self.escapes = 99
            self.notify(TUTORIAL[0])
        seen = set(store.get('seen_species', [])) | {e.species for e in self.enemies}
        store.set('seen_species', sorted(seen))
        biomes = set(store.get('seen_biomes', [])) | {tier}
        store.set('seen_biomes', sorted(biomes))

    def snapshot(self):
        attrs = {k: v for k, v in vars(self).items() if k not in ('store', 'rng', 'config', 'enemies', 'events')}
        return {'version': 3, 'attrs': encode(attrs), 'rng': encode(self.rng.getstate()),
                'enemies': [encode(vars(e)) for e in self.enemies]}

    @classmethod
    def restore(cls, store, data):
        if not isinstance(data, dict) or data.get('version') != 3:
            raise ValueError('This saved expedition is not compatible with v3.0.')
        obj = cls.__new__(cls)
        obj.__dict__.update(decode(data['attrs']))
        obj.store = store
        obj.config = replace(TIERS[obj.tier], hearts=TIERS[obj.tier].hearts + (obj.skill == 'Relaxed'))
        obj.rng = random.Random()
        obj.rng.setstate(decode(data['rng']))
        obj.enemies = []
        for raw in data['enemies']:
            fields = decode(raw)
            enemy = Enemy(**{k: fields[k] for k in Enemy.__dataclass_fields__})
            enemy.__dict__.update(fields)
            obj.enemies.append(enemy)
        obj.events = []
        if not hasattr(obj,'rules_version'): obj.init_biome_rules(legacy=True)
        if not hasattr(obj,'shiny'): obj.shiny=[False,False]
        if not hasattr(obj,'stage_id'): obj.stage_id=secrets.token_hex(16)
        if not hasattr(obj,'story_run'): obj.story_run=False
        if not hasattr(obj,'berries_collected'): obj.berries_collected=0
        if not hasattr(obj,'previous_best'): obj.previous_best={}
        if not hasattr(obj,'contract'): obj.contract=None
        if not hasattr(obj,'team_beacons'):
            obj.team_beacons=[];obj.team_hold=0.0;obj.team_complete=False;obj.team_stamp_new=False
        for enemy in obj.enemies:
            if not hasattr(enemy,'recovery'): enemy.recovery=0.0
        return obj

    def finish(self, outcome):
        if self.recorded: return
        original_mode = self.mode
        # Keep different rules in separate record categories.
        self.mode = f'{original_mode}/{self.skill}/{"duo" if self.coop else "solo"}/{self.ability}'
        super().finish(outcome)
        self.mode = original_mode
        credit_home(self)
        credit_contract(self)
        from team_beacons50 import credit
        self.team_stamp_new=credit(self)
        self.store.set('active_expedition', None)
        if outcome == 'cleared' and original_mode != 'tutorial':
            key = f'{self.tier}/{self.skill}/{self.coop}/{self.ability}/{original_mode}/v{self.rules_version}'
            if self.contract: key += '/contract/'+self.contract
            if original_mode == 'challenge': key += '/' + self.code
            records = self.store.get('personal_bests', {})
            old = records.get(key, {})
            self.previous_best=dict(old)
            records[key] = {'seconds': min(self.elapsed, old.get('seconds', 1e20)),
                            'steps': min(self.steps, old.get('steps', 10**12)),
                            'no_hit': bool(old.get('no_hit', False) or self.hits == 0)}
            self.store.set('personal_bests', records)
            achievements = set(self.store.get('achievements', [])) | {'First sanctuary'}
            if self.hits == 0: achievements.add('Untouched')
            if self.rescued == 2: achievements.add('Rescue ranger')
            if self.tier == 4: achievements.add('Highland hero')
            if self.coop: achievements.add('Better together')
            if self.escapes_used == 0: achievements.add('On foot')
            self.store.set('achievements', sorted(achievements))
        if outcome == 'cleared' and original_mode == 'tutorial':
            self.store.set('tutorial_complete', True)

    def collect(self):
        had_seed = self.player in self.seeds
        if self.player in self.berries: self.berries_collected=getattr(self,'berries_collected',0)+1
        if self.player in self.rescues:
            self.rescues.remove(self.player)
            self.rescued += 1
            self.score += 350
            self.events.append(('rescue', self.player))
            self.notify('Budew: Thank you! I will meet you at home. Rescue +350.')
        if self.player == self.switch and self.bridge and not self.bridge_open and not (self.rules_version>=31 and self.tier in (1,3)):
            x, y = self.bridge[0]
            self.grid[y][x] = 0
            self.bridge_open, self.bridge_time = True, 12.0
            self.board_revision += 1
            self.notify('Bridge switch! The turquoise shortcut lasts 12 seconds.')
        if self.coop and self.active_player == 0 and self.partner['down']:
            if sum(abs(a-b) for a, b in zip(self.player, self.partner['pos'])) <= 1:
                self.partner.update(down=False, invulnerable=3.0, revive=0.0)
                self.events.append(('rescue', self.partner['pos']))
                self.notify('Partner rescued! Keep exploring together.')
        # Both apples must arrive at the shrine in co-op.
        if self.coop and self.player == self.exit and not self.seeds:
            other = self.partner['pos']
            if other != self.exit or self.partner['down']:
                self.exit_wait = True
                self.notify('The shrine is ready. Bring both apples here!')
                return
        super().collect()
        if had_seed:
            self.tutorial_seed = True
            if not self.seeds and not self.finale:
                self.finale, self.finale_warning = True, 3.0
                self.events.append(('warning', self.exit))
                self.notify('Final flight in 3 seconds! Reach the glowing shrine.')
        if self.player in self.hidden_cells: self.tutorial_seen_grass = True

    def partner_action(self, callback):
        if not self.coop or self.partner['down'] or self.state != 'playing': return False
        old = (self.player, self.direction, self.invulnerable, self.camouflage)
        self.player, self.direction = self.partner['pos'], self.partner['direction']
        self.invulnerable, self.camouflage = self.partner['invulnerable'], self.partner['camouflage']
        self.partner['pos'] = old[0]
        before = self.steps
        self.active_player = 1
        try:
            return callback()
        finally:
            self.partner['pos'], self.partner['direction'] = self.player, self.direction
            self.partner['invulnerable'], self.partner['camouflage'] = self.invulnerable, self.camouflage
            self.partner['steps'] += self.steps-before
            self.player, self.direction, self.invulnerable, self.camouflage = old
            self.active_player = 0

    def move_partner(self, direction):
        return self.partner_action(lambda: self.move(direction))

    def collision(self):
        if self.mode == 'tutorial' or self.camouflage > 0: return False
        if self.active_player == 1:
            if self.invulnerable > 0 or self.state != 'playing': return False
            if any(e.pos == self.player and e.stunned <= 0 for e in self.enemies):
                self.partner['down'] = True
                self.partner['revive'] = 8.0
                self.hits += 1
                self.events.append(('hit', self.player))
                self.notify('Partner needs help! Touch them, or wait 8 seconds for recovery.')
                return True
            return False
        if self.invulnerable<=0 and self.state=='playing':
            attacker=next((e for e in self.enemies if e.pos==self.player and e.stunned<=0),None)
            if attacker:
                self.last_capture47=attacker.species+(' caught you during its warned swoop.' if attacker.mood=='swoop' else ' reached your tile while pursuing.')
        hit=super().collision()
        if hit and self.rules_version>=31:
            for enemy in self.enemies:
                enemy.warning=0.0
                enemy.attack=[]
                enemy.recovery=0.0
                enemy.attack_cd=2.0
        return hit

    def interact(self, partner=False):
        if partner: return self.partner_action(self.interact)
        if self.state != 'playing': return False
        if self.biome_interact(): return True
        if self.ledge and self.player == self.ledge[1]:
            self.player = self.ledge[2]
            self.steps += 2
            self.visited.add(self.player)
            if not self.collision(): self.collect()
            self.events.append(('land', self.player))
            return True
        self.notify('Tidal stones change automatically; wait for a clear crossing.' if self.tier==1 else 'Move beside a fruit branch, bell or wheel, or stand on a wind feather. Click a landmark for details.')
        return False

    def escape(self):
        if self.ability == 'Leaf Slip': return super().escape()
        if self.state != 'playing' or self.escapes <= 0 or self.escape_cooldown > 0:
            self.notify('No charge available, or ability is cooling down.')
            return False
        old = self.player
        if self.ability == 'Quick Dash':
            route = [old]
            lane=self.wind_at(self.player) if self.rules_version>=31 else None
            for _ in range(6 if lane and lane['direction']==self.direction else 4):
                nxt = tuple(a+b for a,b in zip(route[-1], self.direction))
                if nxt not in neighbors(self.grid, route[-1]): break
                route.append(nxt)
            if len(route) == 1:
                self.notify('Face an open corridor to dash. Charge preserved.')
                return False
            self.escapes -= 1
            self.escapes_used += 1
            self.invulnerable = max(self.invulnerable, .9)
            for p in route[1:]:
                self.player = p
                self.steps += 1
                self.visited.add(p)
                self.collect()
                if self.state != 'playing': break
        elif self.ability == 'Decoy Apple':
            self.decoy, self.decoy_time = old, 7.0
            self.invulnerable = max(self.invulnerable, 1.0)
        else:
            self.camouflage = 5.0
            self.invulnerable = max(self.invulnerable, 1.0)
        if self.ability != 'Quick Dash':
            self.escapes -= 1
            self.escapes_used += 1
        self.escape_cooldown = 1.5
        self.events.extend([('escape', old), ('land', self.player)])
        self.notify(f'{self.ability}! {self.escapes} charges remain.')
        return True

    def escape_partner(self):
        return self.partner_action(self.escape)

    def enemy_target(self, enemy, player_dist):
        lure=self.biome_enemy_target(enemy)
        if lure is not None and self.decoy_time<=0: return lure
        if self.camouflage > 0 and self.decoy_time <= 0:
            enemy.mood = 'search'
            if enemy.pos == enemy.target: enemy.target = self.rng.choice(self.floors)
            return enemy.target
        target = super().enemy_target(enemy, player_dist)
        if self.finale and self.finale_warning <= 0 and self.decoy_time <= 0:
            enemy.mood = 'chase'
            target = self.player
        if self.coop and not self.partner['down'] and self.partner['camouflage'] <= 0 and self.decoy_time <= 0:
            other = self.partner['pos']
            route = path_to(self.grid, enemy.pos, other)
            if route and len(route) <= self.config.detection and len(route)-1 < player_dist.get(enemy.pos, 999):
                enemy.mood = 'chase'
                target = other
        if self.rules_version>=42 and self.tier>=2 and self.skill!='Relaxed' and enemy.mood=='chase' and self.decoy_time<=0:
            index=self.enemies.index(enemy)
            # One interceptor at tier 3, two at tiers 4/5; the rest keep their species roles.
            if 1 <= index <= (1 if self.tier==2 else 2):
                ahead=self.player
                for _ in range(2+self.tier):
                    nxt=(ahead[0]+self.direction[0],ahead[1]+self.direction[1])
                    if nxt not in neighbors(self.grid,ahead): break
                    ahead=nxt
                    if len(list(neighbors(self.grid,ahead)))>=3: break
                if ahead!=self.player: target=ahead
        return target

    def update(self, dt):
        if self.state != 'playing': return
        self.elapsed += dt
        self.update_biome_rules(dt)
        for attr in ('invulnerable', 'slow_time', 'escape_cooldown', 'decoy_time', 'notice_time', 'camouflage', 'finale_warning'):
            setattr(self, attr, max(0.0, getattr(self, attr)-dt))
        self.partner['invulnerable'] = max(0, self.partner['invulnerable']-dt)
        self.partner['camouflage'] = max(0, self.partner['camouflage']-dt)
        if self.partner['down']:
            self.partner['revive'] -= dt
            if self.partner['revive'] <= 0:
                self.partner.update(pos=(1,1), down=False, invulnerable=3.0)
        if self.bridge_open and not (self.rules_version>=31 and self.tier in (1,3)):
            self.bridge_time = max(0, self.bridge_time-dt)
            cell = self.bridge[0]
            occupied = {self.player, self.partner['pos']} | {e.pos for e in self.enemies}
            if self.bridge_time <= 0 and cell not in occupied:
                self.grid[cell[1]][cell[0]] = 1
                self.bridge_open = False
                self.board_revision += 1
        pd = distances(self.grid, [self.player])
        for enemy in self.enemies:
            enemy.stunned = max(0, enemy.stunned-dt)
            enemy.attack_cd = max(0, enemy.attack_cd-dt)
            enemy.recovery = max(0, enemy.recovery-dt)
            if enemy.recovery>0:
                enemy.mood='recover'
                continue
            if enemy.stunned > 0:
                enemy.attack = []
                enemy.warning = 0
                continue
            if enemy.warning > 0:
                enemy.warning = max(0, enemy.warning-dt)
                enemy.mood = 'warning'
                continue
            enemy.timer -= dt
            if enemy.timer > 0: continue
            target = self.enemy_target(enemy, pd)
            route = path_to(self.grid, enemy.pos, target)
            active_swoops=sum(bool(e.warning>0 or e.attack) for e in self.enemies if e is not enemy)
            limit=2 if self.skill=='Expert' else 1
            can_swoop=self.rules_version<31 or active_swoops<limit
            if can_swoop and enemy.mood == 'chase' and enemy.attack_cd <= 0 and 2 < len(route) <= 9 and not enemy.attack:
                # Fixed preview route; birds never retarget during the committed swoop.
                enemy.attack = route[1:4]
                enemy.warning = (.95 if self.skill == 'Relaxed' else .75) if self.rules_version<31 else {'Relaxed':1.15,'Standard':.95,'Expert':.8}[self.skill]+(.3 if self.tier==4 else 0)
                enemy.attack_cd = 4.0
                enemy.mood = 'warning'
                self.events.append(('warning', enemy.pos))
                continue
            diving = bool(enemy.attack)
            nxt = enemy.attack.pop(0) if diving else route[1] if len(route)>1 else enemy.pos
            delay = enemy.delay * (.72 if self.finale and self.finale_warning <= 0 else 1)
            enemy.timer = (.075 if diving else delay) * (2.2 if self.slow_time > 0 else 1)
            if diving: enemy.mood = 'swoop'
            occupied = {e.pos for e in self.enemies if e is not enemy}
            if nxt in neighbors(self.grid, enemy.pos) and nxt not in occupied:
                enemy.direction = (nxt[0]-enemy.pos[0], nxt[1]-enemy.pos[1])
                enemy.pos = nxt
            elif nxt != enemy.pos:
                if diving and self.rules_version>=31:
                    enemy.attack=[]; enemy.recovery=.35; enemy.mood='recover'
                    continue
                enemy.attack = []
                choices = [p for p in neighbors(self.grid, enemy.pos) if p not in occupied]
                if choices:
                    nxt = self.rng.choice(choices)
                    enemy.direction = (nxt[0]-enemy.pos[0], nxt[1]-enemy.pos[1])
                    enemy.pos = nxt
            if diving and not enemy.attack and self.rules_version>=31:
                enemy.recovery=.35
            if self.collision(): break
            if self.coop and not self.partner['down'] and self.partner['invulnerable'] <= 0 and self.partner['camouflage'] <= 0 and enemy.pos == self.partner['pos']:
                self.partner.update(down=True, revive=8.0)
                self.hits += 1
                self.events.append(('hit', self.partner['pos']))
                self.notify('Partner needs help! Touch them to rescue, or wait 8 seconds.')
        from team_beacons50 import update as update_team
        update_team(self,dt)
        if self.mode == 'tutorial':
            self.escapes = max(self.escapes, 9)
            checks = (self.steps >= 6, self.tutorial_seen_grass, self.biome_uses>0, self.escapes_used > 0, self.tutorial_seed)
            while self.tutorial_step < 5 and checks[self.tutorial_step]: self.tutorial_step += 1
            self.notice, self.notice_time = TUTORIAL[self.tutorial_step], 1.0
