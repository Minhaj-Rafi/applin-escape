"""Rebuild the original rescue/warning sounds and five quiet pursuit rhythms."""
import math
from audio import ASSETS, RATE, add_note, write_wav
from compose import TRACKS


def build():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for name,notes,step in [('warning',(620,620,830),.13), ('rescue',(660,880,990,1320),.12), ('fruit',(330,260,196),.08), ('bell',(784,1176,1568),.18), ('turn',(220,294,330),.08), ('wind',(440,660,880),.09)]:
        data=[0.0]*int((len(notes)*step+.3)*RATE)
        for i,note in enumerate(notes): add_note(data,i*step,.20,note,.16,True)
        write_wav(ASSETS/f'{name}.wav',data)
    for i,(_,_,bpm,root,_,_,_) in enumerate(TRACKS):
        beat=60/bpm
        data=[0.0]*int(8*beat*RATE)
        for j in range(16):
            start=int(j*beat*.5*RATE)
            for k in range(int(.10*RATE)):
                if start+k >= len(data): break
                t=k/RATE
                freq=95 if j%2==0 else 170+i*9
                env=min(1,t/.004)*math.exp(-t*43)
                data[start+k]+=.22*env*math.sin(math.tau*freq*t)
        write_wav(ASSETS/f'pursuit_{i+1}.wav',data)


if __name__=='__main__': build()
