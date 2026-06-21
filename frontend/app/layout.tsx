import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Parts Intelligence',
  description: 'Multi-agent workflow for parts identification, serial recovery, routing, and supply chain analysis',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
