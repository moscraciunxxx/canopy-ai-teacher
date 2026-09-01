import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Canopy · Private AI Learning System',
  description: 'An account-free, multilingual AI teacher with inspectable diagnosis, learning evidence, and course authoring.',
  openGraph: {
    title: 'Canopy · Private AI Learning System',
    description: 'Nine courses. Twenty languages. Private on-device AI.',
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
