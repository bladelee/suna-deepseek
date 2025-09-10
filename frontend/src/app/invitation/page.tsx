'use client';

import React, { Suspense } from 'react';
import AcceptTeamInvitation from '@/components/basejump/accept-team-invitation';
import { redirect, useSearchParams } from 'next/navigation';

function InvitationContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  if (!token) {
    redirect('/');
  }

  return (
    <div className="max-w-md mx-auto w-full my-12">
      <AcceptTeamInvitation token={token} />
    </div>
  );
}

export default function AcceptInvitationPage() {
  return (
    <Suspense fallback={<div className="max-w-md mx-auto w-full my-12">Loading invitation...</div>}>
      <InvitationContent />
    </Suspense>
  );
}
