"""Saved wall-clock growth: crops never spoil and progress while the game is closed."""
import time
BERRIES=(('Oran',120,(92,167,241)),('Pecha',300,(240,153,172)),('Cheri',600,(238,91,70)),('Sitrus',900,(244,202,78)))


def migrate_crops(care,now=None):
    now=time.time() if now is None else now
    if 'crops' not in care:
        care['crops']=[None if stage==0 else {'kind':0,'ready_at':now if stage==3 else now+120,'watered':False} for stage in care['beds']]
    care.setdefault('berry_types',{'Oran':care['berries']})
    care.setdefault('grown_types',[])
    return care['crops']


def crop_stage(crop,now=None):
    if crop is None: return 0
    now=time.time() if now is None else now
    remaining=max(0,crop['ready_at']-now)
    if remaining==0: return 3
    return 2 if remaining<=BERRIES[crop['kind']][1]/2 else 1


def crop_action(care,action,index,kind=0,now=None):
    now=time.time() if now is None else now
    crops=migrate_crops(care,now)
    if index not in range(3) or kind not in range(len(BERRIES)): return 'Choose a valid garden bed.'
    crop=crops[index]
    if action=='plant' and crop is None:
        name,duration,_=BERRIES[kind]
        crops[index]={'kind':kind,'ready_at':now+duration,'watered':False}
        message=f'{name} planted. Ready in {duration//60} minutes, including time away.'
    elif action=='water' and crop and not crop['watered'] and crop_stage(crop,now)<3:
        crop['watered']=True
        crop['ready_at']=max(now+1,crop['ready_at']-BERRIES[crop['kind']][1]*.2)
        message='Watered! Growing time reduced once by 20% of the original duration.'
    elif action=='harvest' and crop and crop_stage(crop,now)==3:
        name=BERRIES[crop['kind']][0]; care['berries']+=2; care['harvests']+=1
        care['berry_types'][name]=care['berry_types'].get(name,0)+2
        if name not in care['grown_types']: care['grown_types'].append(name)
        crops[index]=None; message=f'Two {name} berries harvested.'
    elif crop:
        seconds=max(0,int(crop['ready_at']-now+.999))
        message='Ready to harvest.' if seconds==0 else f'Still growing: {seconds//60}:{seconds%60:02d} remaining. Ripe berries will wait for you.'
    else: message='Plant a berry in this bed first.'
    care['beds']=[crop_stage(c,now) for c in crops]
    return message
