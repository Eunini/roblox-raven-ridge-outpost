import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const params = new URLSearchParams(location.search);
const manual = params.has('record');
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const descriptions = ['A complete alpine outpost','Fortified approach and working barrier','Brutalist command bunker and communications','Custom rotorcraft and landing infrastructure','Corrugated containers, field supplies, and motor pool','Operations room, briefing map, and workstation bays'];
const shots = [
  {duration:8,from:[218,150,-212],to:[159,115,-162],look:[-6,8,4],name:'RAVEN RIDGE',sub:'An original alpine military outpost for Roblox'},
  {duration:7,from:[33,15,-151],to:[5,12,-133],look:[-9,8,-96],name:'THE CHECKPOINT',sub:'Fortified approach, observation towers, and a working barrier'},
  {duration:7,from:[17,30,-25],to:[-12,25,-22],look:[-44,13,24],name:'COMMAND & CONTROL',sub:'A modular concrete bunker with rooftop communications'},
  {duration:7,from:[103,30,16],to:[91,24,76],look:[48,7,47],name:'THE LANDING ZONE',sub:'An original rotorcraft, painted helipad, and practical lighting'},
  {duration:6,from:[101,25,-31],to:[60,17,-31],look:[64,7,-72],name:'FIELD LOGISTICS',sub:'Stacked containers, corrugated metal, and supply-yard detail'},
  {duration:7,from:[-43,8,6],to:[-39,8,20],look:[-43,7,41],name:'INSIDE COMMAND',sub:'An explorable operations room, tactical map, and monitor bays'},
  {duration:8,from:[-176,123,-181],to:[-133,108,-154],look:[0,9,8],name:'BUILT TO BE EXPLORED',sub:'Editable Roblox parts. Studio place and full source included.'},
];
const duration = shots.reduce((sum,s)=>sum+s.duration,0);
const scene = new THREE.Scene();
scene.background = new THREE.Color('#b3c7c6');
scene.fog = new THREE.FogExp2('#b3c7c6', .00105);
const camera = new THREE.PerspectiveCamera(47,innerWidth/innerHeight,.2,2200);
const renderer = new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:manual,powerPreference:'high-performance'});
renderer.setSize(innerWidth,innerHeight);
renderer.setPixelRatio(manual ? .65 : Math.min(devicePixelRatio,1.5));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false;
renderer.shadowMap.needsUpdate = true;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.02;
document.querySelector('#stage').appendChild(renderer.domElement);
const controls = new OrbitControls(camera,renderer.domElement);
controls.enableDamping = !manual;
controls.dampingFactor = .06;
controls.minDistance = 8;
controls.maxDistance = 480;
controls.maxPolarAngle = Math.PI*.49;
controls.target.set(-6,8,4);
camera.position.set(218,150,-212);
controls.update();

const hemisphere = new THREE.HemisphereLight('#dae8e4','#6e7258',1.55);
scene.add(hemisphere);
const sun = new THREE.DirectionalLight('#ffddb0',2.8);
sun.position.set(-170,190,-100);
sun.castShadow = true;
sun.shadow.mapSize.set(2048,2048);
Object.assign(sun.shadow.camera,{left:-172,right:172,top:172,bottom:-172,near:1,far:570});
sun.shadow.bias=-.0002;
sun.shadow.normalBias=.24;
sun.shadow.camera.updateProjectionMatrix();
scene.add(sun);
const fill = new THREE.DirectionalLight('#a6c2cd',.35); fill.position.set(140,85,80);scene.add(fill);
const sky = new THREE.Mesh(new THREE.SphereGeometry(1400,32,16),new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,
  uniforms:{top:{value:new THREE.Color('#799fad')},bottom:{value:new THREE.Color('#c6d5d0')}},
  vertexShader:'varying vec3 vPos; void main(){vPos=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
  fragmentShader:'varying vec3 vPos; uniform vec3 top;uniform vec3 bottom;void main(){float h=pow(max(normalize(vPos).y,0.0),0.65);gl_FragColor=vec4(mix(bottom,top,h),1.0);}'
}));scene.add(sky);
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene,camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth,innerHeight),.15,.5,1.1);
composer.addPass(bloom);composer.addPass(new OutputPass());

