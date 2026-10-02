"""Author an original, editable Roblox place and a matching web-viewer manifest.

Everything visible is geometry authored here; there are no marketplace models,
remote assets, executable downloads, or generative image/video stand-ins.
Coordinates are Roblox studs, Y-up. Seeded scenery makes builds reproducible.
"""
import json, math, random, pathlib, xml.etree.ElementTree as ET
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
rng = random.Random(1819)
parts, labels = [], []
palette = {
    'concrete': '#777c72', 'concreteDark': '#505951', 'edge': '#a5aa9c',
    'olive': '#465446', 'oliveLight': '#65705a', 'steel': '#333c3c',
    'metal': '#85908a', 'rubber': '#202727', 'glass': '#517779',
    'sand': '#9a9377', 'ochre': '#bb8b48', 'white': '#dfded0',
    'asphalt': '#424b48', 'dirt': '#686d50', 'grass': '#626e50',
    'pine': '#334d3e', 'pineLight': '#425e47', 'bark': '#665b49',
    'rock': '#6f7972', 'snow': '#c1ccc5', 'water': '#476f76',
    'warm': '#ffd399', 'red': '#b55647', 'screen': '#8fbeac'
}

def add(group, name, pos, size, color='concrete', shape='box', rot=(0,0,0), material=None, **extra):
    p = dict(group=group, name=name, pos=[round(v,4) for v in pos],
             size=[round(v,4) for v in size], color=palette.get(color,color),
             shape=shape, rot=[round(v,6) for v in rot], material=material or
             ('Neon' if color in ('warm','screen') else 'Metal' if color in ('steel','metal') else
              'Glass' if color=='glass' else 'Concrete' if 'concrete' in color else 'SmoothPlastic'))
    p.update(extra); parts.append(p); return p

def box(g,n,x,y,z,w,h,d,c='concrete',**kw): return add(g,n,(x,y,z),(w,h,d),c,**kw)
def cyl(g,n,x,y,z,h,diam,c='steel',**kw):
    # Roblox cylinders run along X; rotate about Z to stand them upright.
    return add(g,n,(x,y,z),(h,diam,diam),c,'cylinder',rot=(0,0,math.pi/2),**kw)
def beam(g,n,a,b,width=.4,c='steel'):
    dx,dy,dz = (b[i]-a[i] for i in range(3)); length=math.sqrt(dx*dx+dy*dy+dz*dz)
    # A box's Y axis points along the segment. Euler XYZ, shared by Roblox and Three.
    rx=math.atan2(dz,math.sqrt(dx*dx+dy*dy)); rz=-math.atan2(dx,dy)
    # Compose Rz * Rx by explicit rotation matrix (avoids Euler-order ambiguity).
    vx,vy,vz=dx/length,dy/length,dz/length
    up=(0,0,1) if abs(vz)<.99 else (1,0,0)
    xx=up[1]*vz-up[2]*vy; xy=up[2]*vx-up[0]*vz; xz=up[0]*vy-up[1]*vx
    norm=math.sqrt(xx*xx+xy*xy+xz*xz); xx,xy,xz=xx/norm,xy/norm,xz/norm
    zx,zy,zz=xy*vz-xz*vy,xz*vx-xx*vz,xx*vy-xy*vx
    return add(g,n,tuple((a[i]+b[i])/2 for i in range(3)),(width,length,width),c,
               matrix=[xx,vx,zx,xy,vy,zy,xz,vz,zz])

def sign(g,n,text,pos,size=(12,3,.25),rot=(0,0,0),color='steel',ink='white',face='Front'):
    p=add(g,n,pos,size,color,rot=rot)
    labels.append(dict(part=len(parts)-1,text=text,ink=palette.get(ink,ink),face=face)); return p

def lamp(g,x,z,height=17):
    cyl(g,'Light mast',x,height/2,z,height,.38,'steel')
    beam(g,'Cantilever',(x,height,z),(x+3,height,z),.3)
    box(g,'Luminaire',x+3,height-.3,z,2.5,.6,1.4,'steel')
    box(g,'Warm lens',x+3,height-.65,z,2,.12,1,'warm',light=dict(range=30,brightness=1.4))
    box(g,'Mast footing',x,.25,z,2,.5,2,'concreteDark')

def sandbags(g,x,z,rows=3,length=12,y=.7):
    for row in range(rows):
        for i in range(int(length/2.8)):
            box(g,'Sandbag',x-length/2+i*2.9+(row%2)*.7,y+row*.65,z,2.8,.65,1.55,'sand',rot=(0,rng.uniform(-.05,.05),0))

def crate(g,x,y,z,s=3):
    box(g,'Field crate',x,y+s/2,z,s,s,s,'oliveLight')
    for dx in (-s*.43,s*.43): box(g,'Crate strap',x+dx,y+s/2,z,.16,s+.08,s+.08,'steel')
    box(g,'Crate handle',x,y+s*.55,z-s/2-.06,.8,.18,.12,'metal')

def barrel(g,x,z):
    cyl(g,'Fuel drum',x,1.7,z,3.4,2.2,'olive')
    for y in (.35,1.2,2.5,3.05): cyl(g,'Drum band',x,y,z,.12,2.3,'steel')
    cyl(g,'Drum cap',x+.45,3.45,z,.1,.3,'metal')

