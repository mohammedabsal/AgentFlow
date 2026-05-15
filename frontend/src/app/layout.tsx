import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AgentFlow Studio',
  description: 'Lovable-style autonomous AI full-stack app platform',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
