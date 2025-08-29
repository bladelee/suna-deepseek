/**
 * 清除 localStorage 中的旧模型选择
 * 用于修复从 gpt-5-mini 迁移到 deepseek/deepseek-chat 的问题
 */

export const clearModelPreference = (): void => {
  if (typeof window === 'undefined') return;
  
  try {
    const storageKey = 'suna-preferred-model-v3';
    const currentModel = localStorage.getItem(storageKey);
    
    // 检查是否是旧的模型名称
    const oldModels = ['gpt-5-mini', 'openai/gpt-5-mini'];
    
    if (currentModel && oldModels.includes(currentModel)) {
      console.log(`🔄 检测到旧的模型选择: ${currentModel}，正在清除...`);
      localStorage.removeItem(storageKey);
      console.log('✅ 已清除旧的模型选择');
    } else {
      console.log(`ℹ️  当前模型选择: ${currentModel || '未设置'}`);
    }
  } catch (error) {
    console.warn('❌ 清除模型选择时出现错误:', error);
  }
};

/**
 * 强制重置模型选择为默认值
 */
export const resetModelPreference = (): void => {
  if (typeof window === 'undefined') return;
  
  try {
    const storageKey = 'suna-preferred-model-v3';
    localStorage.removeItem(storageKey);
    console.log('✅ 已重置模型选择');
  } catch (error) {
    console.warn('❌ 重置模型选择时出现错误:', error);
  }
};
