# Electron Build Issues and Solutions

## Overview
This document summarizes all issues encountered during the Electron build process and their corresponding solutions.

## 1. Server Actions Incompatibility with Static Export

### Problem
Next.js Server Actions are not supported in static export mode (`output: export`), which is required for Electron builds.

### Solution
**Stub Pattern Implementation:**

Create stub files that replace real Server Actions with console warnings and disabled functionality:

```typescript
// Stub for Electron build - Server Actions not supported in static export

export async function functionName(prevState: any, formData: FormData) {
  console.warn('Server Actions not supported in Electron build');
  return { message: 'Server Actions disabled in Electron build' };
}
```

**Files Affected:**
- `/frontend/src/lib/actions/teams.ts`
- `/frontend/src/lib/actions/members.ts`
- `../actions_stubs/teams.ts` (stub version)
- `../actions_stubs/members.ts` (stub version)

**Build Script Modification:**
Modified `/frontend/scripts/build-electron.js` to:
1. Backup original Server Action files
2. Copy stub files to replace real Server Actions during build
3. Restore original files after build completion

## 2. Dynamic Route Generation Issues

### Problem
Dynamic routes require `generateStaticParams()` when using `output: export`.

### Solution
**Add generateStaticParams to all dynamic routes:**

```typescript
export function generateStaticParams() {
  return [{ param: 'test' }]; // Return empty array or test data
}
```

**Files Modified:**
- `/frontend/src/app/(dashboard)/agents/[threadId]/page.tsx`
- `/frontend/src/app/(dashboard)/agents/config/[agentId]/page.tsx`
- `/frontend/src/app/(dashboard)/agents/config/[agentId]/workflow/[workflowId]/page.tsx`
- `/frontend/src/app/(dashboard)/projects/[projectId]/thread/[threadId]/page.tsx`
- `/frontend/src/app/agents/preview/[templateId]/page.tsx`
- `/frontend/src/app/share/[threadId]/page.tsx`
- `/frontend/src/app/templates/[shareId]/page.tsx`

## 3. API Route Static Export Configuration

### Problem
API routes need explicit static export configuration.

### Solution
**Add static export configuration to API routes:**

```typescript
export const dynamic = "force-static";
export const revalidate = 60;
```

**Files Modified:**
- `/frontend/src/app/api/edge-flags/route.ts`
- `/frontend/src/app/api/integrations/[provider]/callback/route.ts`
- `/frontend/src/app/api/og/template/route.tsx`
- `/frontend/src/app/api/share-page/og-image/route.tsx`
- `/frontend/src/app/api/triggers/[triggerId]/webhook/route.ts`
- `/frontend/src/app/api/webhooks/trigger/[workflowId]/route.ts`
- `/frontend/src/app/auth/callback/route.ts`

## 4. Missing Function Exports in Stubs

### Problem
Stub files were missing function exports that were present in the real Server Action files.

### Solution
**Ensure all function exports match between real and stub files:**

**Teams Actions:**
- `createTeam`
- `updateTeam`
- `editTeamName`
- `editTeamSlug` (missing, needs to be added)
- `deleteTeam`

**Members Actions:**
- `updateMemberRole`
- `updateTeamMemberRole`
- `removeMember`
- `removeTeamMember`

## 5. Build Script Architecture

### Current Build Process
1. **Preparation**: Move problematic directories outside src
2. **Server Action Replacement**: Backup real actions, install stubs
3. **Next.js Build**: Run `NEXT_OUTPUT=export npm run build`
4. **Cleanup**: Restore original files and directories
5. **Electron Packaging**: Build Electron app with electron-builder

### Files Handled by Build Script
- API directory (`src/app/api/`)
- Auth callback directory (`src/app/auth/callback/`)
- Agents preview directory (`src/app/agents/preview/`)
- OpenGraph image file (`src/app/opengraph-image.tsx`)
- Server Actions directory (`src/lib/actions/`)
- Template share page (`src/app/templates/[shareId]/page.tsx`)

## 6. Outstanding Issues

### Current Error
```
./src/components/basejump/edit-team-slug.tsx:5:10
Type error: Module '@/lib/actions/teams' has no exported member 'editTeamSlug'.
```

### Solution Needed
Add `editTeamSlug` function to both:
1. Real Server Action file: `/frontend/src/lib/actions/teams.ts`
2. Stub file: `../actions_stubs/teams.ts`

## 7. Best Practices for Future Development

1. **Server Actions**: Always provide stub implementations for Electron compatibility
2. **Dynamic Routes**: Always include `generateStaticParams()`
3. **API Routes**: Always add static export configuration
4. **Function Exports**: Keep real and stub files in sync
5. **Build Testing**: Test Electron build regularly during development

## 8. Common Error Patterns

### Pattern 1: Missing generateStaticParams
```
Page is missing generateStaticParams() so it cannot be used with output: export config
```

### Pattern 2: Server Actions in Static Export
```
Server Actions are not supported with static export
```

### Pattern 3: API Route Configuration
```
export const dynamic/revalidate not configured on route with output: export
```

### Pattern 4: Missing Function Exports
```
Module has no exported member 'functionName'
```

## 9. Quick Fix Commands

To add missing function to stub:
```bash
echo 'export async function editTeamSlug(prevState: any, formData: FormData) {
  console.warn(\'Server Actions not supported in Electron build\');
  return { message: \'Server Actions disabled in Electron build\' };
}' >> ../actions_stubs/teams.ts
```

To add missing function to real file:
```bash
echo 'export async function editTeamSlug(prevState: any, formData: FormData) {
  // Real implementation here
}' >> src/lib/actions/teams.ts
```

## 10. Monitoring and Maintenance

Regularly check for:
1. New Server Actions added to the codebase
2. New dynamic routes created
3. New API routes added
4. Function export consistency between real and stub files

Update build script and documentation accordingly.