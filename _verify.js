const fs = require('fs');
const c = fs.readFileSync('E:/AI_jianji/video-edit-agent/frontend/dist/assets/BatchView-dQXGWYWS.js', 'utf-8');

function count(str) {
  let idx = 0, cnt = 0;
  while ((idx = c.indexOf(str, idx)) >= 0) { cnt++; idx++; }
  return cnt;
}

console.log('Ee():', count('Ee('));
console.log('Ne():', count('Ne('));
console.log('regenerate-script:', count('regenerate-script'));
console.log('D.info:', count('D.info'));
console.log('D.success:', count('D.success'));
console.log('D.error:', count('D.error'));
console.log('onClick:t=>Ee(e):', count('onClick:t=>Ee(e)'));
console.log('onClick:t=>Ne(e):', count('onClick:t=>Ne(e)'));

const retIdx = c.indexOf('return(e,r)');
const after = c.substring(retIdx);
console.log('Render function length:', after.length);
console.log('Correct ending:', after.trim().endsWith('export{O as default};'));
