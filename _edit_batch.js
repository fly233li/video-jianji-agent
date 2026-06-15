const fs = require('fs');
const path = 'E:/AI_jianji/video-edit-agent/frontend/dist/assets/BatchView-dQXGWYWS.js';
let content = fs.readFileSync(path, 'utf-8');

// ============================================================
// 1. Add regenerateScript function after synthesizeScript (Ee)
// ============================================================
// The Ee function ends with: D.info(t.length>80?t.slice(0,80)+`...`:t)}
// Insert async function Ne after it, before return(e,r)=>{

const oldEnd = `D.info(t.length>80?t.slice(0,80)+\`...\`:t)}`;

const newFunc = `D.info(t.length>80?t.slice(0,80)+\`...\`:t)}async function Ne(e){try{let t=await fetch(\`/api/batch/regenerate-script\`,{method:\`POST\`,headers:{"Content-Type":\`application/json\`},body:JSON.stringify({selling_points:e.selling_points,product_name:P.value,usage_scenario:F.value,video_index:e.video_index})});let n=await t.json();if(!t.ok)throw new Error(n.detail||\`失败\`);let r=z.value.findIndex(t=>t.video_index===e.video_index);if(r>=0)z.value[r]=n;D.success(\`第 \${e.video_index} 条已重新生成\`)}catch(e){D.error(e.message||\`重新生成失败\`)}}`;

if (content.includes(oldEnd)) {
    content = content.replace(oldEnd, newFunc);
    console.log('1. Added regenerateScript function');
} else {
    console.log('1. ERROR: synthEnd not found');
    process.exit(1);
}

// ============================================================
// 2. Add "重新生成" button next to "预览合成" in each script card
// ============================================================
// The preview button: a(s,{size:`small`,text:``,type:`primary`,onClick:t=>Ee(e)},{...})
// Wrap both buttons in a flex div

const oldBtn = `a(s,{size:\`small\`,text:\`\`,type:\`primary\`,onClick:t=>Ee(e)},{default:b(()=>[...r[17]||=[i(\` 预览合成 \`,-1)]]),_:1},8,[\`onClick\`])`;

const newBtns = `n(\`div\`,{style:{display:\`flex\`,gap:\`8px\`,"align-items":\`center\`}},[a(s,{size:\`small\`,text:\`\`,type:\`primary\`,onClick:t=>Ee(e)},{default:b(()=>[...r[17]||=[i(\` 预览合成 \`,-1)]]),_:1},8,[\`onClick\`]),a(s,{size:\`small\`,type:\`primary\`,onClick:t=>Ne(e)},{default:b(()=>[...r[25]||=[i(\`重新生成\`,-1)]]),_:1})])`;

if (content.includes(oldBtn)) {
    content = content.replace(oldBtn, newBtns);
    console.log('2. Added regenerate button');
} else {
    console.log('2. ERROR: oldBtn not found');
    // Try a smaller unique portion
    const sub = `i(\` 预览合成 \`,-1)]]),_:1},8,[\`onClick\`])`;
    if (content.includes(sub)) {
        console.log('Found partial match, checking escaping...');
        console.log('Index:', content.indexOf(sub));
    }
    process.exit(1);
}

// ============================================================
// 3. Verify and write
// ============================================================
fs.writeFileSync(path, content, 'utf-8');
console.log('Write complete. New length:', content.length);

// Verify
const v = fs.readFileSync(path, 'utf-8');
console.log('Ne function:', v.includes('async function Ne(') ? 'OK' : 'MISSING');
console.log('Regen btn:', v.includes('重新生成') ? 'OK' : 'MISSING');
console.log('Ne click:', v.includes('onClick:t=>Ne(e)') ? 'OK' : 'MISSING');
