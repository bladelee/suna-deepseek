// 简单的i18n功能测试
const { detectLanguage, formatTranslation, getNestedTranslation } = require('./src/i18n/index.ts');

console.log('Testing i18n functions...');

// 测试语言检测
try {
  const detectedLang = detectLanguage();
  console.log('✓ Language detection works:', detectedLang);
} catch (error) {
  console.log('✗ Language detection failed:', error.message);
}

// 测试翻译格式化
try {
  const formatted = formatTranslation('Hello {{name}}, you have {{count}} messages', { name: 'John', count: 5 });
  console.log('✓ Translation formatting works:', formatted);
} catch (error) {
  console.log('✗ Translation formatting failed:', error.message);
}

// 测试嵌套对象获取
try {
  const resources = {
    dashboard: {
      title: 'What would you like to do today?'
    }
  };
  const value = getNestedTranslation(resources, ['dashboard', 'title']);
  console.log('✓ Nested translation works:', value);
} catch (error) {
  console.log('✗ Nested translation failed:', error.message);
}

console.log('Basic i18n tests completed.');