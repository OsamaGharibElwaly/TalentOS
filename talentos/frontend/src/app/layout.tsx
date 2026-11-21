import type { Metadata } from 'next';
import { connection } from 'next/server';
import type { ReactNode } from 'react';
import AppShell from '../components/shell/AppShell';
import './globals.css';

export const metadata: Metadata = {
  title: 'TalentOS',
  description: 'Local-first AI-powered hiring workspace',
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  await connection();
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
