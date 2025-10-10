// 统一的Actions导入层
// 此文件的作用是解决TypeScript无法直接识别带特定后缀文件(.web.ts/.electron.ts)的问题
// 所有组件都应通过此文件导入actions，而不是直接从@/lib/actions/模块导入

// 从config模块导入环境检测函数
import { isElectron, isWeb } from './config';

export {
  isElectron,
  isWeb
};

// 为了保持向后兼容性，保留旧的函数名称
export const isElectronBuild = isElectron();
export const isElectronBuildFn = isElectron;

// 导入teams相关操作
import { createTeam, editTeamName, editTeamSlug } from './actions/teams';
export const teams = {
  createTeam,
  editTeamName,
  editTeamSlug
};

// 直接导出主要的action函数，以便在useActionState等hooks中使用
// 这是必要的，因为这些hooks需要直接引用函数，而不是对象属性

export const createTeamFn = createTeam;
export const editTeamNameFn = editTeamName;
export const editTeamSlugFn = editTeamSlug;

// 导入members相关操作
import { removeTeamMember, updateTeamMemberRole } from './actions/members';
export const members = {
  removeTeamMember,
  updateTeamMemberRole,
  // 添加别名以保持兼容性
  updateMemberRole: updateTeamMemberRole,
  removeMember: removeTeamMember
};

export const removeTeamMemberFn = removeTeamMember;
export const updateTeamMemberRoleFn = updateTeamMemberRole;

// 导入invitations相关操作
import { createInvitation, deleteInvitation, acceptInvitation } from './actions/invitations';
export const invitations = {
  createInvitation,
  deleteInvitation,
  acceptInvitation
  // declineInvitation函数在web.ts文件中不存在
};

export const createInvitationFn = createInvitation;
export const deleteInvitationFn = deleteInvitation;
export const acceptInvitationFn = acceptInvitation;

// 导入personal-account相关操作
import { editPersonalAccountName } from './actions/personal-account';
export const personalAccount = {
  editPersonalAccountName
};

export const editPersonalAccountNameFn = editPersonalAccountName;

// 导入threads相关操作
import { generateThreadName } from './actions/threads';
export const threads = {
  generateThreadName
};

export const generateThreadNameFn = generateThreadName;