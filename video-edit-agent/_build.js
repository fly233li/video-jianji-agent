const { execSync } = require('child_process');
try {
    const result = execSync('"D:/nodejs/npm.cmd" run build', {
        cwd: 'E:/AI_jianji/video-edit-agent/frontend',
        timeout: 120000,
        encoding: 'utf-8'
    });
    console.log('BUILD SUCCESS');
    console.log(result.substring(result.length - 1000));
} catch (e) {
    console.log('BUILD FAILED');
    console.log(e.stdout?.substring(-1000) || '');
    console.log(e.stderr?.substring(-1000) || '');
}
