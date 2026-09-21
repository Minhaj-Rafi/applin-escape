"""Optional co-op objective. No change to maze topology, scores or escape charges."""
import random
from model import distances,neighbors

HOLD_SECONDS=1.5

def initialize(game):
    game.team_beacons=[];game.team_hold=0.0;game.team_complete=False;game.team_stamp_new=False
    if not game.coop or game.mode=='tutorial' or game.rules_version<42:return
    reserved=game.seeds|game.berries|game.rescues|set(game.interactables)|set(game.ruin_gates)|{game.player,game.exit,game.switch}
    reserved|={e.spawn for e in game.enemies}
    if game.bridge:reserved.add(game.bridge[0])
    if game.ledge:reserved.add(game.ledge[0])
    for lane in game.wind_lanes:reserved.update(lane['cells'])
    start=distances(game.grid,[(1,1)])
    free=sorted(p for p in game.floors if p not in reserved and start.get(p,0)>5 and len(list(neighbors(game.grid,p)))>=2)
    rng=random.Random(game.seed^0xBEAC0050);rng.shuffle(free)
    for first in free:
        away=distances(game.grid,[first]);second=next((p for p in free if 8<=away.get(p,0)<=22),None)
        if second:
            game.team_beacons=[first,second]
            # Keep existing collectibles and their score totals unchanged.
            return

def update(game,dt):
    if not getattr(game,'team_beacons',[]) or game.team_complete or game.state!='playing':return
    together=(not game.partner['down'] and game.player==game.team_beacons[0] and game.partner['pos']==game.team_beacons[1])
    game.team_hold=min(HOLD_SECONDS,game.team_hold+max(0,dt)) if together else 0.0
    if game.team_hold>=HOLD_SECONDS:
        game.team_complete=True
        game.notify('Both beacons lit! Reach the shrine together to earn this biome team stamp.')
        game.events.append(('seed',game.player))

def credit(game):
    if game.state!='cleared' or not game.coop or not getattr(game,'team_complete',False):return False
    book=game.store.get('team_beacons50',{})
    key=str(game.tier)
    if key in book:return False
    book[key]={'stage':game.stage_id,'seconds':game.elapsed}
    game.store.set('team_beacons50',book)
    return True
