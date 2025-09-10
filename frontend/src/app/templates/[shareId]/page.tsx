import { createClient } from '@/lib/supabase/server';
import ManageTeamMembers from '@/components/basejump/manage-team-members';
import ManageTeamInvitations from '@/components/basejump/manage-team-invitations';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

type AccountParams = {
  accountSlug: string;
};

export async function generateStaticParams() {
  // For Electron build, return empty array since we don't need pre-generated paths
  return [{ shareId: 'test' }];
}

export default async function TeamMembersPage({
  params,
}: {
  params: Promise<AccountParams>;
}) {
  const { accountSlug } = await params;

  let teamAccount = null;
  let error = null;

  try {
    const supabaseClient = await createClient();
    const { data } = await supabaseClient.rpc('get_account_by_slug', {
      slug: accountSlug,
    });
    teamAccount = data;
  } catch (err) {
    error = 'Failed to load team data';
    console.error(err);
  }

  if (error) {
    return (
      <Alert
        variant="destructive"
        className="border-red-300 dark:border-red-800 rounded-xl"
      >
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!teamAccount || teamAccount.account_role !== 'owner') {
    return (
      <Alert
        variant="destructive"
        className="border-red-300 dark:border-red-800 rounded-xl"
      >
        <AlertTitle>Access Denied</AlertTitle>
        <AlertDescription>
          You do not have permission to access this page.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-card-title">Team Members</h3>
        <p className="text-sm text-foreground/70">
          Manage your team members and invitations.
        </p>
      </div>

      <Card className="border-subtle dark:border-white/10 bg-white dark:bg-background-secondary shadow-none">
        <CardHeader>
          <CardTitle className="text-base text-card-title">
            Invitations
          </CardTitle>
          <CardDescription>Invite new members to your team.</CardDescription>
        </CardHeader>
        <CardContent>
          <ManageTeamInvitations accountId={teamAccount.account_id} />
        </CardContent>
      </Card>

      <Card className="border-subtle dark:border-white/10 bg-white dark:bg-background-secondary shadow-none">
        <CardHeader>
          <CardTitle className="text-base text-card-title">Members</CardTitle>
          <CardDescription>Manage existing team members.</CardDescription>
        </CardHeader>
        <CardContent>
          <ManageTeamMembers accountId={teamAccount.account_id} />
        </CardContent>
      </Card>
    </div>
  );
}
