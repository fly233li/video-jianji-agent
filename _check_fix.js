const fs = require('fs');
const c = fs.readFileSync('E:/AI_jianji/video-edit-agent/frontend/dist/assets/BatchView-dQXGWYWS.js', 'utf-8');

// Find the button wrapper area
const idx = c.indexOf('align-items');
console.log('align-items at:', idx);
if (idx >= 0) {
  const ctx = c.substring(Math.max(0, idx - 30), idx + 30);
  console.log('Context:', JSON.stringify(ctx));

  // Show hex around it
  const buf = Buffer.from(c.substring(Math.max(0, idx - 5), idx + 20), 'utf-8');
  const hex = [];
  for (let i = 0; i < buf.length; i++) hex.push(buf[i].toString(16).padStart(2, '0'));
  console.log('Hex:', hex.join(' '));
}

// Check for backslashes
const bl = [];
for (let i = 0; i < c.length; i++) {
  if (c[i] === '\\') bl.push(i);
}
console.log('Backslash count:', bl.length);
if (bl.length > 0) {
  bl.forEach(function(pos) {
    console.log('Backslash at', pos, ':', JSON.stringify(c.substring(Math.max(0, pos - 5), pos + 10)));
  });
} else {
  console.log('No backslashes - good, but still failing!');
}

// Check the file around the second injection point (Ne function)
const neIdx = c.indexOf('async function Ne');
console.log('\nNe function at:', neIdx);
if (neIdx >= 0) {
  const beforeNe = c.substring(neIdx - 20, neIdx);
  console.log('Before Ne:', JSON.stringify(beforeNe));
}