function polyGeometry(kind){
  // Native Roblox WedgePart and CornerWedgePart, in their documented local axes.
  const vertices=kind==='corner' ? [
    [-.5,-.5,-.5],[.5,-.5,-.5],[.5,-.5,.5],[-.5,-.5,.5],[-.5,.5,.5]
  ] : [
    [-.5,-.5,-.5],[.5,-.5,-.5],[.5,-.5,.5],[-.5,-.5,.5],[-.5,.5,.5],[.5,.5,.5]
  ];
  const triangles=kind==='corner' ? [[0,2,1],[0,3,2],[0,1,4],[1,2,4],[2,3,4],[3,0,4]] : [[0,2,1],[0,3,2],[0,1,5],[0,5,4],[3,4,5],[3,5,2],[0,4,3],[1,2,5]];
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(triangles.flatMap(t=>t.flatMap(i=>vertices[i])),3));
  g.computeVertexNormals();return g;
}
const cylinder=new THREE.CylinderGeometry(.5,.5,1,20);cylinder.rotateZ(-Math.PI/2);
const geometries={box:new THREE.BoxGeometry(1,1,1),sphere:new THREE.SphereGeometry(.5,18,12),cylinder,wedge:polyGeometry('wedge'),corner:polyGeometry('corner')};
const materials=new Map(), dynamic={gate:[],bunker:[]}, practical=[];
let data, tourStart=0,playing=false,night=false,gateOpen=false,bunkerOpen=false,transition=null;
const temp = new THREE.Object3D();

