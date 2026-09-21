"""Readable clearing accents, map validation and quiet sanctuary feedback."""
from model import distances

def clearings(game):
    grid=game.grid; candidates=[]
    for y in range(2,len(grid)-2):
        for x in range(2,len(grid[0])-2):
            if all(not grid[yy][xx] for yy in range(y-1,y+2) for xx in range(x-1,x+2)):
                candidates.append((x,y))
    candidates.sort(key=lambda p:((p[0]*73856093 ^ p[1]*19349663 ^ game.seed)%2147483647))
    selected=[]
    for point in candidates:
        if all(abs(point[0]-q[0])+abs(point[1]-q[1])>=6 for q in selected): selected.append(point)
        if len(selected)==4: break
    return selected

def map_report(game):
    grid=[r[:] for r in game.grid]
    if game.bridge: grid[game.bridge[0][1]][game.bridge[0][0]]=1
    for x,y in game.ruin_gates: grid[y][x]=1
    reach=distances(grid,[(1,1)])
    objectives=game.seeds|game.berries|game.rescues|{game.exit}
    return {'reachable':objectives<=reach.keys(),'clearings':len(clearings(game)),
            'spawn_distance':min(distances(game.grid,[(1,1)]).get(e.spawn,0) for e in game.enemies)}

def home_snapshot(store):
    from rewards44 import sanctuary_tasks
    from home_mastery46 import home_milestones
    from home_progress import home_progress,decorations
    p=home_progress(store)
    return ({t['id'] for t in sanctuary_tasks(store) if t['current']>=t['target']},
            {title for title,done,_ in home_milestones(p) if done},set(decorations(p)))

def home_feedback(before,after):
    stamps,goals,decor=(b-a for a,b in zip(before,after))
    parts=[]
    if stamps: parts.append(f'{len(stamps)} new achievement'+('s' if len(stamps)>1 else ''))
    if goals: parts.append('Milestone: '+sorted(goals)[0])
    if decor: parts.append('Decor unlocked: '+', '.join(sorted(decor)))
    return ' / '.join(parts)

TOUR=(
 ('Plant your first berries','Open Garden & residents, choose a variety, then plant an empty bed. Each variety has its own growing time. Crops grow while you are away and never spoil.'),
 ('Welcome rescued residents','Rescue Budew in a maze and reach the shrine. Find them in Resident album: talking and sharing garden berries builds friendship. Three hearts means a happy resident.'),
 ('Build something together','Projects ask for specific berry varieties and resident support. Gather everything, then choose Deliver berries. Only successful deliveries spend berries; projects never expire.'),
 ('Choose your next goal','Sanctuary achievements has category filters and an unfinished-only view. Select a goal to pin it in Sanctuary square. Home milestones show which decorations you can unlock.'),
)
