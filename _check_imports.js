const fs = require('fs');
const idx = fs.readFileSync('E:/AI_jianji/video-edit-agent/frontend/dist/assets/index-CN3hoVpR.js', 'utf-8');

// Find all import statements in the index chunk
const imports = idx.match(/import\("[^"]+"\)/g) || [];
console.log('Dynamic imports in index:');
imports.forEach(imp => console.log('  ', imp));

// Find all static imports
const staticImports = idx.match(/from"[^"]+"/g) || [];
console.log('\nStatic import sources:');
staticImports.forEach(imp => console.log('  ', imp));

// Find useApi reference
const apiRefs = idx.match(/useApi[^"]*/g) || [];
console.log('\nuseApi refs:', apiRefs);

// Check for SyntaxError source - look for problematic patterns
// Check backward slashes in index
const bs = [];
for (let i = 0; i < idx.length; i++) {
  if (idx[i] === '\\') bs.push(i);
}
console.log('\nBackslashes in index:', bs.length);

// Check if there's an eval() or new Function() call that might have bad code
const evalIdx = idx.indexOf('eval');
if (evalIdx >= 0) console.log('eval found at', evalIdx, ':', idx.substring(evalIdx, evalIdx + 30));
const funcIdx = idx.indexOf('new Function');
if (funcIdx >= 0) console.log('new Function at', funcIdx, ':', idx.substring(funcIdx, funcIdx + 40));

// Check for blob: URL usage
const blobIdx = idx.indexOf('blob:');
if (blobIdx >= 0) console.log('blob: found at', blobIdx, ':', idx.substring(Math.max(0, blobIdx - 20), blobIdx + 20));
