const fs = require('fs');
const api = fs.readFileSync('E:/AI_jianji/video-edit-agent/frontend/dist/assets/useApi-CvWfOpp_.js', 'utf-8');

// Check all backslash contexts
const bs = [];
for (let i = 0; i < api.length; i++) {
  if (api[i] === '\\') {
    const ctx = api.substring(Math.max(0,i-5), i+10);
    bs.push({pos:i, ctx});
  }
}
console.log('Backslashes in useApi:', bs.length);
bs.slice(0, 10).forEach(b => console.log(`  ${b.pos}: ${JSON.stringify(b.ctx)}`));
if (bs.length > 10) console.log('  ... and', bs.length - 10, 'more');

// Check for the specific problematic pattern
const hasEscapedQuote = api.includes('\\"');
console.log('Has \\":', hasEscapedQuote);
