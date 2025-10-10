// Stub for Electron build - Server-side API calls not supported in static export

import { Project, Thread } from '@/lib/api';

export const getThread = async (threadId: string): Promise<Thread> => {
  console.warn('Server-side API calls not supported in Electron build');
  throw new Error('Server-side API calls disabled in Electron build');
};

export const getProject = async (projectId: string): Promise<Project> => {
  console.warn('Server-side API calls not supported in Electron build');
  throw new Error('Server-side API calls disabled in Electron build');
};