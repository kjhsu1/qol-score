import * as THREE from './vendor/three.module.min.js';

// A fully modeled, jointed little Boyacki. No external models or network assets.
const stage=document.createElement('div');stage.className='mascot-stage';stage.setAttribute('aria-label','Animated 3D Boyacki walking around the hideout');document.body.append(stage);
const caption=document.createElement('span');caption.className='mascot-caption';caption.textContent='ボヤッキー 巡回中';stage.append(caption);
let paused=document.body.classList.contains('motion-off'),celebrateUntil=0,forceRender=true;
window.addEventListener('qol-motion',e=>{paused=e.detail.paused;forceRender=true;});
window.addEventListener('qol-saved',()=>celebrateUntil=performance.now()+4500);
try{
const renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'low-power'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setClearColor(0,0);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.3;stage.prepend(renderer.domElement);
const scene=new THREE.Scene();const camera=new THREE.PerspectiveCamera(30,1,.1,100);camera.position.set(0,2.5,9);camera.lookAt(0,1.5,0);
scene.add(new THREE.HemisphereLight(0xffecd0,0x304830,2.1));const key=new THREE.DirectionalLight(0xffcf81,4);key.position.set(-3,6,5);scene.add(key);const rim=new THREE.DirectionalLight(0xc4e7a1,3);rim.position.set(4,2,-3);scene.add(rim);
const mat=(color,roughness=.55,metalness=.03)=>new THREE.MeshStandardMaterial({color,roughness,metalness});
const skin=mat('#e6b174'),noseMat=mat('#e3a16b'),green=mat('#35663c'),darkGreen=mat('#173c2b'),maskMat=mat('#2c7b4d',.35),cream=mat('#ecdfb1'),black=mat('#30231a'),white=mat('#faf0cf'),purple=mat('#52385a'),bootMat=mat('#382e28'),gold=mat('#d5ad52',.35,.5),lens=mat('#bbcaaa',.2,.3);
function ellipsoid(parent,material,x,y,z,sx,sy,sz){const mesh=new THREE.Mesh(new THREE.SphereGeometry(1,24,18),material);mesh.position.set(x,y,z);mesh.scale.set(sx,sy,sz);parent.add(mesh);return mesh;}
function box(parent,material,x,y,z,sx,sy,sz){const mesh=new THREE.Mesh(new THREE.BoxGeometry(sx,sy,sz),material);mesh.position.set(x,y,z);parent.add(mesh);return mesh;}
function cone(parent,material,x,y,z,radius,height,rx=0,rz=0){const mesh=new THREE.Mesh(new THREE.ConeGeometry(radius,height,24),material);mesh.position.set(x,y,z);mesh.rotation.set(rx,0,rz);parent.add(mesh);return mesh;}
const actor=new THREE.Group();scene.add(actor);const body=new THREE.Group();actor.add(body);
ellipsoid(body,green,0,1.1,0,.28,.36,.2);ellipsoid(body,cream,0,1.35,.02,.31,.09,.23);box(body,darkGreen,0,.93,.02,.51,.13,.35);box(body,gold,0,.93,.213,.11,.1,.03);
const head=new THREE.Group();head.position.y=1.76;body.add(head);
ellipsoid(head,skin,0,0,.01,.3,.38,.27);ellipsoid(head,skin,0,-.22,.13,.2,.21,.2);
// Boyacki's unmistakable long nose, eye mask, moustache and buck teeth.
ellipsoid(head,maskMat,0,.08,.205,.32,.155,.12);
ellipsoid(head,white,-.13,.08,.297,.095,.085,.035);ellipsoid(head,white,.13,.08,.297,.095,.085,.035);
ellipsoid(head,black,-.115,.067,.327,.035,.046,.02);ellipsoid(head,black,.143,.067,.327,.035,.046,.02);
const nose=ellipsoid(head,noseMat,0,-.03,.42,.09,.11,.29);nose.rotation.x=.28;ellipsoid(head,skin,0,-.115,.67,.095,.075,.09);
const brow1=box(head,darkGreen,-.14,.19,.3,.19,.04,.04);brow1.rotation.z=-.22;const brow2=box(head,darkGreen,.14,.19,.3,.19,.04,.04);brow2.rotation.z=.22;
ellipsoid(head,black,0,-.25,.29,.13,.055,.025);box(head,white,-.047,-.28,.325,.075,.12,.04);box(head,white,.047,-.28,.325,.075,.12,.04);
const moustache1=ellipsoid(head,black,-.115,-.19,.34,.15,.035,.035);moustache1.rotation.z=.28;const moustache2=ellipsoid(head,black,.115,-.19,.34,.15,.035,.035);moustache2.rotation.z=-.28;
ellipsoid(head,skin,-.3,0,.02,.075,.12,.055);ellipsoid(head,skin,.3,0,.02,.075,.12,.055);
// Soft engineer's cap with round brass goggles perched on top.
ellipsoid(head,green,0,.28,-.03,.35,.2,.29);ellipsoid(head,darkGreen,0,.23,.22,.37,.055,.14);ellipsoid(head,purple,-.26,.16,-.07,.14,.22,.16);ellipsoid(head,purple,.26,.16,-.07,.14,.22,.16);
for(const x of [-.14,.14]){const ring=new THREE.Mesh(new THREE.TorusGeometry(.085,.022,10,28),gold);ring.position.set(x,.37,.23);ring.rotation.x=-.35;head.add(ring);ellipsoid(head,lens,x,.37,.231,.067,.064,.015);}box(head,gold,0,.37,.23,.08,.025,.03);
cone(head,darkGreen,-.29,.39,-.04,.08,.25,0,.45);cone(head,darkGreen,.29,.39,-.04,.08,.25,0,-.45);
const legs=[],arms=[];
for(const side of [-1,1]){
 const leg=new THREE.Group();leg.position.set(side*.15,.88,0);body.add(leg);ellipsoid(leg,green,0,-.19,0,.11,.24,.11);const shin=new THREE.Group();shin.position.y=-.36;leg.add(shin);ellipsoid(shin,darkGreen,0,-.13,0,.095,.19,.1);ellipsoid(shin,bootMat,0,-.29,.09,.135,.12,.22);box(shin,cream,0,-.21,.02,.18,.05,.17);legs.push({leg,shin});
 const arm=new THREE.Group();arm.position.set(side*.27,1.32,0);body.add(arm);ellipsoid(arm,green,side*.04,-.17,0,.095,.22,.105);const hand=new THREE.Group();hand.position.set(side*.05,-.39,.015);arm.add(hand);ellipsoid(hand,skin,0,0,0,.095,.105,.08);ellipsoid(hand,skin,-side*.06,.02,.055,.04,.06,.04);arms.push(arm);
}
// Tiny tool pouch and spanner at his belt.
box(body,bootMat,.27,.96,-.02,.14,.2,.12);const tool=box(body,gold,.32,1.1,.035,.035,.26,.025);tool.rotation.z=-.2;
const shadowTexture=(()=>{const canvas=document.createElement('canvas');canvas.width=128;canvas.height=64;const ctx=canvas.getContext('2d');const g=ctx.createRadialGradient(64,32,2,64,32,55);g.addColorStop(0,'rgba(0,0,0,.5)');g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.fillRect(0,0,128,64);return new THREE.CanvasTexture(canvas);})();
const shadow=new THREE.Mesh(new THREE.PlaneGeometry(1.3,.5),new THREE.MeshBasicMaterial({map:shadowTexture,transparent:true,depthWrite:false}));shadow.rotation.x=-Math.PI/2;shadow.position.y=.025;actor.add(shadow);
let width=0,clock=0,last=performance.now(),hasRendered=false;
function size(){width=stage.clientWidth;renderer.setSize(width,stage.clientHeight);camera.aspect=width/stage.clientHeight;camera.updateProjectionMatrix();hasRendered=false;}new ResizeObserver(size).observe(stage);size();
function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-last)/1000,.05);last=now;if(document.hidden)return;if(paused&&hasRendered&&!forceRender)return;if(!paused)clock+=dt;
 const range=Math.max(1,camera.aspect*2.3-1),cycle=clock*.22,position=Math.sin(cycle)*range;
 actor.position.set(position,.03,0);actor.rotation.y=Math.cos(cycle)>0?.75:-.75;
 const gait=clock*6;body.position.y=Math.abs(Math.sin(gait))*.035;
 legs.forEach(({leg,shin},i)=>{leg.rotation.x=Math.sin(gait+i*Math.PI)*.48;shin.rotation.x=Math.max(0,-Math.sin(gait+i*Math.PI))*.35;});
 arms.forEach((arm,i)=>{arm.rotation.x=-Math.sin(gait+i*Math.PI)*.35;arm.rotation.z=(i===0?.08:-.08);});head.rotation.y=Math.sin(clock*.8)*.12;
 if(now<celebrateUntil){actor.rotation.y=0;arms[1].rotation.z=-1.8+Math.sin(clock*15)*.3;head.rotation.z=Math.sin(clock*7)*.08;body.position.y=.08+Math.abs(Math.sin(clock*8))*.1;}else head.rotation.z=0;
 if(paused){legs.forEach(({leg,shin})=>{leg.rotation.x=0;shin.rotation.x=0;});arms.forEach(a=>a.rotation.x=0);actor.position.x=range*.6;actor.rotation.y=-.5;}
 renderer.render(scene,camera);hasRendered=true;forceRender=false;document.body.dataset.mascot='ready';
}requestAnimationFrame(animate);
renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();caption.textContent='ボヤッキー 休憩中';});
}catch(error){stage.classList.add('no-webgl');stage.replaceChildren();const note=document.createElement('span');note.className='mascot-fallback';note.textContent='Boyacki is taking a break — 3D graphics unavailable';stage.append(note);document.body.dataset.mascot='unavailable';console.warn('3D mascot unavailable:',error);}