def pine(x,z,h):
    g='Forest'; y=terrain(x,z)
    cyl(g,'Spruce trunk',x,y+h*.27,z,h*.54,h*.065,'bark')
    # Four corner wedges join at the apex of each layer. No uploaded meshes.
    for level in range(4):
        r=h*(.26-level*.05); height=h*.38
        for k in range(4):
            a=k*math.pi/2
            ox=r/2; oz=-r/2
            px=x+math.cos(a)*ox+math.sin(a)*oz
            pz=z-math.sin(a)*ox+math.cos(a)*oz
            add(g,'Spruce crown',(px,y+h*.28+level*h*.16,pz),(r,height,r),
                'pine' if (level+k)%3 else 'pineLight','corner',rot=(0,a,0))

def terrain(x,z):
    # Quiet floor around the fort; taller layered foothills outside the perimeter.
    radius=math.sqrt((x*.84)**2+(z*.9)**2)
    if radius<140: return -.55
    return max(-.6,min(42,(radius-135)*.2))+3*math.sin(x*.026)*math.cos(z*.022)

def triangle(g,name,a,b,c,color='grass'):
    """Two native WedgeParts exactly tile an arbitrary terrain triangle."""
    def sub(v,w): return tuple(v[i]-w[i] for i in range(3))
    def dot(v,w): return sum(v[i]*w[i] for i in range(3))
    def length(v): return math.sqrt(dot(v,v))
    # Put the longest edge opposite the apex so its projection lies inside.
    edges=[(length(sub(b,c)),a,b,c),(length(sub(a,c)),b,a,c),(length(sub(a,b)),c,a,b)]
    _,a,b,c=max(edges,key=lambda v:v[0])
    base=sub(c,b); l=length(base); unit=tuple(v/l for v in base)
    projection=dot(sub(a,b),unit); d=tuple(b[i]+unit[i]*projection for i in range(3))
    altitude=sub(a,d); h=length(altitude)
    if h<.001:return
    yy=tuple(v/h for v in altitude)
    for end in (b,c):
        line=sub(d,end); width=length(line)
        if width<.001:continue
        zz=tuple(v/width for v in line)
        xx=(yy[1]*zz[2]-yy[2]*zz[1],yy[2]*zz[0]-yy[0]*zz[2],yy[0]*zz[1]-yy[1]*zz[0])
        add(g,name,tuple((end[i]+a[i])/2 for i in range(3)),(.08,h,width),color,'wedge',material='Grass',castShadow=False,
            matrix=[xx[0],yy[0],zz[0],xx[1],yy[1],zz[1],xx[2],yy[2],zz[2]])

def tower(x,z):
    g='Watchtower'; base=1
    for dx in (-5,5):
        for dz in (-5,5): box(g,'Tower pier',x+dx,11,z+dz,1.1,22,1.1,'olive')
    for dz in (-5,5):
        beam(g,'Diagonal brace',(x-5,3,z+dz),(x+5,20,z+dz),.55,'oliveLight')
        beam(g,'Diagonal brace',(x+5,3,z+dz),(x-5,20,z+dz),.55,'oliveLight')
    for dx in (-5,5): beam(g,'Side brace',(x+dx,3,z-5),(x+dx,20,z+5),.55,'oliveLight')
    box(g,'Observation deck',x,22,z,14,1,14,'steel')
    box(g,'Cabin roof',x,29,z,15,.75,15,'olive')
    box(g,'Cabin sill',x,23.3,z,12,1.8,12,'olive')
    # Window panes and corner mullions.
    for dx in (-5.8,5.8):
        box(g,'Observation window',x+dx,26,z,.18,3.4,10.9,'glass',transparent=.16)
    for dz in (-5.8,5.8): box(g,'Observation window',x,26,z+dz,11,3.4,.18,'glass',transparent=.16)
    for dx in (-5.8,5.8):
        for dz in (-5.8,5.8): box(g,'Window mullion',x+dx,26,z+dz,.3,4.2,.3,'steel')
    for dz in (-6.7,6.7):
        for dx in (-6.6,0,6.6): box(g,'Guardrail post',x+dx,24,z+dz,.18,3,.18,'steel')
        box(g,'Guardrail',x,25.5,z+dz,13.4,.18,.18,'steel')
    for dx in (-6.7,6.7): box(g,'Side rail',x+dx,25.5,z,.18,.18,13.4,'steel')
    for dx in (-2,2): box(g,'Ladder upright',x+dx,11,z+7,.2,22,.2,'metal')
    for i in range(24): box(g,'Ladder rung',x,.7+i*.9,z+7,4,.16,.18,'metal')
    cyl(g,'Roof antenna',x,32,z,6,.14,'steel')
    box(g,'Beacon',x,35.4,z,.7,.7,.7,'red',material='Neon')
    box(g,'Searchlight',x+4,28,z-6,2,1.7,2,'steel')
    box(g,'Searchlight lens',x+4,28,z-7.05,1.55,1.25,.1,'warm')

