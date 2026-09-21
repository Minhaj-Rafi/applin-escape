"""Local descriptive run statistics. No rankings or automatic difficulty changes."""
from model import TIERS

def summarize(store,skill='Standard',players='solo'):
    groups=[{'biome':t.biome,'attempts':0,'clears':0,'hits':0,'escapes':0,'clear_seconds':0.0} for t in TIERS]
    for tier,outcome,seconds,hits,escapes,mode in store.db.execute('SELECT tier,outcome,seconds,hits,escapes,mode FROM runs'):
        parts=(mode or '').split('/')
        if tier not in range(5) or outcome not in ('cleared','caught') or len(parts)<3: continue
        if parts[0]=='tutorial' or parts[1]!=skill or parts[2]!=players: continue
        row=groups[tier];row['attempts']+=1;row['hits']+=hits or 0;row['escapes']+=escapes or 0
        if outcome=='cleared':row['clears']+=1;row['clear_seconds']+=seconds or 0
    for row in groups:
        n=row['attempts'];wins=row['clears']
        row['clear_rate']=round(wins/n*100,1) if n else None
        row['average_hits']=round(row['hits']/n,1) if n else None
        row['average_escapes']=round(row['escapes']/n,1) if n else None
        row['average_clear_seconds']=round(row['clear_seconds']/wins,1) if wins else None
    return groups

def guidance(rows):
    available=[r for r in rows if r['attempts']>=5]
    if not available:return 'Play a few completed runs first. Small samples cannot tell us much about difficulty.'
    row=min(available,key=lambda r:r['clear_rate'])
    if row['average_hits']>=1 and row['average_escapes']<1:
        return row['biome']+': try using an escape before birds surround you.'
    if row['clear_rate']<60:return row['biome']+': practise its biome interaction and watch the swoop warning route.'
    return 'Your clears are becoming consistent. Try a different ability or an optional mastery contract.'
