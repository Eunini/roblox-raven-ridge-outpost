import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),args:['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader']});
const page=await browser.newPage({viewport:{width:1600,height:900},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
await page.goto('http://127.0.0.1:4317/?record=1',{waitUntil:'networkidle',timeout:90000});
await page.waitForFunction(()=>window.raven?.ready,{timeout:90000});
await fs.mkdir('media',{recursive:true});
for(const [name,time] of [['overview',3],['checkpoint',11],['command',18],['helipad',25],['logistics',32],['interior',39],['dusk',46]]){
  await page.evaluate(t=>window.raven.renderAt(t),time);
  await page.screenshot({path:path.resolve(`media/${name}.jpg`),type:'jpeg',quality:90});
}
console.log(JSON.stringify({stats:await page.evaluate(()=>window.raven.stats()),errors},null,2));
await browser.close();
