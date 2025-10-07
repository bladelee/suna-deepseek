// Global TypeScript declarations for the project
declare global {
  interface Window {
    useQuery?: () => {
      data: any[];
      isLoading: boolean;
      refetch: () => void;
    };
    useMutation?: () => {
      mutate: () => void;
      isLoading: boolean;
    };
    tolt_referral?: string | null;
    electronAPI?: any;
  }
}

export {}; // This export statement is required to make this a module