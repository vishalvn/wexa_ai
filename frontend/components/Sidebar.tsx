'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart3, LayoutDashboard, Bell, Settings,
  Activity, LogOut, ChevronLeft, ChevronRight
} from 'lucide-react';
import { useAuthStore, useDashboardStore } from '@/lib/store';
import { clsx } from 'clsx';

const navItems = [
  { href: '/dashboards', label: 'Dashboards', icon: LayoutDashboard },
  { href: '/events', label: 'Live Events', icon: Activity },
  { href: '/alerts', label: 'Alerts', icon: Bell },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const { sidebarOpen, toggleSidebar } = useDashboardStore();

  return (
    <aside className={clsx(
      'flex flex-col h-screen bg-surface-50 border-r border-white/8 transition-all duration-200',
      sidebarOpen ? 'w-56' : 'w-16'
    )}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-white/8">
        <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center flex-shrink-0">
          <BarChart3 size={16} className="text-white" />
        </div>
        {sidebarOpen && (
          <span className="font-semibold text-sm tracking-tight">DataPulse</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                active
                  ? 'bg-brand-500/15 text-brand-light'
                  : 'text-white/60 hover:text-white hover:bg-white/5'
              )}
            >
              <Icon size={18} className="flex-shrink-0" />
              {sidebarOpen && <span>{label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="border-t border-white/8 p-3 space-y-2">
        {sidebarOpen && user && (
          <div className="px-2 py-1">
            <p className="text-xs font-medium truncate">{user.full_name}</p>
            <p className="text-xs text-white/40 truncate">{user.organization.name}</p>
          </div>
        )}
        <button
          onClick={() => logout()}
          className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-white/60 hover:text-red-400 hover:bg-red-500/10 transition-colors"
        >
          <LogOut size={16} className="flex-shrink-0" />
          {sidebarOpen && <span>Sign out</span>}
        </button>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-20 w-6 h-6 bg-surface-100 border border-white/10 rounded-full flex items-center justify-center text-white/50 hover:text-white hover:border-white/30 transition-colors"
      >
        {sidebarOpen ? <ChevronLeft size={12} /> : <ChevronRight size={12} />}
      </button>
    </aside>
  );
}
