const fs = require('fs');
const bv = fs.readFileSync('E:/AI_jianji/video-edit-agent/frontend/dist/assets/BatchView-dQXGWYWS.js', 'utf-8');
const idx = fs.readFileSync('E:/AI_jianji/video-edit-agent/frontend/dist/assets/index-CN3hoVpR.js', 'utf-8');
const api = fs.readFileSync('E:/AI_jianji/video-edit-agent/frontend/dist/assets/useApi-CvWfOpp_.js', 'utf-8');

console.log('=== BatchView ===');
console.log('Length:', bv.length);
console.log('Has backslash:', bv.includes('\\'));
console.log('Has "align-items":', bv.includes('"align-items"'));
console.log('Has \\"align-items\\":', bv.includes('\\"align-items"'));
console.log('First 50:', JSON.stringify(bv.substring(0, 50)));
console.log('Last 50:', JSON.stringify(bv.substring(bv.length - 50)));

// Check the imported function Ne
const neIdx = bv.indexOf('async function Ne');
if (neIdx >= 0) {
  console.log('\nNe function found at', neIdx);
  console.log('Ne body:', bv.substring(neIdx, neIdx + 400));
}

// Check useApi for its export name
console.log('\n=== useApi ===');
console.log('Length:', api.length);
// Find exports
const exportIdx = api.indexOf('export');
if (exportIdx >= 0) console.log('Export:', api.substring(exportIdx, exportIdx + 60));

// Check index for BatchView import
console.log('\n=== Index ===');
const bvRef = idx.indexOf('BatchView');
if (bvRef >= 0) console.log('BatchView ref in index:', idx.substring(Math.max(0, bvRef - 20), bvRef + 60));
const bvRef2 = idx.indexOf('dQXGWYWS');
if (bvRef2 >= 0) console.log('BatchView hash ref:', idx.substring(Math.max(0, bvRef2 - 10), bvRef2 + 10));
