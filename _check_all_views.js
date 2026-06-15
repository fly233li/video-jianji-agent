const fs = require('fs');
const dir = 'E:/AI_jianji/video-edit-agent/frontend/dist/assets/';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.js'));

for (const file of files) {
  const content = fs.readFileSync(dir + file, 'utf-8');

  // Check for common syntax error patterns
  const issues = [];

  // Check for backslashes
  const backslashes = [];
  for (let i = 0; i < content.length; i++) {
    if (content[i] === '\\') backslashes.push(i);
  }

  if (backslashes.length > 0) {
    // Check for specific invalid patterns like \" outside string context
    for (const pos of backslashes) {
      const next = content[pos + 1];
      if (next === '"') {
        // Check context: is this in a string?
        const before = content.substring(Math.max(0,pos-20), pos);
        // Common indicator: if in a JS string, there should be quote chars nearby
        // If not, this might be an issue
        issues.push(`Possible problematic \\" at ${pos}: ...${content.substring(Math.max(0,pos-10), pos+10)}...`);
      }
    }
  }

  console.log(`\n=== ${file} ===`);
  console.log(`Size: ${content.length} bytes`);
  console.log(`Backslashes: ${backslashes.length}`);
  if (issues.length > 0) {
    console.log('ISSUES:');
    issues.forEach(i => console.log('  ' + i));
  }

  // Check first 50 chars
  console.log(`Starts with: ${content.substring(0,50)}`);

  // Check if it can be parsed by new Function (for non-ESM files)
  if (!content.includes('import{') && !content.includes('export{')) {
    try {
      new Function(content);
    } catch(e) {
      console.log(`Parse error: ${e.message}`);
    }
  }
}
