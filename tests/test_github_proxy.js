#!/usr/bin/env node

'use strict';

import fetch from 'node-fetch';
import { Agent } from 'https';
import { HttpsProxyAgent } from 'https-proxy-agent';

/**
 * 测试代理服务器是否能正常访问GitHub.com (与postinstall.js代理方式对齐)
 * 用法: node test_github_proxy.js
 * 仅使用npm配置的代理设置
 */
async function testGitHubProxy() {
  // 从npm配置获取代理URL（与postinstall.js保持一致）
  const proxyUrl = 
    process.env.npm_config_https_proxy ||
    process.env.npm_config_http_proxy ||
    process.env.npm_config_proxy;
  
  console.log('正在测试GitHub代理连接...');
  console.log(`使用的代理URL: ${proxyUrl || '无代理'}`);
  
  // 创建代理agent或默认agent（与postinstall.js保持一致）
  const agent = proxyUrl
    ? new HttpsProxyAgent(proxyUrl, { keepAlive: true })
    : new Agent({ keepAlive: true });
  
  try {
    // 测试连接GitHub Releases下载checksums文件
    const startTime = Date.now();
    console.log('正在连接github.com/releases/download...');
    const response = await fetch('https://github.com/supabase/cli/releases/download/v2.48.3/supabase_2.48.3_checksums.txt', {
      agent,
      timeout: 10000, // 10秒超时
      headers: {
        'User-Agent': 'Node.js Proxy Tester'
      }
    });
    
    const endTime = Date.now();
    
    if (response.ok) {
      const data = await response.text();
      console.log(`✓ 代理连接成功！响应时间: ${endTime - startTime}ms`);
      console.log(`✓ 成功获取checksums.txt文件（前50个字符）: ${data.substring(0, 50)}...`);
      console.log('✓ 代理服务器工作正常，可以访问GitHub Releases下载文件');
    } else {
      console.error(`✗ 代理连接失败，HTTP状态码: ${response.status}`);
      console.error(`✗ 响应状态: ${response.statusText}`);
    }
  } catch (error) {
    console.error('✗ 代理连接异常:', error.message);
    console.error('✗ 请检查代理服务器设置是否正确，以及代理服务器是否可用');
    console.error('✗ 可能的原因：代理服务器地址错误、代理服务器未启动、网络连接问题或代理服务器被防火墙阻止');
  }
}

// 运行测试
console.log('=== GitHub代理测试工具 (与postinstall.js对齐) ===');
console.log('此工具用于验证代理服务器是否能正常访问GitHub.com的Releases下载文件\n');
testGitHubProxy();