"""Five new compositions using handheld-era timbres; no borrowed melodies."""
import math
import random
from audio import RATE, ASSETS, write_wav

TRACKS = (
    ('biome_1', 'Bramblebrook Morning', 112, 60, (0,2,4,7,9), (0,2,1,3,2,4,3,1, 2,0,3,4,2,1,0,2), 'pulse'),
    ('biome_2', 'Tideglass Crossing', 126, 62, (0,2,4,7,9), (0,3,2,4,1,2,0,3, 4,2,1,3,0,2,1,0), 'marimba'),
    ('biome_3', 'Bells Beneath the Ferns',  90, 57, (0,2,3,7,10), (2,0,3,1,4,2,0,1, 3,4,1,2,0,3,2,0), 'bell'),
    ('biome_4', 'Copperleaf Footsteps', 136,  60, (0,2,3,5,7), (0,1,3,2,4,1,2,0, 3,2,1,4,3,0,2,1), 'reed'),
    ('biome_5', 'A Sky Full of Waypoints', 104,  60, (0,2,5,7,9), (4,1,3,0,2,4,1,2, 0,3,4,2,1,3,0,4), 'glass'),
)


def tone(data, start, duration, freq, vol, instrument):
    count=int(duration*RATE)
    begin=int(start*RATE)
    for n in range(count):
        index=(begin+n)%len(data)
        t=n/RATE
        phase=math.tau*freq*t
        attack=min(1,t/.012)
        decay=(1-n/count)
        if instrument=='pulse':
            value=(math.sin(phase)+math.sin(phase*3)/3+math.sin(phase*5)/5)*.72
            env=attack*decay**1.3
        elif instrument=='marimba':
            value=math.sin(phase)+.3*math.sin(phase*4)*math.exp(-t*19)
            env=attack*math.exp(-t*7)*decay
        elif instrument=='bell':
            value=math.sin(phase)+.35*math.sin(phase*2.76)+.14*math.sin(phase*5.4)
            env=attack*math.exp(-t*2.7)*decay
        elif instrument=='reed':
            value=math.sin(phase)+.23*math.sin(phase*2)+.12*math.sin(phase*3)
            env=attack*decay**1.8
        elif instrument=='glass':
            value=math.sin(phase+.015*math.sin(t*31))+.3*math.sin(phase*2)
            env=attack*math.exp(-t*3.5)*decay
        else:
            value=math.sin(phase)+.12*math.sin(phase*2)
            env=attack*decay
        data[index]+=value*env*vol


def compose_all():
    ASSETS.mkdir(parents=True,exist_ok=True)
    for tier,(filename,title,bpm,root,scale,motif,instrument) in enumerate(TRACKS):
        beat=60/bpm
        beats=48 if tier==2 else 64
        data=[0.0]*int(beats*beat*RATE)
        rng=random.Random(410+tier)
        hz=lambda note: 440*2**((note-69)/12)
        for i in range(beats*2):
            if i%16 in (7,15) or (tier==2 and i%3==2):
                continue
            degree=motif[i%16]
            octave=12 if (i//16)%4 in (1,2) else 0
            note=root+12+scale[degree]+octave
            duration=beat*(1.2 if i%8==6 else .7)
            tone(data,i*beat/2,duration,hz(note),.105,instrument)
            if tier in (2,4):
                tone(data,i*beat/2+beat*.65,beat*.65,hz(note),.024,instrument)
        for b in range(beats):
            chord=[0,3,4,1][(b//4)%4]
            bass=root-12+scale[chord]
            if b%2==0:
                tone(data,b*beat,beat*1.8,hz(bass),.13,'bass')
            if b%2==1:
                tone(data,b*beat,beat*.55,hz(root+scale[(chord+2)%5]),.043,'reed')
            # Soft original percussion, with distinct rhythmic density by biome.
            if tier!=2 and b%2==0:
                for n in range(int(.11*RATE)):
                    t=n/RATE
                    data[(int(b*beat*RATE)+n)%len(data)]+=.085*math.sin(math.tau*(70*t-80*t*t))*math.exp(-t* 30)
            if tier in (0,1,3) or b%4==3:
                for n in range(int(.045*RATE)):
                    t=n/RATE
                    data[(int((b+.5)*beat*RATE)+n)%len(data)]+=.024*rng.uniform(-1,1)*math.exp(-t*90)
        peak=max(abs(v) for v in data)
        if peak>.78:
            data=[v*.78/peak for v in data]
        # Close the endpoint without a click; each loop contains its own cadence.
        fade=int(.012*RATE)
        for n in range(fade):
            data[n]*=n/fade
            data[-1-n]*=n/fade
        write_wav(ASSETS/f'{filename}.wav',data)
        print(f'{title}: {len(data)/RATE:.1f}s')


if __name__=='__main__':
    compose_all()
