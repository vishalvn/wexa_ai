'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { LayoutDashboard, Plus, Trash2, Share2, RefreshCw } from 'lucide-react';
import api from '@/lib/api';

interface Dashboard {
  id: number;
  name: string;
  description: string | null;
  is_public: boolean;
  refresh_interval: number;
  widgets: any[];
}

async function fetchDashboards(): Promise<Dashboard[]> {
  const { data } = await api.get('/dashboards/');
  return data;
}

async function createDashboard(payload: { name: string; description?: string }) {
  const { data } = await api.post('/dashboards/', payload);
  return data;
}

export default function DashboardsPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');

  const { data: dashboards = [], isLoading } = useQuery({
    queryKey: ['dashboards'],
    queryFn: fetchDashboards,
  });

  const createMutation = useMutation({
    mutationFn: createDashboard,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      setShowCreate(false);
      setNewName('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/dashboards/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['dashboards'] }),
  });

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold">Dashboards</h1>
          <p className="text-white/50 text-sm mt-1">Create and manage your analytics dashboards</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          <Plus size={16} /> New Dashboard
        </button>
      </div>

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="card w-full max-w-sm space-y-4">
            <h2 className="text-lg font-semibold">New Dashboard</h2>
            <input
              autoFocus
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && newName && createMutation.mutate({ name: newName })}
              placeholder="e.g. Product Analytics"
              className="w-full bg-surface-100 border border-white/10 rounded-lg px-4 py-2.5 text-sm placeholder-white/30 focus:outline-none focus:border-brand-500"
            />
            <div className="flex gap-3">
              <button
                onClick={() => setShowCreate(false)}
                className="flex-1 border border-white/10 rounded-lg py-2 text-sm text-white/70 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => newName && createMutation.mutate({ name: newName })}
                disabled={!newName || createMutation.isPending}
                className="flex-1 bg-brand-500 hover:bg-brand-600 text-white rounded-lg py-2 text-sm font-medium transition-colors disabled:opacity-50"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-40 text-white/40">Loading...</div>
      ) : dashboards.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <LayoutDashboard size={40} className="text-white/20 mb-4" />
          <p className="text-white/50 mb-2">No dashboards yet</p>
          <button
            onClick={() => setShowCreate(true)}
            className="text-brand-light text-sm hover:underline"
          >
            Create your first dashboard
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {dashboards.map((dashboard) => (
            <div key={dashboard.id} className="card hover:border-white/15 transition-colors group">
              <div className="flex items-start justify-between">
                <Link href={`/dashboards/${dashboard.id}`}>
                  <h3 className="font-medium text-sm group-hover:text-brand-light transition-colors">
                    {dashboard.name}
                  </h3>
                  {dashboard.description && (
                    <p className="text-xs text-white/40 mt-1">{dashboard.description}</p>
                  )}
                  <div className="flex items-center gap-3 mt-4 text-xs text-white/40">
                    <span>{dashboard.widgets.length} widgets</span>
                    {dashboard.is_public && (
                      <span className="flex items-center gap-1 text-green-400">
                        <Share2 size={10} /> Public
                      </span>
                    )}
                    {dashboard.refresh_interval > 0 && (
                      <span className="flex items-center gap-1">
                        <RefreshCw size={10} /> {dashboard.refresh_interval}s
                      </span>
                    )}
                  </div>
                </Link>
                <button
                  onClick={(e) => { e.preventDefault(); deleteMutation.mutate(dashboard.id); }}
                  className="opacity-0 group-hover:opacity-100 p-1.5 text-white/30 hover:text-red-400 transition-all rounded"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