def container(x,y,z,color='olive',turn=0):
    g='Logistics'; yaw=turn
    # local placement helper to make complete modules rotatable.
    def cb(n,dx,dy,dz,w,h,d,c):
        return box(g,n,x+math.cos(yaw)*dx+math.sin(yaw)*dz,y+dy,
                   z-math.sin(yaw)*dx+math.cos(yaw)*dz,w,h,d,c,rot=(0,yaw,0))
    cb('Shipping container',0,4.4,0,12,8.8,25,color)
    for dx in (-6.1,6.1):
        for i in range(22): cb('Corrugated siding',dx,4.4,-11.7+i*1.1,.16,8.1,.25,'oliveLight' if color=='olive' else 'ochre')
    for dx in (-5.9,5.9):
        for dz in (-12.4,12.4): cb('Container corner',dx,4.4,dz,.35,8.9,.35,'steel')
    for dx in (-3.0,3.0):
        cb('Cargo door',dx,4.4,-12.65,5.7,8.4,.22,color)
        cb('Locking rod',dx,4.4,-12.88,.12,8,.12,'metal')
        cb('Lock handle',dx+.6,3,-13,1.3,.15,.15,'metal')
    for dy in (.35,8.4): cb('Container end rail',0,dy,-12.75,12,.3,.35,'steel')

def truck(x,z):
    g='Motor pool'
    box(g,'Chassis',x,2.3,z,8,1,17,'steel')
    box(g,'Hood',x,4.3,z-5,7.7,2.2,4,'olive')
    box(g,'Cabin',x,5.4,z-1.5,7.7,4.8,4,'olive')
    box(g,'Windscreen',x,6,z-3.56,6.3,2.1,.12,'glass')
    for dx in (-3.91,3.91):
        box(g,'Door window',x+dx,6.3,z-1.5,.1,1.8,2.7,'glass')
        box(g,'Side mirror',x+dx*1.2,6,z-2,.3,1,.75,'metal')
    box(g,'Cargo bed',x,3.4,z+5,8,.5,9,'olive')
    for dx in (-3.8,3.8):
        box(g,'Bed side',x+dx,4.7,z+5,.3,2.3,9,'olive')
        for dz in (1.8,5,8.8): box(g,'Canvas rib',x+dx,6,z+dz,.18,3.7,.18,'steel')
    box(g,'Canvas canopy',x,7.8,z+5,8.2,.4,9.2,'oliveLight')
    box(g,'Tailgate',x,4.7,z+9.5,8,2.3,.3,'olive')
    for dz in (-4.4,4.1,7.2):
        for dx in (-4.15,4.15):
            add(g,'Tire',(x+dx,2.15,z+dz),(1.4,4.1,4.1),'rubber','cylinder')
            add(g,'Wheel hub',(x+dx*1.14,2.15,z+dz),(.2,2.1,2.1),'metal','cylinder')
    box(g,'Grille',x,4.1,z-7.13,4.5,1.7,.2,'steel')
    for dx in (-1.8,-.9,0,.9,1.8): box(g,'Grille slat',x+dx,4.1,z-7.27,.2,1.4,.15,'metal')
    for dx in (-2.8,2.8): box(g,'Headlight',x+dx,4.7,z-7.2,1.2,.9,.14,'warm')
    box(g,'Front bumper',x,2.9,z-7.5,8.7,.65,.7,'steel')

def helicopter(x,z):
    g='Helipad'
    add(g,'Rotorcraft fuselage',(x,5,z),(7,6.5,15),'olive','sphere')
    add(g,'Cockpit canopy',(x,5.7,z-5.2),(6.5,4.1,5),'glass','sphere',transparent=.1)
    box(g,'Cockpit divider',x,6,z-7.3,.22,3.1,.3,'steel')
    add(g,'Tail boom',(x,5,z+11),(2.4,2.6,13),'olive','box',rot=(.1,0,0))
    add(g,'Tail fin',(x,7,z+17),(1,6,4),'olive','wedge',rot=(0,math.pi,0))
    box(g,'Tail plane',x,5.3,z+14.4,9,.35,2.4,'olive')
    cyl(g,'Rotor mast',x,9,z,4,.65,'steel')
    box(g,'Rotor hub',x,10.8,z,2,.5,2,'metal')
    for yaw in (0,math.pi/2):
        add(g,'Main rotor',(x,11.1,z),(29,.18,1.1),'steel',rot=(0,yaw+.35,0))
    for dx in (-3.4,3.4):
        box(g,'Landing skid',x+dx,1.1,z,.35,.4,14,'steel')
        for dz in (-3,4): beam(g,'Skid strut',(x+dx,1.2,z+dz),(x+dx*.65,3.5,z+dz),.35,'metal')
        box(g,'Cabin side',x+dx,5.2,z,.1,2,4,'olive')
        box(g,'Cabin window',x+dx*1.02,6,z+1,.1,1.5,2.5,'glass')
        box(g,'Step',x+dx*1.15,2.3,z,1.5,.2,3.5,'steel')
    add(g,'Tail rotor',(x+1.6,7,z+17),(.2,7,.5),'steel',rot=(.45,0,0))
    add(g,'Tail rotor',(x+1.6,7,z+17),(.2,.5,7),'steel',rot=(.45,0,0))

def h_marker(g,x,y,z,s=1):
    for dx in (-3*s,3*s): box(g,'Helipad H',x+dx,y,z,1.2*s,.04,8*s,'white')
    box(g,'Helipad H',x,y,z,6*s,.04,1.2*s,'white')

