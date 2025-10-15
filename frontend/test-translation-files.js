// 翻译文件测试
console.log('🔍 测试翻译文件加载和验证...\n');

const fs = require('fs');
const path = require('path');

// 测试翻译文件是否存在和格式正确
function testTranslationFiles() {
  let passed = 0;
  let total = 0;

  console.log('📁 测试翻译文件存在性');

  const files = [
    'messages/en.json',
    'messages/zh-CN.json',
    'messages/electron.json'
  ];

  files.forEach(file => {
    total++;
    if (fs.existsSync(file)) {
      console.log(`✅ ${file} - 文件存在`);
      passed++;
    } else {
      console.log(`❌ ${file} - 文件不存在`);
    }
  });

  console.log('\n📄 测试翻译文件格式');

  try {
    // 测试英文翻译文件
    total++;
    const enContent = JSON.parse(fs.readFileSync('messages/en.json', 'utf8'));
    if (enContent.dashboard && enContent.dashboard.title) {
      console.log('✅ 英文翻译文件格式正确');
      passed++;
    } else {
      console.log('❌ 英文翻译文件格式不正确');
    }

    // 测试中文翻译文件
    total++;
    const zhContent = JSON.parse(fs.readFileSync('messages/zh-CN.json', 'utf8'));
    if (zhContent.dashboard && zhContent.dashboard.title) {
      console.log('✅ 中文翻译文件格式正确');
      passed++;
    } else {
      console.log('❌ 中文翻译文件格式不正确');
    }

    // 测试Electron翻译文件
    total++;
    const electronContent = JSON.parse(fs.readFileSync('messages/electron.json', 'utf8'));
    if (electronContent.en && electronContent.zhCN) {
      console.log('✅ Electron翻译文件格式正确');
      passed++;
    } else {
      console.log('❌ Electron翻译文件格式不正确');
    }

  } catch (error) {
    console.log('❌ 翻译文件解析错误:', error.message);
  }

  console.log('\n🔍 测试翻译内容一致性');

  try {
    const enContent = JSON.parse(fs.readFileSync('messages/en.json', 'utf8'));
    const zhContent = JSON.parse(fs.readFileSync('messages/zh-CN.json', 'utf8'));

    // 检查关键翻译项
    const keysToCheck = [
      'dashboard.title',
      'dashboard.placeholder',
      'common.save',
      'common.cancel',
      'navigation.dashboard',
      'auth.login'
    ];

    let consistentCount = 0;
    keysToCheck.forEach(key => {
      const keys = key.split('.');
      let enValue = enContent;
      let zhValue = zhContent;

      for (const k of keys) {
        enValue = enValue?.[k];
        zhValue = zhValue?.[k];
      }

      total++;
      if (enValue && zhValue && typeof enValue === 'string' && typeof zhValue === 'string') {
        consistentCount++;
        console.log(`✅ ${key} - 中英文都存在`);
        passed++;
      } else {
        console.log(`❌ ${key} - 翻译不完整 (EN: ${enValue || 'missing'}, ZH: ${zhValue || 'missing'})`);
      }
    });

    console.log(`\n📊 翻译完整性: ${consistentCount}/${keysToCheck.length} 个关键项有完整翻译`);

  } catch (error) {
    console.log('❌ 翻译一致性检查失败:', error.message);
  }

  console.log('\n🏆 文件测试结果:');
  console.log(`通过: ${passed}/${total}`);
  console.log(`成功率: ${((passed/total)*100).toFixed(1)}%`);

  if (passed === total) {
    console.log('🎉 所有翻译文件测试通过！');
  } else {
    console.log('⚠️  部分文件测试失败，需要检查翻译文件。');
  }

  return passed === total;
}

// 测试翻译内容质量
function testTranslationQuality() {
  console.log('\n📝 测试翻译内容质量...');

  try {
    const zhContent = JSON.parse(fs.readFileSync('messages/zh-CN.json', 'utf8'));

    // 检查中文翻译的基本质量
    const qualityChecks = [
      { key: 'dashboard.title', pattern: /今天想做什么/, description: 'Dashboard标题翻译' },
      { key: 'common.save', pattern: /保存/, description: '保存按钮翻译' },
      { key: 'navigation.dashboard', pattern: /仪表板/, description: '导航菜单翻译' }
    ];

    let qualityPassed = 0;
    qualityChecks.forEach(check => {
      const keys = check.key.split('.');
      let value = zhContent;
      for (const k of keys) {
        value = value?.[k];
      }

      if (value && check.pattern.test(value)) {
        console.log(`✅ ${check.description} - 质量良好`);
        qualityPassed++;
      } else {
        console.log(`❌ ${check.description} - 质量有问题: ${value}`);
      }
    });

    console.log(`\n📊 翻译质量: ${qualityPassed}/${qualityChecks.length} 个检查项通过`);

    return qualityPassed === qualityChecks.length;
  } catch (error) {
    console.log('❌ 翻译质量测试失败:', error.message);
    return false;
  }
}

// 运行所有测试
console.log('🧪 开始翻译文件测试...\n');
const fileTestPassed = testTranslationFiles();
const qualityTestPassed = testTranslationQuality();

console.log('\n🎯 最终测试结果:');
if (fileTestPassed && qualityTestPassed) {
  console.log('🎉 所有翻译文件测试通过！翻译系统准备就绪。');
} else {
  console.log('⚠️  部分测试失败，请检查翻译文件。');
}