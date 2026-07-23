import type { ReactNode } from 'react';
import { NavBar } from './NavBar';
import { UtilityDock } from './UtilityDock.tsx';

interface Props {
  children: ReactNode;
}

export function AppLayout({ children }: Props) {
  return (
    <>
      <NavBar />
      <main>{children}</main>
      <UtilityDock />
    </>
  );
}