// Screenshots an HTML file at phone width: node tools/preview_mobile.js out/issue-NN/preview.html shot.png
const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:390,height:800}});
await p.goto('file://'+require('path').resolve(process.argv[2]));await p.waitForTimeout(1500);await p.screenshot({path:process.argv[3],fullPage:true});await b.close();})();
