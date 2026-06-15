const fs = require('fs');
const path = 'E:/AI_jianji/video-edit-agent/frontend/dist/assets/BatchView-dQXGWYWS.js';
const c = fs.readFileSync(path, 'utf-8');

// The problem: \"align-items\" in JS source outside a string context
// Need to replace with "align-items"
const fixed = c.split('\\"align-items\\"').join('"align-items"');

fs.writeFileSync(path, fixed, 'utf-8');
console.log('Fixed!');

// Verify: check remaining backslashes outside allowed patterns
const bs = [];
for (let i = 0; i < fixed.length; i++) {
  if (fixed[i] === '\\') bs.push(i);
}
console.log('Remaining backslashes:', bs.length, '(should be 0)');
if (bs.length > 0) {
  for (const idx of bs) {
    console.log(`  Backslash at ${idx}: context: "${fixed.substring(Math.max(0,idx-10), idx+10)}"`);
  }
}
