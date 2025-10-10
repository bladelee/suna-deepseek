// 示例：如何在组件中使用统一的Actions导入层

import { useState } from 'react';
import { teams, isElectronBuildFn } from '@/lib/actions-import';

// 为了保持代码一致性，重命名为isElectronBuild
const isElectronBuild = isElectronBuildFn;

const CreateTeamForm = () => {
  const [formState, setFormState] = useState<{
    name: string;
    slug: string;
    error: string | null;
  }>({
    name: '',
    slug: '',
    error: null,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isElectronBuild()) {
      // 在Electron环境下，可以显示一个提示或者禁用相关功能
      setFormState(prev => ({ ...prev, error: '此功能在Electron版本中不可用' }));
      return;
    }

    setIsSubmitting(true);
    setFormState(prev => ({ ...prev, error: null }));

    try {
      // 创建FormData对象，模拟表单提交
      const formData = new FormData();
      formData.append('name', formState.name);
      formData.append('slug', formState.slug);

      // 使用统一导入层调用createTeam action
      const result = await teams.createTeam({}, formData);

      // 处理错误情况
      if (result?.message) {
        setFormState(prev => ({ ...prev, error: result.message }));
      }
    } catch (error) {
      setFormState(prev => ({ ...prev, error: '创建团队失败，请重试' }));
      console.error('Create team error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormState(prev => ({ ...prev, [name]: value }));
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="name">团队名称</label>
        <input
          id="name"
          name="name"
          value={formState.name}
          onChange={handleInputChange}
          required
          disabled={isSubmitting}
        />
      </div>
      <div>
        <label htmlFor="slug">团队Slug</label>
        <input
          id="slug"
          name="slug"
          value={formState.slug}
          onChange={handleInputChange}
          required
          disabled={isSubmitting}
        />
      </div>
      {formState.error && (
        <div className="error-message">{formState.error}</div>
      )}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? '创建中...' : '创建团队'}
      </button>
      {isElectronBuild() && (
        <p className="electron-warning">
          注意：此功能在Electron版本中不可用，仅在Web版本中支持。
        </p>
      )}
    </form>
  );
};

export default CreateTeamForm;