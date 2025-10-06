// Stub for Electron build - Server Actions not supported in static export

export async function createTeam(prevState: any, formData: FormData) {
  console.warn('Server Actions not supported in Electron build');
  return { message: 'Server Actions disabled in Electron build' };
}

export async function updateTeam(prevState: any, formData: FormData) {
  console.warn('Server Actions not supported in Electron build');
  return { message: 'Server Actions disabled in Electron build' };
}

export async function editTeamName(prevState: any, formData: FormData) {
  console.warn('Server Actions not supported in Electron build');
  return { message: 'Server Actions disabled in Electron build' };
}

export async function deleteTeam(prevState: any, formData: FormData) {
  console.warn('Server Actions not supported in Electron build');
  return { message: 'Server Actions disabled in Electron build' };
}

export async function editTeamSlug(prevState: any, formData: FormData) {
  console.warn('Server Actions not supported in Electron build');
  return { message: 'Server Actions disabled in Electron build' };
}