def build():
    # Landform and approach: a designed valley rather than a naked baseplate.
    box('Landscape','Valley foundation',0,-6,0,950,10,950,'dirt',material='Ground')
    for x in range(-420,421,35):
        for z in range(-420,421,35):
            if abs(x)<133 and -135<z<124: continue
            corners=[(x+dx,terrain(x+dx,z+dz),z+dz) for dx,dz in ((-17.5,-17.5),(17.5,-17.5),(17.5,17.5),(-17.5,17.5))]
            triangle('Landscape','Sculpted foothill',corners[0],corners[1],corners[2])
            triangle('Landscape','Sculpted foothill',corners[0],corners[2],corners[3])
    # Large distant, layered granite crags.
    for i in range(19):
        a=(i/19)*math.tau; radius=rng.uniform(340,470)
        x,z=math.sin(a)*radius,math.cos(a)*radius; h=rng.uniform(95,165); w=rng.uniform(150,225)
        phase=rng.uniform(0,math.tau)
        for k in range(4):
            yaw=k*math.pi/2+phase
            ox=w/4; oz=-w/4
            add('Mountains','Granite peak',(x+math.cos(yaw)*ox+math.sin(yaw)*oz,h/2+12,
                 z-math.sin(yaw)*ox+math.cos(yaw)*oz),(w/2,h,w/2),'rock','corner',rot=(0,yaw,0),castShadow=False)
            add('Mountains','Snow summit',(x+math.cos(yaw)*ox*.35+math.sin(yaw)*oz*.35,h*.83+12.4,
                 z-math.sin(yaw)*ox*.35+math.cos(yaw)*oz*.35),(w*.175,h*.34,w*.175),'snow','corner',rot=(0,yaw,0),castShadow=False)
    # River to the east, rocky shore and bridge.
    box('Landscape','Alpine water',187,-.05,5,44,.3,720,'water',material='SmoothPlastic',transparent=.12)
    for i in range(65):
        z=rng.uniform(-300,330); x=rng.choice((153,214))+rng.uniform(-6,6)
        add('Landscape','River rock',(x,rng.uniform(0,2),z),(rng.uniform(3,9),rng.uniform(2,6),rng.uniform(3,9)),'rock','sphere')
    for _ in range(155):
        x,z=rng.uniform(-325,325),rng.uniform(-325,325)
        if abs(x)<139 and -143<z<132: continue
        if 150<x<223: continue
        if abs(x)<24 and z<-100: continue
        pine(x,z,rng.uniform(18,36))
    for _ in range(35):
        x,z=rng.uniform(-145,145),rng.uniform(-150,145)
        if abs(x)<117 and abs(z)<110: continue
        add('Landscape','Granite boulder',(x,1.3,z),(rng.uniform(5,12),rng.uniform(3,8),rng.uniform(5,12)),'rock','sphere',rot=(rng.random(),rng.random(),0))
    box('Roads','Compound asphalt',0,-.08,-5,214,.25,218,'asphalt',material='Asphalt')
    box('Roads','Approach road',0,-.03,-198,22,.3,210,'asphalt',material='Asphalt')
    for z in range(-290,-102,13): box('Roads','Approach centerline',0,.15,z,.6,.04,6,'ochre')
    for dx in (-10.6,10.6): box('Roads','Approach edge',dx,.15,-197,.35,.04,202,'white')
    box('Roads','Cross compound lane',0,.08,-39,199,.05,15,'concreteDark')
    for x in range(-98,98,15): box('Roads','Lane dash',x,.13,-39,7,.035,.3,'ochre')
    # Modular retaining perimeter with capstones and steel wire.
    for z in (-108,105):
        for x in range(-108,109,12):
            if z<0 and abs(x)<20: continue
            box('Perimeter','Wall module',x,4.5,z,11.8,9,2.1,'concrete')
            box('Perimeter','Wall cap',x,9.1,z,12,.35,2.7,'edge')
            box('Perimeter','Buttress',x-5.7,4.5,z+1.9,1.4,9.3,3.5,'concreteDark')
            box('Perimeter','Fence post',x,10.3,z,.14,2.4,.14,'steel')
            for y in (9.9,10.8,11.35): box('Perimeter','Security wire',x,y,z,12,.035,.035,'metal')
    for x in (-113,113):
        for z in range(-96,103,12):
            box('Perimeter','Wall module',x,4.5,z,2.1,9,11.8,'concrete')
            box('Perimeter','Wall cap',x,9.1,z,2.7,.35,12,'edge')
            box('Perimeter','Buttress',x-1.8,4.5,z-5.7,3.4,9.3,1.4,'concreteDark')
    for x,z in ((-96,-94),(96,-94),(-96,91),(96,91)): tower(x,z)
    # Checkpoint and gatehouse.
    g='Checkpoint'
    for x in (-19,19):
        box(g,'Gate pier',x,7,-107,3.8,14,5,'concreteDark')
        box(g,'Pier cap',x,14,-107,4.4,.65,5.5,'edge')
    sign(g,'Raven Ridge entrance','RAVEN RIDGE  /  OUTPOST 07',(0,13.4,-109.1),(36,3.2,.35))
    box(g,'Boom gate',0,3.4,-105,32,.55,.6,'ochre',dynamic='gate')
    for x in range(-15,16,3): box(g,'Gate stripe',x,3.41,-105,1.3,.57,.65,'steel',dynamic='gate')
    box(g,'Gate control',-18,2.5,-104,1,4,1,'olive',prompt='Toggle checkpoint barrier')
    box(g,'Gatehouse slab',-38,.25,-88,22,.5,21,'concrete')
    for x in (-48,-28): box(g,'Gatehouse wall',x,5,-88,1.1,9,20,'concreteDark')
    box(g,'Gatehouse back',-38,5,-78,20,9,1,'concreteDark')
    box(g,'Gatehouse sill',-38,2.2,-98,20,3.8,1,'concreteDark')
    box(g,'Gatehouse glass',-38,6,-98.1,18,3.7,.2,'glass',transparent=.18)
    for x in (-43,-33): box(g,'Gatehouse mullion',x,6,-98.35,.2,4,.3,'steel')
    box(g,'Gatehouse roof',-38,10,-88,23,1,23,'olive')
    sign(g,'Checkpoint sign','CHECKPOINT',(-38,8.7,-99),(16,1.5,.2))
    for x in (-16,16):
        for z in (-121,-126,-131):
            box(g,'Concrete bollard',x,1.4,z,1.3,2.8,1.3,'concrete')
            box(g,'Bollard reflector',x,2.1,z-.7,.7,.5,.08,'ochre')
    sandbags(g,35,-101,3,24)
    # Main command building: intentional brutalist bunker, accessible interior.
    g='Command'
    box(g,'Command foundation',-43,.5,28,73,1,61,'concreteDark')
    box(g,'North wall',-43,8,56,70,15,3,'concrete')
    box(g,'West wall',-77,8,28,3,15,57,'concrete')
    box(g,'East wall',-9,8,28,3,15,57,'concrete')
    # South opening is eight studs wide with a functional sliding door.
    box(g,'Facade left',-62.5,8,-1,30,15,3,'concrete')
    box(g,'Facade right',-23.5,8,-1,30,15,3,'concrete')
    box(g,'Door lintel',-43,13,-1,9,5,3,'concrete')
    box(g,'BunkerDoor',-43,5,-1,8,9,1,'olive',dynamic='bunker',prompt='Open command bunker')
    for x in (-46,-40): box(g,'Door rib',x,5,-1.6,.2,8,.12,'steel',dynamic='bunker')
    box(g,'Roof slab',-43,16,28,76,2,64,'concreteDark')
    for x in (-79, -7): box(g,'Roof parapet',x,17.6,28,1.3,1.8,63,'concrete')
    for z in (-3,59): box(g,'Roof parapet',-43,17.6,z,73,1.8,1.3,'concrete')
    for x in (-75,-61,-25,-11): box(g,'Facade pilaster',x,8,-3,1.6,15,2,'concreteDark')
    sign(g,'Command identification','COMMAND  /  07',(-43,12.8,-3.2),(27,2.5,.35))
    box(g,'Entrance canopy',-43,10.6,-6,17,.6,10,'olive')
    for x in (-50,-36): box(g,'Canopy rod',x,5.1,-9,.25,10,.25,'steel')
    for x in (-51,-35): box(g,'Entry light',x,8,-3.3,1.2,.8,.2,'warm',light=dict(range=20,brightness=1.5))
    # Full interior: briefing table, map wall, workstation bays, beams and lighting.
    box(g,'Interior floor',-43,1.06,27,66,.15,53,'edge')
    for z in (11,27,44): box(g,'Ceiling beam',-43,14.8,z,66,1,1.2,'steel')
    box(g,'Briefing tabletop',-43,5.2,28,20,.6,10,'oliveLight')
    for x in (-50,-36): box(g,'Table leg',x,3,28,.7,4.5,6,'steel')
    box(g,'Tactical map',-43,5.56,28,17,.08,7.8,'pine')
    for i in range(10):
        box(g,'Map contour',-50+i*1.4,5.61,28,1,.035,5.2,'oliveLight',rot=(0,math.sin(i)*.3,0))
    for dx,dz in ((-5,-1),(0,2),(5,-2)): box(g,'Map marker',-43+dx,5.72,28+dz,.5,.18,.5,'ochre')
    for x in (-67,-19):
        box(g,'Operations desk',x,4.1,36,6,.6,19,'olive')
        for z in (30,37,44):
            box(g,'Monitor housing',x,6,z,.65,3,4.2,'steel')
            box(g,'Monitor screen',x+(.34 if x< -43 else -.34),6,z,.04,2.5,3.6,'screen')
            box(g,'Keyboard',x+(.9 if x< -43 else -.9),4.5,z,1.2,.12,2.8,'steel')
            box(g,'Chair seat',x+(4 if x< -43 else -4),2.7,z,2.8,.4,2.8,'steel')
            box(g,'Chair back',x+(5 if x< -43 else -5),4,z,.3,2.8,2.8,'olive')
    sign(g,'Briefing board','RAVEN RIDGE\nSECTOR 07\nOPERATIONS',(-43,9,54.1),(24,8,.2))
    for z in (12,33,49): box(g,'Ceiling luminaire',-43,14.1,z,11,.1,1.2,'warm',light=dict(range=35,brightness=1.7))
    # Rooftop ventilation and communications lattice.
    for x in (-67,-55):
        box(g,'HVAC unit',x,19.4,43,9,4,8,'olive')
        for z in range(40,47): box(g,'Vent grille',x,21.5,z,7,.12,.12,'steel')
    for dx in (-2,2):
        for dz in (-2,2): box(g,'Radio mast leg',-24+dx,32,41+dz,.3,29,.3,'metal')
    for y in range(21,45,5):
        for z in (39,43): beam(g,'Mast lattice',(-26,y,z),(-22,y+5,z),.16,'metal')
        box(g,'Mast tie',-24,y,41,4,.2,4,'metal')
    cyl(g,'Antenna spindle',-24,50,41,7,.18,'steel')
    for y in (46,49,52): box(g,'Yagi antenna',-24,y,41,8,.16,.16,'metal')
    # Satellite receiver built of radial ribs and a shallow native sphere.
    add(g,'Receiver dish',(-60,22,10),(10,2.8,10),'white','sphere',rot=(.42,0,0))
    cyl(g,'Dish pedestal',-60,19.5,10,5,.8,'metal')
    beam(g,'Receiver feed',(-60,22,10),(-60,27,7),.24,'steel')
    # Helipad and aircraft east of the command building.
    g='Helipad'; x,z=48,47
    box(g,'Helipad plinth',x,.3,z,61,.6,61,'concreteDark')
    cyl(g,'Landing circle',x,.66,z,.08,51,'ochre')
    cyl(g,'Landing surface',x,.71,z,.08,49,'asphalt')
    h_marker(g,x,.78,z,2)
    for dx in (-30,30):
        for dz in (-30,30): box(g,'Landing beacon',x+dx,.9,z+dz,1.1,.6,1.1,'warm',light=dict(range=7,brightness=.8))
    sign(g,'Helipad warning','KEEP CLEAR  /  H-07',(48,2.6,15),(25,2,.25))
    helicopter(48,47)
    # Logistics, workshop, truck and supply clutter.
    container(76,0,-70,'olive')
    container(60,0,-70,'ochre')
    container(76,8.8,-70,'olive')
    container(30,0,-69,'olive',math.pi/2)
    truck(-62,-53)
    # A maintenance pavilion with open frontage and fitted service bays.
    g='Maintenance'; mx,mz=79,-6
    box(g,'Maintenance slab',mx,.35,mz,30,.7,32,'concreteDark')
    for dx in (-14,14):box(g,'Workshop side',mx+dx,6,mz,1.2,11.3,30,'olive')
    box(g,'Workshop back',mx,6,mz+14.5,29,11.3,1.2,'olive')
    box(g,'Workshop header',mx,10.5,mz-15,30,2.6,1.2,'oliveLight')
    box(g,'Workshop roof',mx,12.1,mz,33,.8,34,'steel')
    for dx in (-10,0,10):box(g,'Roof seam',mx+dx,12.55,mz,.15,.13,33,'metal')
    for dx in (-14.1,14.1):
        for zz in range(-20,9,2):box(g,'Workshop corrugation',mx+dx,6,zz,.12,11,.16,'oliveLight')
    sign(g,'Maintenance identification','MAINTENANCE  /  07',(mx,10.5,mz-15.7),(23,1.65,.15))
    box(g,'Workshop bench',mx,3,mz+10,24,.5,4,'bark')
    for dx in (-10,10):box(g,'Workbench foot',mx+dx,1.7,mz+10,.4,2.6,3,'steel')
    box(g,'Workshop fixture',mx,10.8,mz,12,.13,1,'warm',light=dict(range=22,brightness=1.8))
    for dx in (-9,-4,5):crate(g,mx+dx,0,mz+3,3)
    for dx in (-10,-7):barrel(g,mx+dx,mz-9)
    # Generator enclosure and service pipes fill the corridor behind command.
    g='Utilities'
    box(g,'Generator footing',4,.5,86,14,1,14,'concrete')
    box(g,'Field generator',4,3.3,86,10,5,8,'olive')
    for y in (2,2.8,3.6,4.4):box(g,'Cooling louvre',4,y,81.9,8,.3,.15,'steel')
    cyl(g,'Exhaust stack',8,6.5,88,5,.4,'steel')
    box(g,'Generator service panel',-1.1,3.5,85,.2,3,4,'steel')
    box(g,'Service indicator',-1.25,4.2,84,.1,.3,.4,'screen')
    for x,z,s in ((45,-84,3),(40,-84,3),(43,-80,3),(86,-48,4),(81,-48,4),(-23,77,4),(-29,77,4)):
        crate('Logistics',x,0,z,s)
    crate('Logistics',43,3,-82,2.8)
    for x in (37,40,43): barrel('Logistics',x,-90)
    # Small barracks pavilion, used to demonstrate another modular building style.
    g='Barracks'
    box(g,'Barracks floor',-53,.6,82,48,1.2,22,'concreteDark')
    box(g,'Barracks body',-53,5.8,82,46,10,20,'olive')
    for x in (-69,-53,-37):
        box(g,'Barracks window',x,6.8,71.9,8,3,.14,'glass')
        for dx in (-4.1,4.1): box(g,'Window trim',x+dx,6.8,71.7,.25,3.6,.2,'metal')
    box(g,'Barracks door',-76.1,4.8,82,.2,8,4.5,'steel')
    for yaw in (0,math.pi): add(g,'Pitched roof',(-53,12.5,82+(5 if yaw==0 else -5)),(49,4,10),'oliveLight','wedge',rot=(0,yaw,0))
    box(g,'Ridge cap',-53,14.55,82,49,.25,.6,'metal')
    sign(g,'Barracks identification','PERSONNEL',(-53,9.6,71.7),(18,1.5,.2))
    # Concrete lane dividers, drainage, steps, bollards and all the lived-in details.
    for x in (-80,-67,-54,15,28,41,54,67,80):
        if x<0: z=-27
        else: z=-22
        box('Roads','Parking line',x,.16,z,.15,.05,13,'white')
    for x in (-86,-73,-21,7,89):
        box('Roads','Jersey barrier',x,1.4,-15,9,2.8,1.7,'concrete')
        for dx in (-3,0,3): box('Roads','Barrier stripe',x+dx,1.6,-15.9,1.4,1.6,.05,'ochre',rot=(0,0,-.2))
    for x,z in ((-78,-30),(17,-25),(92,-23),(5,87),(-88,63),(90,67)):
        lamp('Lighting',x,z)
    for x,z in ((-87,-58),(15,84),(93,-62)):
        for dx in (-.8,.8): box('Details','Bench foot',x+dx,.7,z,.3,1.4,3,'steel')
        box('Details','Bench',x,1.6,z,5,.35,3.5,'bark')
    sandbags('Perimeter',89,11,3,24)
    # Central mast, windsock, directional board and safe player spawn.
    cyl('Details','Flag mast',5,15,4,30,.28,'metal')
    box('Details','Raven pennant',8,27,4,5.8,3.2,.07,'ochre')
    box('Details','Pennant stripe',8,27,3.95,4,.45,.04,'steel')
    sign('Details','Wayfinding','COMMAND  <\nHELIPAD  >\nLOGISTICS  >',(5,6,-16),(11,5,.2))
    box('Details','Wayfinding post',5,2.5,-16,.3,5,.3,'steel')
    box('Details','Spawn',0,.25,-143,6,.4,6,'asphalt',spawn=True,transparent=1)
    # Commissioned asset set remains anchored; no firearm/combat functionality.
    return dict(title='Raven Ridge',subtitle='Alpine military outpost',parts=parts,labels=labels,
                cameras=[
                    dict(name='Overview',pos=[205,155,-215],target=[0,9,3]),
                    dict(name='Checkpoint',pos=[43,19,-152],target=[-8,9,-92]),
                    dict(name='Command',pos=[14,34,-19],target=[-42,11,24]),
                    dict(name='Helipad',pos=[98,34,8],target=[46,6,47]),
                    dict(name='Logistics',pos=[95,25,-28],target=[55,5,-67]),
                    dict(name='Interior',pos=[-43,8,6],target=[-43,7,38]),
                ],stats=dict(parts=len(parts),models=len(set(p['group'] for p in parts)),seed=1819))

