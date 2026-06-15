const fs = require('fs');
const content = fs.readFileSync('E:/AI_jianji/video-edit-agent/frontend/dist/assets/BatchView-dQXGWYWS.js', 'utf-8');

// Find "预览合成"
const idx = content.indexOf('预览合成');
if (idx >= 0) {
    const ctx = content.substring(Math.max(0, idx - 300), idx + 100);
    console.log("Context around '预览合成':");
    console.log(ctx);
    console.log("\n--- Hex dump of the exact match area ---");
    const exact = content.substring(idx - 5, idx + 50);
    for (let i = 0; i < exact.length; i++) {
        const c = exact[i];
        const code = c.charCodeAt(0);
        if (code > 127) {
            process.stdout.write(c);
        } else if (c === '\n') {
            process.stdout.write('\\n');
        } else if (c === '\r') {
            process.stdout.write('\\r');
        } else {
            process.stdout.write(c);
        }
    }
    console.log('\n');
}

// Also find "Ee(e)" to locate the synthesizeScript call
const eeIdx = content.indexOf('Ee(e)');
if (eeIdx >= 0) {
    console.log('Ee(e) found at', eeIdx);
    console.log('Context:', content.substring(Math.max(0, eeIdx - 100), eeIdx + 50));
}
