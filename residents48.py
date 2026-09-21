"""Stable resident personalities and finite, saved personal requests."""
from garden_timers import BERRIES

PERSONALITIES=(
 ('Curious',('I counted the stepping stones. There are more than I expected!','Could a seed float all the way across the pond?','There is always a new corner to explore here.')),
 ('Gentle',('The pond is quiet today. I saved you a spot beside it.','I helped a new arrival find the berry garden.','A little shade makes a lovely resting place.')),
 ('Cheerful',('I made up a song for watering day!','The garden smells wonderful after a harvest.','Everyone is invited to our next picnic.')),
 ('Thoughtful',('I like watching a seed become a plant.','A garden takes time. That is part of what makes it special.','I remember the path home, but this is my favourite place.')),
 ('Adventurous',('One day I would like to see the far side of the hills.','I practised my brave face beside the fountain.','Exploring is better when there is a home to return to.')),
)

def profile(index):
    personality,lines=PERSONALITIES[index%len(PERSONALITIES)]
    return personality,BERRIES[(index*3+index//5)%4][0],lines

def state(care,index): return care.setdefault('residents48',{}).setdefault(str(index),{'talks':0,'requests':[]})

def talk(care,index):
    entry=state(care,index); _,favourite,lines=profile(index)
    line=lines[entry['talks']%len(lines)]; entry['talks']+=1
    return line+(' My favourite berry is '+favourite+'.' if entry['talks']==1 else '')

def requests(care,index):
    entry=care.get('residents48',{}).get(str(index),{}); _,favourite,_=profile(index)
    done=entry.get('requests',[]); points=care.get('friends',{}).get(str(index),0)
    return (
      ('A proper hello','Talk to this resident once.',index in care.get('chatted',[]),0 in done),
      ('A favourite picnic',f'Deliver 2 {favourite} berries. They will be spent.',care.get('berry_types',{}).get(favourite,0)>=2,1 in done),
      ('Putting down roots',f'Reach 3 hearts and harvest {favourite} at least once.',points>=3 and favourite in care.get('grown_types',[]),2 in done),
    )

def complete_request(progress,index,number):
    if not 0<=index<progress['rescued'] or number not in range(3): return 'Choose a resident request.'
    care=progress['care']; entry=state(care,index)
    if number in entry['requests']: return 'This request is already complete. Nothing was spent.'
    if number and number-1 not in entry['requests']: return 'Complete the previous request first.'
    if not requests(care,index)[number][2]: return 'The request requirements are not met yet. Nothing was spent.'
    if number==1:
        favourite=profile(index)[1]; care['berry_types'][favourite]-=2
        care['berries']=sum(care['berry_types'].values())
    entry['requests'].append(number)
    from rewards44 import record_interaction
    record_interaction(care)
    return 'Request complete! Home ribbon earned for this resident.' if len(entry['requests'])==3 else 'Request complete! The next chapter of this resident story is ready.'
