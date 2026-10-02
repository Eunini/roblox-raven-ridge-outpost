/** Actual deterministic browser recording. Every frame renders the shared
 * authored geometry at an exact camera time. No generated video or still pan. */
import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import { spawn } from 'node:child_process';
import path from 'node:path';

const executablePath=process.env.CHROMIUM_PATH;
const browser=await chromium.launch({headless:true,...(executablePath?{executablePath}:{}),args:['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader']});
const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
const errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('404'))errors.push(m.text());});
await page.goto((process.env.DEMO_URL||'http://127.0.0.1:4317/')+'?record=1',{waitUntil:'networkidle',timeout:90000});
await page.waitForFunction(()=>window.raven?.ready,{timeout:90000});
const duration=await page.evaluate(()=>window.raven.duration);
const fps=24;const frames=Math.ceil(duration*fps);
await page.evaluate(()=>{
  const out=document.createElement('canvas');out.width=1920;out.height=1080;
  const ctx=out.getContext('2d',{alpha:false});
  window.captureRavenFrame=time=>{
    window.raven.renderAt(time);
    ctx.drawImage(window.raven.renderer.domElement,0,0,1920,1080);
    const gradient=ctx.createLinearGradient(0,1080,0,0);
    gradient.addColorStop(0,'rgba(12,24,19,.80)');gradient.addColorStop(.26,'rgba(12,24,19,0)');
    gradient.addColorStop(.85,'rgba(12,24,19,0)');gradient.addColorStop(1,'rgba(12,24,19,.42)');
    ctx.fillStyle=gradient;ctx.fillRect(0,0,1920,1080);
    ctx.fillStyle='#f0f1e7';ctx.textBaseline='top';ctx.font='13px Arial';ctx.letterSpacing='4px';ctx.fillText('RAVEN RIDGE',56,40);
    ctx.textAlign='right';ctx.font='10px Arial';ctx.letterSpacing='2px';ctx.fillStyle='#d2ded1';ctx.fillText('ROBLOX ENVIRONMENT PORTFOLIO',1864,43);
    ctx.textAlign='left';ctx.fillStyle='#f0f1e7';ctx.font='600 62px Barlow, Arial';ctx.letterSpacing='1px';
    ctx.fillText(document.querySelector('#film-heading').textContent,56,869);
    ctx.font='14px Arial';ctx.letterSpacing='.4px';ctx.fillStyle='#d8e2d4';ctx.fillText(document.querySelector('#film-subtitle').textContent,56,947);
    ctx.font='10px Arial';ctx.letterSpacing='.5px';ctx.fillStyle='#bdcbb9';ctx.fillText('Browser render of the authored Roblox geometry',56,1029);
    ctx.fillStyle='#e5bc77';ctx.fillRect(0,1077,time/window.raven.duration*1920,3);
    return out.toDataURL('image/jpeg',.93).split(',')[1];
  };
});
await fs.mkdir('media',{recursive:true});
const output=path.resolve('media/RavenRidge-Walkthrough.mp4');
const ffmpeg=spawn('ffmpeg',['-y','-hide_banner','-loglevel','warning','-f','image2pipe','-vcodec','mjpeg','-framerate',String(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',output],{stdio:['pipe','inherit','inherit']});
const finished=new Promise((resolve,reject)=>{ffmpeg.on('error',reject);ffmpeg.on('exit',c=>c===0?resolve():reject(new Error(`ffmpeg exited ${c}`)));});
const started=Date.now();
for(let i=0;i<frames;i++){
  const jpeg=Buffer.from(await page.evaluate(t=>window.captureRavenFrame(t),i/fps),'base64');
  if([0,600,960].includes(i))await fs.writeFile(`media/film-frame-${i}.jpg`,jpeg);
  if(!ffmpeg.stdin.write(jpeg))await new Promise(resolve=>ffmpeg.stdin.once('drain',resolve));
  if(i%60===0)console.log(`Recording ${Math.round(i/frames*100)}% | ${i}/${frames} | ${Math.round((Date.now()-started)/1000)}s elapsed`);
}
ffmpeg.stdin.end();await finished;
await fs.writeFile('media/recording-evidence.json',JSON.stringify({format:'Actual WebGL browser recording of the authored Roblox geometry',resolution:[1920,1080],fps,duration,frames,errors,geometry:await page.evaluate(()=>window.raven.data.stats)},null,2)+'\n');
await browser.close();
if(errors.length)throw new Error(errors.join('\n'));
console.log(`Recorded ${duration}s / ${fps}fps / 1920x1080: ${output}`);