def matrix(p):
    if 'matrix' in p: return p['matrix']
    x,y,z=p['rot']; a,b=math.cos(x),math.sin(x); c,d=math.cos(y),math.sin(y); e,f=math.cos(z),math.sin(z)
    # Three.js / CFrame.fromEulerAnglesXYZ: Rx * Ry * Rz.
    return [c*e,-c*f,d,a*f+b*d*e,a*e-b*d*f,-b*c,b*f-a*d*e,b*e+a*d*f,a*c]

serial=0
def item(parent,cls,name):
    global serial; serial+=1
    el=ET.SubElement(parent,'Item',{'class':cls,'referent':f'RR{serial:06d}'})
    props=ET.SubElement(el,'Properties'); prop(props,'string','Name',name); return el,props
def prop(props,typ,name,value):
    el=ET.SubElement(props,typ,{'name':name}); el.text=str(value).lower() if isinstance(value,bool) else str(value); return el
def vec(props,name,v):
    el=ET.SubElement(props,'Vector3',{'name':name})
    for n,w in zip(('X','Y','Z'),v): ET.SubElement(el,n).text=str(w)
def color(props,name,hex):
    rgb=tuple(int(hex.lstrip('#')[i:i+2],16) for i in (0,2,4))
    el=ET.SubElement(props,'Color3',{'name':name})
    for n,w in zip(('R','G','B'),rgb): ET.SubElement(el,n).text=str(w/255)
