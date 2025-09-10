// Stub for Electron build - Server Actions not supported in static export

export async function editPersonalAccountName(prevState: any, formData: FormData) {
  console.warn('Server Actions not supported in Electron build');
  return { message: 'Server Actions disabled in Electron build' };
}