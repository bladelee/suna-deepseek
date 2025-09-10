// Stub for Electron build - Server Actions not supported in static export

export async function createClient() {
  console.warn('Server Actions not supported in Electron build');
  
  // Return a mock client with minimal functionality
  return {
    rpc: (fnName: string, params?: any) => Promise.resolve({ data: null, error: null }),
    from: (table: string) => ({
      select: (columns?: string) => ({
        eq: (column: string, value: any) => ({
          single: () => Promise.resolve({ data: null, error: null })
        })
      })
    }),
    auth: {
      signOut: () => Promise.resolve({ error: null }),
      signInWithPassword: () => Promise.resolve({ error: null, data: null }),
      signUp: () => Promise.resolve({ error: null, data: null }),
      resetPasswordForEmail: () => Promise.resolve({ error: null }),
      updateUser: () => Promise.resolve({ error: null }),
      exchangeCodeForSession: (code: string) => Promise.resolve({ error: null, data: null }),
      getUser: () => Promise.resolve({ data: { user: { id: 'mock-user-id' } }, error: null })
    }
  };
}