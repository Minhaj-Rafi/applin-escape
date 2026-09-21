"""Run-only shiny rolls and persistent sanctuary restoration."""
import secrets

SHINY_ODDS = 256


def roll_shiny(coop):
    # Independent of map seeds, challenge codes, cosmetics and achievements.
    return [secrets.randbelow(SHINY_ODDS)==0,
            secrets.randbelow(SHINY_ODDS)==0 if coop else False]


def home_progress(store):
    value=store.get('sanctuary_v4',None)
    if value is None:
        # Previous victories restore their gardens too. Old rescue totals were not recorded.
        restored=[r[0] for r in store.db.execute("SELECT DISTINCT tier FROM runs WHERE outcome='cleared' AND mode NOT LIKE 'tutorial%' ORDER BY tier") if r[0] in range(5)]
        value={'restored':restored,'rescued':0,'receipts':[],'chapters':[]}
        store.set('sanctuary_v4',value)
    return value


def credit_home(game):
    if game.mode=='tutorial' or game.state!='cleared': return
    progress=home_progress(game.store)
    if game.stage_id in progress['receipts']: return
    progress['receipts'].append(game.stage_id)
    progress['restored']=sorted(set(progress['restored'])|{game.tier})
    progress['rescued']+=game.rescued
    if getattr(game,'story_run',False):
        progress['chapters']=sorted(set(progress['chapters'])|{game.tier})
    game.store.set('sanctuary_v4',progress)


def decorations(progress):
    result=['Natural']
    if progress['restored']: result.append('Lanterns')
    if progress['rescued']>=3: result.append('Flowers')
    if len(progress['restored'])>=5: result.append('Fountain')
    care=progress.get('care',{})
    friendship=sum(care.get('friends',{}).values())
    if care.get('harvests',0)>=1 and friendship>=3: result.append('Picnic')
    if care.get('harvests',0)>=5 and friendship>=5: result.append('Blossom arch')
    return result