def frame(props,name,pos,rotation):
    el=ET.SubElement(props,'CoordinateFrame',{'name':name})
    for n,w in zip(('X','Y','Z','R00','R01','R02','R10','R11','R12','R20','R21','R22'),pos+rotation): ET.SubElement(el,n).text=str(w)

materials={'SmoothPlastic':256,'Neon':288,'Concrete':816,'Metal':1088,'Glass':1568,'Grass':1280,'Ground':1360,'Asphalt':1376}

def export(scene):
    root=ET.Element('roblox',{'version':'4'}); ET.SubElement(root,'External').text='null'; ET.SubElement(root,'External').text='nil'
    ws,wp=item(root,'Workspace','Workspace'); prop(wp,'float','Gravity',196.2)
    cam,cp=item(ws,'Camera','Camera')
    pos=[205,155,-215];target=[0,9,3];back=[pos[i]-target[i] for i in range(3)];norm=math.sqrt(sum(v*v for v in back));back=[v/norm for v in back]
    right=[back[2],0,-back[0]];norm=math.sqrt(sum(v*v for v in right));right=[v/norm for v in right]
    up=[back[1]*right[2]-back[2]*right[1],back[2]*right[0]-back[0]*right[2],back[0]*right[1]-back[1]*right[0]]
    frame(cp,'CFrame',pos,[right[0],up[0],back[0],right[1],up[1],back[1],right[2],up[2],back[2]])
    prop(wp,'Ref','CurrentCamera',cam.attrib['referent'])
    model,mp=item(ws,'Model','RavenRidge'); folders={}; native=[]
    for g in sorted(set(p['group'] for p in scene['parts'])):
        folders[g]=item(model,'Model',g)[0]
    for p in scene['parts']:
        cls='SpawnLocation' if p.get('spawn') else 'WedgePart' if p['shape']=='wedge' else 'CornerWedgePart' if p['shape']=='corner' else 'Part'
        el,pr=item(folders[p['group']],cls,p['name']); native.append(el)
        prop(pr,'bool','Anchored',True); prop(pr,'bool','CanCollide',p.get('material') not in ('Neon','Glass') and not p.get('spawn',False))
        prop(pr,'bool','CanTouch',False); prop(pr,'bool','CastShadow',p.get('castShadow',p['material']!='Neon'))
        vec(pr,'size',p['size']); frame(pr,'CFrame',p['pos'],matrix(p))
        rgb=int(p['color'][1:],16); prop(pr,'Color3uint8','Color3uint8',0xff000000|rgb)
        prop(pr,'token','Material',materials[p['material']]); prop(pr,'float','Transparency',p.get('transparent',0))
        for surface in ('TopSurface','BottomSurface'): prop(pr,'token',surface,0)
        if cls in ('Part','SpawnLocation'): prop(pr,'token','shape',0 if p['shape']=='sphere' else 2 if p['shape']=='cylinder' else 1)
        if p.get('spawn'): prop(pr,'bool','Neutral',True); prop(pr,'float','Duration',0)
        if p.get('light'):
            le,lp=item(el,'PointLight','WarmLighting'); color(lp,'Color',p['color']); prop(lp,'float','Range',p['light']['range']); prop(lp,'float','Brightness',p['light']['brightness'])
        if p.get('prompt'):
            pe,pp=item(el,'ProximityPrompt','Interaction'); prop(pp,'string','ActionText',p['prompt']); prop(pp,'string','ObjectText','Raven Ridge')
            prop(pp,'float','HoldDuration',.35); prop(pp,'float','MaxActivationDistance',10); prop(pp,'bool','RequiresLineOfSight',False)
        if p.get('dynamic'):
            ve,vp=item(el,'StringValue','Mechanism'); prop(vp,'string','Value',p['dynamic'])
    for label in scene['labels']:
        el=native[label['part']]; se,sp=item(el,'SurfaceGui','Identification'); prop(sp,'token','Face',5 if label['face']=='Front' else 1)
        prop(sp,'float','PixelsPerStud',38); prop(sp,'token','SizingMode',1)
        te,tp=item(se,'TextLabel','Text'); ud=ET.SubElement(tp,'UDim2',{'name':'Size'})
        for n,v in [('XS',1),('XO',0),('YS',1),('YO',0)]: ET.SubElement(ud,n).text=str(v)
        prop(tp,'string','Text',label['text']); prop(tp,'float','BackgroundTransparency',1); color(tp,'TextColor3',label['ink'])
        prop(tp,'bool','TextScaled',True); prop(tp,'bool','TextWrapped',True); prop(tp,'token','Font',4)
    lighting,lp=item(root,'Lighting','Lighting')
    prop(lp,'float','ClockTime',16.7); prop(lp,'float','Brightness',2.5); prop(lp,'bool','GlobalShadows',True)
    color(lp,'Ambient','#606c6c'); color(lp,'OutdoorAmbient','#829b9c')
    prop(lp,'float','EnvironmentDiffuseScale',.45); prop(lp,'float','EnvironmentSpecularScale',.65)
    atm,ap=item(lighting,'Atmosphere','AlpineHaze'); prop(ap,'float','Density',.29); prop(ap,'float','Offset',.15)
    color(ap,'Color','#c6d4cd'); color(ap,'Decay','#858f82'); prop(ap,'float','Haze',1.2); prop(ap,'float','Glare',.12)
    cc,ccp=item(lighting,'ColorCorrectionEffect','FilmGrade'); prop(ccp,'float','Contrast',.1); prop(ccp,'float','Saturation',-.12); color(ccp,'TintColor','#fff3dc')
    be,bp=item(lighting,'BloomEffect','PracticalBloom'); prop(bp,'float','Intensity',.16); prop(bp,'float','Size',20); prop(bp,'float','Threshold',1.5)
    ss,ssp=item(root,'ServerScriptService','ServerScriptService')
    se,sp=item(ss,'Script','OutpostInteractions'); prop(sp,'ProtectedString','Source',(ROOT/'src/Outpost.server.luau').read_text())
    starter,stp=item(root,'StarterPlayer','StarterPlayer'); prop(stp,'float','CameraMaxZoomDistance',350)
    sps,spsp=item(starter,'StarterPlayerScripts','StarterPlayerScripts')
    se,sp=item(sps,'LocalScript','PortfolioTour'); prop(sp,'ProtectedString','Source',(ROOT/'src/Tour.client.luau').read_text())
    rs,rp=item(root,'ReplicatedStorage','ReplicatedStorage')
    me,mp=item(rs,'ModuleScript','TourCameras'); prop(mp,'ProtectedString','Source','return '+luau(scene['cameras']))
    ET.indent(root)
    (ROOT/'build').mkdir(exist_ok=True)
    ET.ElementTree(root).write(ROOT/'build/RavenRidge.rbxlx',encoding='utf-8',xml_declaration=False)

def luau(v):
    if isinstance(v,str): return json.dumps(v)
    if isinstance(v,list): return '{'+','.join(luau(x) for x in v)+'}'
    if isinstance(v,dict): return '{'+','.join(k+'='+luau(w) for k,w in v.items())+'}'
    return str(v)

if __name__=='__main__':
    scene=build(); export(scene)
    (ROOT/'viewer/scene.json').write_text(json.dumps(scene,separators=(',',':')))
    (ROOT/'build/manifest.json').write_text(json.dumps(dict(stats=scene['stats'],groups=dict(Counter(p['group'] for p in parts))),indent=2)+'\n')
    print(json.dumps(scene['stats']))
