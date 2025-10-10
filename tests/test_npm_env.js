'use strict';

/**
 * 测试脚本：验证npm配置环境变量是否能被正确读取
 * 用法：node test_npm_env.js
 */
console.log('=== npm环境变量测试工具 ===');
console.log('检查npm代理相关环境变量:');

// 打印npm代理相关环境变量
console.log('1. 读取npm配置环境变量:');
console.log(`   npm_config_https_proxy: ${process.env.npm_config_https_proxy || '未设置'}`);
console.log(`   npm_config_http_proxy: ${process.env.npm_config_http_proxy || '未设置'}`);
console.log(`   npm_config_proxy: ${process.env.npm_config_proxy || '未设置'}`);

// 打印所有以npm_config_开头的环境变量，查看是否有其他相关配置
console.log('\n2. 所有以npm_config_开头的环境变量:');
const npmVars = Object.keys(process.env)
  .filter(key => key.startsWith('npm_config_'))
  .sort();

npmVars.forEach(key => {
  console.log(`   ${key}: ${process.env[key]}`);
});

console.log('\n3. 环境变量读取说明:');
console.log('   - npm在运行脚本时会自动传递其配置作为环境变量');
console.log('   - 但这些环境变量只在npm命令的上下文中可用');
console.log('   - 如果直接使用node命令运行脚本，这些环境变量可能不存在');
console.log('\n建议使用以下命令测试:');
console.log('   npm run test-env  (需要在package.json中配置scripts)');
console.log('或');
console.log('   npm exec -- node test_npm_env.js');