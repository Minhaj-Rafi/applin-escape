"""Optional biome interactions. Original maze corridors are never removed."""
import random
from model import DIRS, neighbors, distances, path_to

BIOME_RULES = (
    ('Falling fruit', 'Interact near a red fruit tree to drop a lure. Nearby birds investigate.'),
    ('Tidal crossing', 'The stone shortcut opens with the tide. Amber stones warn before it closes.'),
    ('Shrine bells', 'Interact near a bell to lure nearby birds away for six seconds.'),
    ('Turning ruins', 'Interact near the wheel to swap two shortcuts. Amber marks the next closing gate.'),
    ('Wind lanes', 'Interact on a wind arrow to ride three tiles. Quick Dash travels farther here.'),
)


class BiomeRules:
    def init_biome_rules(self, legacy=False):
        self.rules_version = 30 if legacy else 31
        self.lure_pos = None
        self.lure_time = self.lure_pending = 0.0
        self.terrain_cooldowns = {}
        self.biome_uses = 0
        self.ruin_pending = 0.0
        self.ruin_turn = 0
        self.ruin_request = False
        self.tide_label = 'CLOSED'
        self.interactables = []
        self.ruin_gates = []
        self.wind_lanes = []
        if legacy: return
        rng=random.Random(self.seed ^ 0xB1031)
        reserved=self.seeds|self.berries|self.rescues|{self.player,self.exit,self.switch}|{e.spawn for e in self.enemies}
        free=[p for p in self.floors if p not in reserved]
        rng.shuffle(free)
        if self.tier in (0,2):
            self.interactables=free[:3 if self.tier==0 else 2]
            self.dew-=set(self.interactables)
            self.initial_dew=len(self.dew)+self.dew_collected
        if self.tier==3 and self.bridge:
            first=self.bridge[0]
            candidates=[]
            for y in range(2,self.config.height-2):
                for x in range(2,self.config.width-2):
                    if self.grid[y][x] and (x,y)!=first and (not self.ledge or (x,y)!=self.ledge[0]):
                        if any((x-dx,y-dy) in self.floors and (x+dx,y+dy) in self.floors for dx,dy in ((1,0),(0,1))):
                            candidates.append((x,y))
            if candidates:
                second=min(candidates,key=lambda p:abs(p[0]-first[0])+abs(p[1]-first[1]))
                self.ruin_gates=[first,second]
                self.set_passage(first,True)
        if self.tier==4:
            used=set()
            for start in free:
                if start in used: continue
                for dx,dy in DIRS:
                    cells=[(start[0]+dx*i,start[1]+dy*i) for i in range(4)]
                    if all(p in self.floors and p not in reserved and p not in used for p in cells):
                        self.wind_lanes.append({'cells':cells,'direction':(dx,dy)})
                        used.update(cells)
                        break
                if len(self.wind_lanes)>=4: break
        if self.tier==1: self.update_biome_rules(0)
        # New open shortcuts can shorten spawn distances: retain the original safe-start margin.
        start_dist=distances(self.grid,[(1,1)])
        excluded=reserved|set(self.interactables)
        for enemy in self.enemies:
            if start_dist.get(enemy.pos,0)<16:
                choices=[p for p in self.floors if start_dist[p]>=16 and p not in excluded]
                if choices:
                    enemy.pos=enemy.spawn=rng.choice(choices)
                    excluded.add(enemy.pos)

    def set_passage(self, cell, opened):
        x,y=cell
        value=0 if opened else 1
        if self.grid[y][x]!=value:
            self.grid[y][x]=value
            self.board_revision+=1

    def occupied_cells(self):
        cells={self.player}|{e.pos for e in self.enemies}
        if self.coop: cells.add(self.partner['pos'])
        return cells

    def wind_at(self, pos):
        return next((lane for lane in self.wind_lanes if pos in lane['cells']),None)

    def biome_prompt(self):
        if self.rules_version<31: return 'Legacy v3.0 rules'
        if self.tier==1: return f'TIDE: {self.tide_label} / use the stone shortcut'
        if self.tier==3: return 'Turning wheel: interact to swap the two marked gates'
        if self.tier==4: return 'Wind arrow: interact to ride / longer Quick Dash'
        return 'Red fruit tree: interact to distract birds' if self.tier==0 else 'Brass bell: interact to lure nearby birds'

    def biome_interact(self):
        if self.rules_version<31: return False
        if self.tier in (0,2):
            targets=[p for p in self.interactables if abs(p[0]-self.player[0])+abs(p[1]-self.player[1])<=1]
            if targets:
                target=targets[0]; key=f'{target[0]},{target[1]}'
                if self.terrain_cooldowns.get(key,0)>0:
                    self.notify(f'Resting: {self.terrain_cooldowns[key]:.0f}s until you can use this again.')
                    return True
                self.terrain_cooldowns[key]=14.0
                self.lure_pos=target
                self.lure_pending=.8 if self.tier==0 else .1
                self.lure_time=0
                self.biome_uses+=1
                self.events.append(('fruit' if self.tier==0 else 'bell',target))
                self.notify('Fruit dropping! Nearby birds will investigate.' if self.tier==0 else 'Bell ringing! Nearby birds follow the sound.')
                return True
        if self.tier==3 and self.ruin_gates and abs(self.player[0]-self.switch[0])+abs(self.player[1]-self.switch[1])<=1:
            if self.ruin_request:
                self.notify('The gates are turning. Keep the amber tile clear.')
                return True
            self.ruin_request=True
            self.ruin_pending=1.5
            self.biome_uses+=1
            self.events.append(('turn',self.switch))
            self.notify('Turning gates in 1.5 seconds. Amber closes; teal opens.')
            return True
        if self.tier==4:
            lane=self.wind_at(self.player)
            if lane:
                key=f'wind{self.active_player}'
                if self.terrain_cooldowns.get(key,0)>0:
                    self.notify('The wind ride is recharging.')
                    return True
                self.terrain_cooldowns[key]=2.0
                self.biome_uses+=1
                self.direction=lane['direction']
                self.invulnerable=max(self.invulnerable,.7)
                for _ in range(3):
                    if not self.move(self.direction) or self.state!='playing': break
                self.events.append(('wind',self.player))
                self.events.append(('land',self.player))
                self.notify('Wind ride! A brief shield helps you land safely.')
                return True
        return False

    def update_biome_rules(self, dt):
        if self.rules_version<31: return
        self.terrain_cooldowns={k:max(0,v-dt) for k,v in self.terrain_cooldowns.items() if v>dt}
        if self.lure_pending>0:
            self.lure_pending=max(0,self.lure_pending-dt)
            if self.lure_pending==0: self.lure_time=6.0 if self.tier==2 else 5.0
        else:
            self.lure_time=max(0,self.lure_time-dt)
        occupied=self.occupied_cells()
        if self.tier==1 and self.bridge:
            phase=self.elapsed%16
            desired=phase<10
            cell=self.bridge[0]
            if not desired and cell in occupied:
                desired=True
                self.tide_label='WAITING FOR YOU'
            else:
                self.tide_label='OPEN' if phase<8 else 'CLOSING SOON' if phase<10 else 'CLOSED'
            self.bridge_open=desired
            self.bridge_time=max(0,10-phase) if desired else 16-phase
            self.set_passage(cell,desired)
        if self.tier==3 and self.ruin_request:
            self.ruin_pending=max(0,self.ruin_pending-dt)
            closing=self.ruin_gates[self.ruin_turn]
            if self.ruin_pending<=0 and closing not in occupied:
                self.set_passage(closing,False)
                self.ruin_turn=1-self.ruin_turn
                self.set_passage(self.ruin_gates[self.ruin_turn],True)
                self.ruin_request=False
                self.notify('The ruin gates have turned. A different shortcut is open.')

    def biome_enemy_target(self, enemy):
        if self.rules_version>=31 and self.lure_time>0 and self.lure_pos:
            route=path_to(self.grid,enemy.pos,self.lure_pos)
            if route and len(route)<=19:
                enemy.mood='lured'
                return self.lure_pos
        return None
