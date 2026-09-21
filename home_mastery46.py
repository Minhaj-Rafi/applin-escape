"""Optional sanctuary mastery and permanent community projects. No expiring tasks."""
from garden_timers import BERRIES,crop_stage

PROJECTS=(
 ('Welcome baskets',{'Oran':6,'Pecha':2},0,0),
 ('Pond picnic',{'Oran':4,'Cheri':6},3,1),
 ('Resident feast',{'Pecha':6,'Sitrus':4},5,2),
 ('Orchard exchange',{'Oran':6,'Pecha':6,'Cheri':6,'Sitrus':6},8,3),
 ('Lantern supper',{'Cheri':10,'Sitrus':8,'Pecha':6},12,5),
 ('Homecoming festival',{'Oran':12,'Pecha':12,'Cheri':12,'Sitrus':12},20,8),
)

def happy(care): return sum(v>=3 for v in care.get('friends',{}).values())

def deliver(progress,index):
    if not 0<=index<len(PROJECTS): return 'Choose a community project.'
    name,recipe,rescues,hearts=PROJECTS[index]; care=progress['care']; inv=care.get('berry_types',{})
    if progress['rescued']<rescues or happy(care)<hearts: return 'More rescued and happy residents are needed. See the project requirements.'
    if any(inv.get(k,0)<v for k,v in recipe.items()): return 'Not enough of each berry variety. Nothing was spent.'
    for k,v in recipe.items(): inv[k]-=v
    care['berries']=sum(inv.values())
    book=care.setdefault('projects46',{}); book[str(index)]=book.get(str(index),0)+1
    from rewards44 import record_interaction
    record_interaction(care)
    return name+' delivered! Community progress saved.'

def record_harvest(care,crops):
    ripe=[c for c in crops if c and crop_stage(c)==3]
    if len(ripe)==3 and len({c['kind'] for c in ripe})==3:
        care['mixed_beds46']=care.get('mixed_beds46',0)+1
    # Only the first harvest of a complete three-bed arrangement can count.

def advanced_tasks(progress):
    care=progress.get('care',{}); counts=care.get('harvest_methods44',{}); book=care.get('projects46',{})
    minimum=lambda method:min(counts.get(n,{}).get(method,0) for n,_,_ in BERRIES)
    rescue=progress.get('rescue_mastery46',{})
    metrics=(
      ('Balanced orchard','Harvest EACH of the four varieties this many times.',minimum('Any harvest'),(12,24)),
      ('Watering specialist','Harvest EACH variety with watering.',minimum('Watered'),(8,16)),
      ('Natural specialist','Harvest EACH variety without watering.',minimum('Natural'),(8,16)),
      ('Mixed ripe beds','Have three different varieties ripe together, then harvest a bed.',care.get('mixed_beds46',0),(3,8)),
      ('Community builder','Complete DIFFERENT community projects.',len(book),(3,6)),
      ('Community provider','Complete community deliveries; projects can be repeated.',sum(book.values()),(12,24)),
      ('A welcoming home','Bring rescued Budew safely home.',progress['rescued'],(50,100)),
      ('Resident champion','Reach three hearts with this many residents.',happy(care),(20,35)),
      ('All-biome rescuer','Rescue Budew on successful runs in DIFFERENT biomes.',len(rescue.get('biomes',[])),(3,5)),
      ('Expert rescue','Clear Expert with BOTH Budew rescued.',rescue.get('expert',0),(5,15)),
      ('Careful rescue','Clear tier 4 or 5 with BOTH Budew and no hits, Standard or Expert.',rescue.get('careful',0),(3,10)),
      ('Thriving sanctuary','Each set: 5 rescued Budew, 10 harvests and 2 happy residents.',min(progress['rescued']//5,care.get('harvests',0)//10,happy(care)//2),(5,10)),
    )
    return [dict(title='Mastery / '+title,detail=detail,current=current,target=n) for title,detail,current,targets in metrics for n in targets]

def home_milestones(progress):
    c=progress.get('care',{}); h=c.get('harvests',0); f=sum(c.get('friends',{}).values()); r=progress['rescued']; b=c.get('projects46',{})
    return [
      ('First harvest',h>=1,'Harvest one berry bed.'),
      ('A shared picnic',h>=1 and f>=3,'1 harvest + 3 friendship hearts. Unlock: Picnic.'),
      ('A garden in bloom',h>=5 and f>=5,'5 harvests + 5 friendship hearts. Unlock: Blossom arch.'),
      ('Lights across the garden',len(progress['restored'])==5,'Restore five biomes. Unlock: Fountain.'),
      ('First arrivals',r>=5,'Bring 5 Budew safely home.'),
      ('A growing village',r>=20,'Bring 20 Budew safely home.'),
      ('Resident haven',r>=50 and happy(c)>=15,'50 rescues + 15 happy residents.'),
      ('Four seasons',len(c.get('grown_types',[]))==4,'Harvest all four berry varieties.'),
      ('Garden steward',h>=30 and f>=20,'30 harvests + 20 friendship hearts.'),
      ('The shared table',len(b)>=3,'Complete 3 different projects. Unlock: Market stall.'),
      ('A place for everyone',len(b)==6,'Complete all 6 projects. Unlock: Welcome gazebo.'),
      ('Orchard planner',c.get('mixed_beds46',0)>=3,'Harvest 3 arrangements of three different ripe beds.'),
      ('Old friends',happy(c)>=25,'Help 25 residents reach three hearts.'),
      ('Community tradition',sum(b.values())>=12,'Complete 12 community deliveries.'),
      ('Rescue network',len(progress.get('rescue_mastery46',{}).get('biomes',[]))==5,'Bring Budew home from every biome.'),
      ('Living sanctuary',all(t['current']>=t['target'] for t in advanced_tasks(progress)),'Complete all 24 mastery goals. Unlock: Sanctuary monument.'),
    ]
