"""Independent permanent stamps and cosmetic rewards for maze and garden play."""
from garden_timers import BERRIES
from home_progress import home_progress
from challenge_hall import TOTAL

MAZE_REWARDS=((1,'Copper trail'),(10,'Silver trail'),(50,'Gold trail'),(120,'Sapphire trail'),(240,'Star trail'),(TOTAL,'Master crown'))
HOME_REWARDS=((1,'Seed ribbon'),(12,'Flower ribbon'),(24,'Orchard ribbon'),(36,'Garden crown'),(54,'Home companion'),(72,'Sanctuary guardian'))
COLORS=((188,130,89),(194,211,216),(247,201,91),(106,170,239),(196,155,231),(250,223,136))


def garden_tasks():
    return [(name,method,target) for name,_,_ in BERRIES for method in ('Any harvest','Watered','Natural') for target in (1,3,6)]


def garden_stamps(store):
    care=home_progress(store).get('care',{}); counts=care.get('harvest_methods44',{})
    return [f'{name}/{method}/{target}' for name,method,target in garden_tasks() if counts.get(name,{}).get(method,0)>=target]


def reward_rows(store,domain):
    count=len(store.get('contract_book43',{})) if domain=='maze' else sum(t['current']>=t['target'] for t in sanctuary_tasks(store)[:72])
    table=MAZE_REWARDS if domain=='maze' else HOME_REWARDS
    return [(n,title,count>=n) for n,title in table]


def equipped(store):
    domain,title=store.get('reward_frame44',['maze',''])
    rows=reward_rows(store,domain)
    for i,(_,label,earned) in enumerate(rows):
        if label==title and earned: return label,COLORS[i]
    return 'Applin Trainer',(177,225,153)


def record_interaction(care,day=None):
    """Once per local calendar date; a gap never removes earned best-streak credit."""
    from datetime import date
    day=date.today() if day is None else day
    visits=care.setdefault('visits45',{'last':'','streak':0,'best':0,'days':0})
    if visits['last'] and day.isoformat()<=visits['last']: return
    consecutive=bool(visits['last']) and (day-date.fromisoformat(visits['last'])).days==1
    visits['streak']=visits['streak']+1 if consecutive else 1
    visits['best']=max(visits['best'],visits['streak'])
    visits['days']+=1; visits['last']=day.isoformat()


def sanctuary_tasks(store):
    progress=home_progress(store); care=progress.get('care',{})
    tasks=[]
    for name,method,target in garden_tasks():
        tasks.append(dict(title=f'Garden / {name} / {method}',detail='Harvests; Natural means no watering.',target=target,
            current=care.get('harvest_methods44',{}).get(name,{}).get(method,0)))
    friends=care.get('friends',{}); visits=care.get('visits45',{})
    metrics=(
      ('Rescue / Budew brought home','Rescue Budew and reach the shrine.',progress['rescued'],(1,5,15,30)),
      ('Friendship / Residents greeted','Talk to different rescued residents.',len(care.get('chatted',[])),(1,3,5,10)),
      ('Friendship / Happy residents','Reach three hearts with different residents.',sum(v>=3 for v in friends.values()),(1,3,5,10)),
      ('Restoration / Biomes restored','Clear different biomes to restore their gardens.',len(progress['restored']),(1,2,3,5)),
      ('Visits / Interaction days','Plant, water, harvest or talk on different local dates.',visits.get('days',0),(1,3,7,14)),
      ('Visits / Best daily streak','Interact on consecutive local dates; best streak stays saved.',visits.get('best',0),(3,5,7,14)),
      ('Care / Berries shared','Give garden berries to residents who need friendship.',care.get('feeds45',0),(1,5,10,20)),
      ('Collection / Berry varieties','Harvest different berry varieties.',len(care.get('grown_types',[])),(1,2,3,4)),
      ('Together / Rescue and care','Each set: one rescued Budew, one harvest and one friendship heart.',min(progress['rescued'],care.get('harvests',0),sum(friends.values())),(1,3,5,10)),
    )
    for title,detail,current,targets in metrics:
        for target in targets: tasks.append(dict(title=title,detail=detail,current=current,target=target))
    from home_mastery46 import advanced_tasks
    tasks.extend(advanced_tasks(progress))
    for i,task in enumerate(tasks): task['id']=str(i)
    return tasks
