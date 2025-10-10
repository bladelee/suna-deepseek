# Electron 构建问题与解决方案

## 概述
本文档总结了 Electron 构建过程中遇到的所有问题及其对应的解决方案。

## 1. Server Actions 与静态导出的不兼容性

### 问题
Next.js Server Actions 不支持静态导出模式 (`output: export`)，而 Electron 构建需要此模式。

### 解决方案
**存根模式实现：**

创建存根文件，用控制台警告和禁用功能替换真实的 Server Actions：

```typescript
// Electron 构建存根 - Server Actions 在静态导出中不受支持

export async function functionName(prevState: any, formData: FormData) {
  console.warn('Server Actions not supported in Electron build');
  return { message: 'Server Actions disabled in Electron build' };
}
```

**受影响文件：**
- `/frontend/src/lib/actions/teams.ts`
- `/frontend/src/lib/actions/members.ts`
- `../actions_stubs/teams.ts` (存根版本)
- `../actions_stubs/members.ts` (存根版本)

**构建脚本修改：**
修改 `/frontend/scripts/build-electron.js` 以：
1. 备份原始 Server Action 文件
2. 在构建期间复制存根文件替换真实 Server Actions
3. 构建完成后恢复原始文件

## 2. 动态路由生成问题

### 问题
使用 `output: export` 时，动态路由需要 `generateStaticParams()`。

### 解决方案
**为所有动态路由添加 generateStaticParams：**

```typescript
export function generateStaticParams() {
  return [{ param: 'test' }]; // 返回空数组或测试数据
}
```

**修改的文件：**
- `/frontend/src/app/(dashboard)/agents/[threadId]/page.tsx`
- `/frontend/src/app/(dashboard)/agents/config/[agentId]/page.tsx`
- `/frontend/src/app/(dashboard)/agents/config/[agentId]/workflow/[workflowId]/page.tsx`
- `/frontend/src/app/(dashboard)/projects/[projectId]/thread/[threadId]/page.tsx`
- `/frontend/src/app/agents/preview/[templateId]/page.tsx`
- `/frontend/src/app/share/[threadId]/page.tsx`
- `/frontend/src/app/templates/[shareId]/page.tsx`

## 3. API 路由静态导出配置

### 问题
API 路由需要明确的静态导出配置。

### 解决方案
**为 API 路由添加静态导出配置：**

```typescript
export const dynamic = "force-static";
export const revalidate = 60;
```

**修改的文件：**
- `/frontend/src/app/api/edge-flags/route.ts`
- `/frontend/src/app/api/integrations/[provider]/callback/route.ts`
- `/frontend/src/app/api/og/template/route.tsx`
- `/frontend/src/app/api/share-page/og-image/route.tsx`
- `/frontend/src/app/api/triggers/[triggerId]/webhook/route.ts`
- `/frontend/src/app/api/webhooks/trigger/[workflowId]/route.ts`
- `/frontend/src/app/auth/callback/route.ts`

## 4. 存根文件中缺少函数导出

### 问题
存根文件缺少真实 Server Action 文件中存在的函数导出。

### 解决方案
**确保所有函数导出在真实文件和存根文件之间匹配：**

**团队操作：**
- `createTeam`
- `updateTeam`
- `editTeamName`
- `editTeamSlug` (缺少，需要添加)
- `deleteTeam`

**成员操作：**
- `updateMemberRole`
- `updateTeamMemberRole`
- `removeMember`
- `removeTeamMember`

## 5. 构建脚本架构

### 当前构建流程
1. **准备**：将有问题的目录移出 src
2. **Server Action 替换**：备份真实操作，安装存根
3. **Next.js 构建**：运行 `NEXT_OUTPUT=export npm run build`
4. **清理**：恢复原始文件和目录
5. **Electron 打包**：使用 electron-builder 构建 Electron 应用

### 构建脚本处理的文件
- API 目录 (`src/app/api/`)
- 认证回调目录 (`src/app/auth/callback/`)
- 代理预览目录 (`src/app/agents/preview/`)
- OpenGraph 图片文件 (`src/app/opengraph-image.tsx`)
- Server Actions 目录 (`src/lib/actions/`)
- 模板分享页面 (`src/app/templates/[shareId]/page.tsx`)

## 6. 未解决的问题

### 当前错误
```
./src/components/basejump/edit-team-slug.tsx:5:10
Type error: Module '@/lib/actions/teams' has no exported member 'editTeamSlug'.
```

### 需要的解决方案
将 `editTeamSlug` 函数添加到：
1. 真实 Server Action 文件：`/frontend/src/lib/actions/teams.ts`
2. 存根文件：`../actions_stubs/teams.ts`

## 7. 未来开发的最佳实践

1. **Server Actions**：始终为 Electron 兼容性提供存根实现
2. **动态路由**：始终包含 `generateStaticParams()`
3. **API 路由**：始终添加静态导出配置
4. **函数导出**：保持真实文件和存根文件同步
5. **构建测试**：在开发期间定期测试 Electron 构建

## 8. 常见错误模式

### 模式 1：缺少 generateStaticParams
```
Page is missing generateStaticParams() so it cannot be used with output: export config
```

### 模式 2：静态导出中的 Server Actions
```
Server Actions are not supported with static export
```

### 模式 3：API 路由配置
```
export const dynamic/revalidate not configured on route with output: export
```

### 模式 4：缺少函数导出
```
Module has no exported member 'functionName'
```

## 9. 快速修复命令

向存根添加缺失函数：
```bash
echo 'export async function editTeamSlug(prevState: any, formData: FormData) {
  console.warn(\'Server Actions not supported in Electron build\');
  return { message: \'Server Actions disabled in Electron build\' };
}' >> ../actions_stubs/teams.ts
```

向真实文件添加缺失函数：
```bash
echo 'export async function editTeamSlug(prevState: any, formData: FormData) {
  // 真实实现在这里
}' >> src/lib/actions/teams.ts
```

## 10. 监控和维护

定期检查：
1. 代码库中添加的新 Server Actions
2. 创建的新动态路由
3. 添加的新 API 路由
4. 真实文件和存根文件之间的函数导出一致性

相应地更新构建脚本和文档。