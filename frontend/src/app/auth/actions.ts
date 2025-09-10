// Stub for Electron build - Server Actions not supported in static export

export async function signIn(prevState: any, formData: FormData) {
  console.warn('Server Actions not supported in Electron build');
  return { message: 'Server Actions disabled in Electron build' };
}

export async function signUp(prevState: any, formData: FormData) {
  console.warn('Server Actions not supported in Electron build');
  return { message: 'Server Actions disabled in Electron build' };
}

export async function forgotPassword(prevState: any, formData: FormData) {
  console.warn('Server Actions not supported in Electron build');
  return { message: 'Server Actions disabled in Electron build' };
}

export async function resetPassword(prevState: any, formData: FormData) {
  console.warn('Server Actions not supported in Electron build');
  return { message: 'Server Actions disabled in Electron build' };
}

export async function signOut() {
  console.warn('Server Actions not supported in Electron build');
  // Return void to satisfy form action type requirements
}