const fs = require('fs');
const c = fs.readFileSync('E:/AI_jianji/video-edit-agent/frontend/dist/assets/BatchView-dQXGWYWS.js', 'utf-8');

// Find ALL occurrences of "align-items"
let pos = -1;
let count = 0;
while ((pos = c.indexOf('align-items', pos + 1)) >= 0) {
  count++;
  console.log('align-items #' + count + ' at', pos, ':', JSON.stringify(c.substring(Math.max(0, pos - 40), pos + 20)));
  if (count > 10) break;
}

console.log('\nTotal occurrences:', count);

// Also find the button wrapper div
const flexGap = c.indexOf('gap:');
console.log('\nFirst gap: at', flexGap, JSON.stringify(c.substring(flexGap, flexGap + 30)));

// Find the buttons area
const previewBtn = c.indexOf('预览合成');
console.log('\n预览合成 at', previewBtn);
if (previewBtn >= 0) {
  console.log('Context:', JSON.stringify(c.substring(Math.max(0, previewBtn - 60), previewBtn + 20)));
}

// Check the first few chars for any BOM or invisible chars
const buf = Buffer.from(c.substring(0, 10));
console.log('\nFirst 10 bytes:', Array.from(buf).map(b => b.toString(16)).join(' '));
