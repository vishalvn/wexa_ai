'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar } from '@/components/Sidebar';
import { useAuthStore } from '@/lib/store';
import { useWebSocket } from '@/lib/useWebSocket';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, loadUser } = useAuthStore();

  // Initialize WebSocket for real-time updates
  useWebSocket();

  useEffect(() => {
    loadUser();
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen overflow-hidden relative">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