function material(p){
  const key=`${p.color}/${p.material}/${p.transparent||0}`;
  if(materials.has(key))return materials.get(key);
  const m=new THREE.MeshStandardMaterial({color:p.color,roughness:p.material==='Metal'?.52:.91,
    metalness:p.material==='Metal'?.38:0,transparent:!!p.transparent,opacity:1-(p.transparent||0)});
  if(p.material==='Neon'){m.emissive.set(p.color);m.emissiveIntensity=1.8;}
  if(p.material==='Glass'){m.roughness=.15;m.metalness=.45;}
  if(['Concrete','Asphalt','Metal'].includes(p.material)){
    m.onBeforeCompile=shader=>{
      shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 vWorldPoint;');
      shader.vertexShader=shader.vertexShader.replace('#include <worldpos_vertex>',`#include <worldpos_vertex>
        vec4 rrPos=vec4(transformed,1.0);
        #ifdef USE_INSTANCING
        rrPos=instanceMatrix*rrPos;
        #endif
        vWorldPoint=(modelMatrix*rrPos).xyz;`);
      shader.fragmentShader=shader.fragmentShader.replace('#include <common>',`#include <common>
        varying vec3 vWorldPoint;
        float rrNoise(vec3 p){return fract(sin(dot(floor(p),vec3(12.9898,78.233,39.425)))*43758.5453);}`);
      shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
        float rrGrain=rrNoise(vWorldPoint*5.0);
        float rrMottle=rrNoise(vWorldPoint*0.42);
        diffuseColor.rgb *= 0.91 + rrGrain*0.10 + rrMottle*0.08;`);
    };
  }
  materials.set(key,m);return m;
}
function setTransform(o,p){
  o.position.fromArray(p.pos);o.scale.fromArray(p.size);
  if(p.matrix){const a=p.matrix;const m=new THREE.Matrix4().set(a[0],a[1],a[2],0,a[3],a[4],a[5],0,a[6],a[7],a[8],0,0,0,0,1);o.quaternion.setFromRotationMatrix(m);}
  else o.rotation.fromArray([...p.rot,'XYZ']);o.updateMatrix();
}
function labelTexture(label,p){
  const c=document.createElement('canvas');c.width=1024;c.height=Math.max(128,Math.round(1024*p.size[1]/p.size[0]));
  const ctx=c.getContext('2d');ctx.fillStyle=label.ink;ctx.textAlign='center';ctx.textBaseline='middle';
  const lines=label.text.split('\n');const max=lines.reduce((a,b)=>a.length>b.length?a:b,'');
  let font=Math.min(c.height/(lines.length*1.3),c.width/max.length*1.48);ctx.font=`600 ${font}px Barlow, Arial`;
  lines.forEach((line,i)=>ctx.fillText(line,c.width/2,c.height/2+(i-(lines.length-1)/2)*font*1.22,c.width*.92));
  const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;tex.anisotropy=4;return tex;
}
async function load(){
  try{
    const response=await fetch(new URL('./scene.json',import.meta.url));if(!response.ok)throw new Error('Scene could not be loaded.');data=await response.json();
    await document.fonts.ready;
    const batches=new Map();
    data.parts.forEach((p,i)=>{
      if(p.transparent===1)return;
      if(p.dynamic){const m=new THREE.Mesh(geometries[p.shape],material(p));setTransform(m,p);m.castShadow=true;m.receiveShadow=true;dynamic[p.dynamic].push({mesh:m,origin:m.position.clone()});scene.add(m);return;}
      const key=p.shape+'/'+p.color+'/'+p.material+'/'+(p.transparent||0);
      if(!batches.has(key))batches.set(key,[]);batches.get(key).push(p);
    });
    for(const batch of batches.values()){
      const p=batch[0],m=new THREE.InstancedMesh(geometries[p.shape],material(p),batch.length);
      batch.forEach((part,i)=>{setTransform(temp,part);m.setMatrixAt(i,temp.matrix);});
      m.castShadow=p.castShadow??(p.material!=='Neon'&&p.material!=='Glass');m.receiveShadow=p.group!=='Mountains';
      m.computeBoundingSphere();scene.add(m);
    }
    for(const label of data.labels){
      const p=data.parts[label.part];
      const mesh=new THREE.Mesh(new THREE.PlaneGeometry(p.size[0]*.95,p.size[1]*.88),new THREE.MeshBasicMaterial({map:labelTexture(label,p),transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1}));
      mesh.position.fromArray(p.pos);mesh.position.z-=p.size[2]/2+.04;
      mesh.rotation.y=Math.PI;scene.add(mesh);
    }
    // Keep every emissive fixture; prioritize interior point lights in the web
    // preview. The Studio export contains the full native lighting rig.
    const lightParts=data.parts.filter(p=>p.light);
    const focusedLights=[...lightParts.filter(p=>p.group==='Command'||p.group==='Maintenance'),...lightParts.filter(p=>p.group==='Lighting').slice(0,2)];
    focusedLights.forEach(p=>{
      const light=new THREE.PointLight(p.color,p.light.brightness*11,p.light.range,1.5);
      light.position.fromArray(p.pos);scene.add(light);practical.push(light);
    });
    data.cameras.forEach((shot,i)=>{
      const b=document.createElement('button');b.textContent=shot.name;b.setAttribute('aria-pressed','false');
      b.addEventListener('click',()=>view(i));document.querySelector('#views').appendChild(b);
    });
    document.querySelector('#loading').remove();
    window.raven={ready:true,data,duration,renderAt,view,renderer,camera,controls,setNight,setGate,setBunker,
      state:()=>({night,gateOpen,bunkerOpen,gateY:dynamic.gate[0].mesh.position.y,doorX:dynamic.bunker[0].mesh.position.x}),
      stats:()=>({...data.stats,instancedBatches:batches.size,previewPointLights:practical.length})};
    if(manual||params.has('cinema')){document.body.classList.add('cinema');renderAt(0);}
    if(params.has('cinema')&&!manual)startTour();
    if(!manual)animate();
    else composer.render();
  }catch(error){document.querySelector('#loading')?.remove();const el=document.querySelector('#error');el.hidden=false;el.textContent='The 3D preview could not start. Try a browser with WebGL enabled, or download the Roblox Studio place from GitHub.';console.error(error);}
}
function setNight(value){
  night=value;
  scene.fog.color.set(value?'#495d64':'#b3c7c6');scene.fog.density=value?.0017:.00105;
  sky.material.uniforms.top.value.set(value?'#213844':'#799fad');sky.material.uniforms.bottom.value.set(value?'#748486':'#c6d5d0');
  sun.color.set(value?'#abb9d0':'#ffddb0');sun.intensity=value?.7:2.8;
  hemisphere.intensity=value?.9:1.55;renderer.toneMappingExposure=value?1.02:1.02;
  bloom.strength=value?.28:.15;
  practical.forEach(l=>l.intensity=value?l.userData.base||18:10);
  document.querySelector('#lighting').textContent=value?'Daylight':'Dusk lighting';
}
function setGate(value){if(gateOpen!==value)renderer.shadowMap.needsUpdate=true;gateOpen=value;dynamic.gate.forEach(d=>d.mesh.position.copy(d.origin).add(new THREE.Vector3(0,value*8,0)));document.querySelector('#gate').textContent=value?'Close gate':'Open gate';}
function setBunker(value){if(bunkerOpen!==value)renderer.shadowMap.needsUpdate=true;bunkerOpen=value;dynamic.bunker.forEach(d=>d.mesh.position.copy(d.origin).add(new THREE.Vector3(value*8.5,0,0)));document.querySelector('#bunker').textContent=value?'Close bunker':'Open bunker';}
function view(index){
  stopTour();document.body.classList.add('exploring');
  const shot=data.cameras[index];
  document.querySelectorAll('#views button').forEach((b,i)=>b.setAttribute('aria-pressed',String(index===i)));
  document.querySelector('#view-name').textContent=shot.name;document.querySelector('#view-description').textContent=descriptions[index];
  if(index===5)setBunker(true);
  if(reduced||manual){camera.position.fromArray(shot.pos);controls.target.fromArray(shot.target);controls.update();}
  else transition={start:performance.now(),from:camera.position.clone(),to:new THREE.Vector3(...shot.pos),targetFrom:controls.target.clone(),targetTo:new THREE.Vector3(...shot.target)};
}
function renderAt(time){
  document.body.classList.add('cinema');transition=null;
  let elapsed=0,shot=shots.at(-1),local=1;
  for(const s of shots){if(time<elapsed+s.duration){shot=s;local=(time-elapsed)/s.duration;break;}elapsed+=s.duration;}
  local=THREE.MathUtils.clamp(local,0,1);const f=local*local*(3-2*local);
  camera.position.lerpVectors(new THREE.Vector3(...shot.from),new THREE.Vector3(...shot.to),f);
  controls.target.fromArray(shot.look);camera.lookAt(controls.target);
  document.querySelector('#film-heading').textContent=shot.name;document.querySelector('#film-subtitle').textContent=shot.sub;
  document.documentElement.style.setProperty('--progress',`${time/duration*100}%`);
  if(time>=8&&time<15)setGate(Math.min(1,Math.max(0,(time-10)/1.4)));
  if(time>=35)setBunker(true);
  setNight(time>=42);
  if(manual)renderer.render(scene,camera);else composer.render();
}
function startTour(){playing=true;transition=null;tourStart=performance.now();controls.enabled=false;document.body.classList.add('cinema');}
function stopTour(){playing=false;controls.enabled=true;document.body.classList.remove('cinema');}
document.querySelector('#tour').addEventListener('click',startTour);
document.querySelector('#lighting').addEventListener('click',()=>setNight(!night));
document.querySelector('#gate').addEventListener('click',()=>setGate(!gateOpen));
document.querySelector('#bunker').addEventListener('click',()=>setBunker(!bunkerOpen));
addEventListener('keydown',event=>{if(event.key==='Escape'){stopTour();document.body.classList.add('exploring');}if(event.key.toLowerCase()==='l')setNight(!night);});
controls.addEventListener('start',()=>{transition=null;if(!playing)document.body.classList.add('exploring');});
function animate(){
  requestAnimationFrame(animate);
  if(playing){const t=(performance.now()-tourStart)/1000;if(t>duration){stopTour();document.body.classList.add('exploring');}else{renderAt(t);return;}}
  if(transition){const t=Math.min(1,(performance.now()-transition.start)/1400);const ease=t*t*(3-2*t);
    camera.position.lerpVectors(transition.from,transition.to,ease);controls.target.lerpVectors(transition.targetFrom,transition.targetTo,ease);if(t===1)transition=null;}
  controls.update();composer.render();
}
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);composer.setSize(innerWidth,innerHeight);});
load();
