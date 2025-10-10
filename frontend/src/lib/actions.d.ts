// 类型声明文件，帮助TypeScript理解带特定后缀的actions模块

declare module '*/actions/teams' {
  export const createTeam: any;
  export const editTeamName: any;
  export const editTeamSlug: any;
  export const updateTeam: any;
  export const deleteTeam: any;
}

declare module '*/actions/members' {
  export const removeTeamMember: any;
  export const updateTeamMemberRole: any;
  export const updateMemberRole: any;
  export const removeMember: any;
}

declare module '*/actions/invitations' {
  export const createInvitation: any;
  export const deleteInvitation: any;
  export const acceptInvitation: any;
  export const declineInvitation: any;
}

declare module '*/actions/personal-account' {
  export const editPersonalAccountName: any;
}

declare module '*/actions/threads' {
  export const generateThreadName: any;
}