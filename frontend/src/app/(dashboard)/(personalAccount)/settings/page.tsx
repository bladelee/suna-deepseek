'use client';

import EditPersonalAccountName from '@/components/basejump/edit-personal-account-name';
import { useEffect, useState } from 'react';

export default function PersonalAccountSettingsPage() {
  const [personalAccount, setPersonalAccount] = useState<any>(null);

  useEffect(() => {
    // Mock data for static export
    setPersonalAccount({ account_id: 'mock-account-id', name: 'Personal Account' });
  }, []);

  if (!personalAccount) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <EditPersonalAccountName account={personalAccount} />
    </div>
  );
}
