'use client';

import UsageLogs from '@/components/billing/usage-logs';
import { useEffect, useState } from 'react';

export default function UsageLogsPage() {
  const [accountId, setAccountId] = useState<string>('');

  useEffect(() => {
    // Mock data for static export
    setAccountId('mock-account-id');
  }, []);

  if (!accountId) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <UsageLogs accountId={accountId} />
    </div>
  );
}
