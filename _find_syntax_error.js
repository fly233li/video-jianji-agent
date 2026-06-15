// Use acorn to parse the module and find the exact syntax error
const fs = require('fs');
const code = fs.readFileSync('E:/AI_jianji/video-edit-agent/frontend/dist/assets/BatchView-dQXGWYWS.js', 'utf-8');

// Try to find the error by scanning through each character
// The "Invalid or unexpected token" is usually caused by:
// 1. A stray character that doesn't belong
// 2. A line break or space issue inside a string/template literal
// 3. Incorrect escaping

// Look for common issues in template literals
// Find all template literal boundaries
const backtickPositions = [];
for (let i = 0; i < code.length; i++) {
  if (code[i] === '`') backtickPositions.push(i);
}

console.log('Total backticks:', backtickPositions.length, '(should be even)');
if (backtickPositions.length % 2 !== 0) {
  console.log('ERROR: Odd number of backticks!');
  // Find the unmatched one
  let depth = 0;
  for (let i = 0; i < code.length; i++) {
    if (code[i] === '`') {
      depth++;
    }
  }
}

// Check for problematic patterns in template literals
// Find template literals containing ${} with nested backtick issues
for (let i = 0; i < backtickPositions.length; i += 2) {
  if (i + 1 >= backtickPositions.length) break;
  const start = backtickPositions[i];
  const end = backtickPositions[i + 1];
  const content = code.substring(start, end + 1);

  // Check for unescaped backticks inside
  let inner = code.substring(start + 1, end);
  if (inner.includes('`')) {
    console.log(`Template literal at ${start} has inner backtick`);
    console.log(`  Content: ${inner.substring(0, 100)}...`);
  }
}

// Check for \$ patterns that might cause issues
const dollarBrace = [];
for (let i = 0; i < code.length - 1; i++) {
  if (code[i] === '$' && code[i+1] === '{') dollarBrace.push(i);
}
console.log('${ occurrences:', dollarBrace.length);

// Check for any invalid characters (non-ASCII printable except in strings)
for (let i = 0; i < code.length; i++) {
  const ch = code[i];
  const codePoint = code.charCodeAt(i);
  // Check for invalid characters outside of template literals/strings
  if (codePoint !== 10 && codePoint !== 13 && (codePoint < 32 || codePoint > 126) && codePoint !== 0x2029 && codePoint !== 0x2028) {
    // This might be a non-ASCII char not in a string context
    // But since it's a Chinese app, there are many CJK characters, so ignore them
    if (codePoint >= 0x4e00 && codePoint <= 0x9fff) continue; // CJK
    if (codePoint >= 0x3000 && codePoint <= 0x303f) continue; // CJK punctuation
    if (codePoint >= 0xff00 && codePoint <= 0xffef) continue; // Fullwidth
    console.log(`Char at ${i}: U+${codePoint.toString(16)} '${ch}' (outside ASCII range)`);
  }
}

console.log('\nFile length:', code.length);
console.log('First 50 chars:', code.substring(0, 50));
console.log('Last 50 chars:', code.substring(code.length - 50));

// Try to check if the issue is with my injected code
const myCode = code.substring(5084, 5563); // Ne function
console.log('\nInjected Ne function length:', myCode.length);
console.log('Backticks in Ne:', (myCode.match(/`/g)||[]).length, '(should be even)');

// Check for specific issues in the Ne function
for (let i = 0; i < myCode.length; i++) {
  if (myCode[i] === '`') {
    // Check if this backtick is properly closed
    const next = myCode.indexOf('`', i + 1);
    if (next < 0) {
      console.log(`Unclosed backtick at local position ${i} (file position ${5084 + i})`);
    }
    i = next;
  }
}

// Check for any double backtick issues - empty template literals are OK
console.log('\nEmpty template literals (``):', (code.match(/``/g)||[]).length);

// Check for backslash escaping issues
const backslashes = [];
for (let i = 0; i < code.length; i++) {
  if (code[i] === '\\') backslashes.push(i);
}
console.log('Backslashes:', backslashes.length);

// Specifically check the button replacement area
const btnIdx = code.indexOf('flex`,gap:`8px`');
console.log('\nButtons wrapper at:', btnIdx);
if (btnIdx >= 0) {
  const context = code.substring(btnIdx - 50, btnIdx + 200);
  console.log('Context:', context.substring(0, 250));

  // Check for proper escaping
  for (let i = Math.max(0, btnIdx - 50); i < Math.min(code.length, btnIdx + 200); i++) {
    if (code[i] === '\\') {
      console.log(`  Backslash at ${i}: '${code[i]}${code[i+1]||""}'`);
    }
  }
}

// Check for the issue - maybe the escaped quotes in style props
const alignIdx = code.indexOf('\"align-items\"');
console.log('\n\"align-items\" occurrences:', (code.match(/\"align-items\"/g)||[]).length);
