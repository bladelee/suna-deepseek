// Stub for Electron build - Server Actions not supported in static export

export async function checkAndInstallSunaAgent(userId: string, userCreatedAt: string) {
  console.warn('Server Actions not supported in Electron build');
  return false;
}