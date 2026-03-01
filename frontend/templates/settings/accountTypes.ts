export type AccountUser = {
  id: string;
  initials: string;
  firstName: string;
  lastName: string;
  email: string;
  avatarUrl: string | null;
};

export type EmailMessage = 'success' | 'error' | null;
