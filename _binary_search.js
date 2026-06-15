const fs = require('fs');
const c = fs.readFileSync('E:/AI_jianji/video-edit-agent/frontend/dist/assets/BatchView-dQXGWYWS.js', 'utf-8');

// Check for BOM
const first4 = c.substring(0, 4);
console.log('First 4 chars codes:', Array.from(first4).map(ch => ch.charCodeAt(0)));

// Check for zero-width characters throughout the file
const zw = [];
for (let i = 0; i < c.length; i++) {
  const cp = c.charCodeAt(i);
  if (cp === 0x200B || cp === 0x200C || cp === 0x200D || cp === 0xFEFF || cp === 0x00AD || cp === 0x2060) {
    zw.push({ pos: i, code: cp, context: c.substring(Math.max(0, i - 5), i + 5) });
  }
}
console.log('Zero-width chars:', zw.length);
if (zw.length > 0) {
  zw.forEach(z => console.log(`  at ${z.pos}: U+${z.code.toString(16)} - ${JSON.stringify(z.context)}`));
}

// Try binary search by truncating the file
// First, let me find where the syntax error occurs by trying to parse truncated versions
function tryParse(code) {
  try {
    new Function(code);
    return true;
  } catch (e) {
    return false;
  }
}

// The ESM import syntax causes failure in non-module context
// Let's try something different: use acorn if available
try {
  require('acorn');
  console.log('acorn available');
} catch {
  console.log('acorn not available');
}

// Instead, let me check if the original file (before edits) would parse
// I can reconstruct it by removing my injected code

// Strategy: find the exact spot where the parse fails by dividing the file
// Since we can't parse ESM directly, let me try prepending module setup code
const wrapInModule = (code) => {
  // Replace imports with empty definitions
  const noImports = code.replace(/import\{[^}]+\}from"[^"]+"/g, '');
  // Replace export
  const noExport = noImports.replace(/export\{[^}]+\};$/, '');
  return noExport;
};

const cleaned = wrapInModule(c);
try {
  new Function(cleaned);
  console.log('Wrapped version parses OK');
} catch (e) {
  console.log('Wrapped version parse error:', e.message, 'at line', e.lineNumber, 'col', e.columnNumber);

  // Binary search in the cleaned code
  let low = 0;
  let high = cleaned.length;
  let lastGood = -1;
  let attempts = 0;

  while (low < high && attempts < 30) {
    attempts++;
    const mid = Math.floor((low + high) / 2);
    const chunk = cleaned.substring(0, mid);
    try {
      new Function(chunk);
      // If this parses, the error is after mid
      lastGood = mid;
      low = mid + 1;
    } catch {
      // If this doesn't parse, the error is before mid
      high = mid;
    }
  }

  console.log('Binary search found error boundary at approximately position', lastGood);
  if (lastGood >= 0) {
    console.log('Context:', JSON.stringify(cleaned.substring(Math.max(0, lastGood - 30), lastGood + 30)));
    console.log('Hex:', Buffer.from(cleaned.substring(Math.max(0, lastGood - 5), lastGood + 10), 'utf-8').toString('hex'));
  }
}
