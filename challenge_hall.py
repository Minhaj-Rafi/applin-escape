"""A finite, explicit collection of mastery contracts with no streak requirements."""
GOALS=('Clear','Untouched','Rescue duo','No escape','Untouched + rescue','Untouched + no escape','Rescue + no escape','All three')
TOTAL=5*3*4*2*len(GOALS)

def combinations():
    from expedition import SKILLS,ABILITIES
    return [(tier,skill,ability,coop,goal) for tier in range(5) for skill in SKILLS for ability in ABILITIES for coop in (False,True) for goal in GOALS]


def contract_key(game):
    return f'{game.tier}/{game.skill}/{game.ability}/{int(game.coop)}/{game.contract}'


def goal_met(game):
    checks={'Clear':True,'Untouched':game.hits==0,'Rescue duo':game.rescued==2,'No escape':game.escapes_used==0,
            'Untouched + rescue':game.hits==0 and game.rescued==2,
            'Untouched + no escape':game.hits==0 and game.escapes_used==0,
            'Rescue + no escape':game.rescued==2 and game.escapes_used==0,
            'All three':game.hits==0 and game.rescued==2 and game.escapes_used==0}
    return game.state=='cleared' and checks.get(game.contract,False)


def credit_contract(game):
    if not getattr(game,'contract',None): return
    book=game.store.get('contract_book43',{})
    if goal_met(game):
        key=contract_key(game); old=book.get(key,{})
        book[key]={'clears':old.get('clears',0)+1,'seconds':min(game.elapsed,old.get('seconds',float('inf')))}
        game.store.set('contract_book43',book)
        achievements=set(game.store.get('achievements',[]))
        for target,title in ((1,'First mastery'),(10,'Trail apprentice'),(50,'Trail specialist'),(120,'Biome scholar'),(240,'Master explorer'),(TOTAL,'Complete mastery')):
            if len(book)>=target: achievements.add(title)
        game.store.set('achievements',sorted(achievements))
