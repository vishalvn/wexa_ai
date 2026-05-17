'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell, Plus, CheckCircle, AlertTriangle, Clock, VolumeX } from 'lucide-react';
import api from '@/lib/api';
import { format } from 'date-fns';
import { clsx } from 'clsx';

interface Alert {
  id: number;
  name: string;
  event_type: string;
  condition: string;
  threshold: number;
  evaluation_window_minutes: number;
  status: 'active' | 'triggered' | 'resolved' | 'muted';
  last_triggered_at: string | null;
  last_triggered_value: number | null;
  notification_channels: Record<string, any>;
}

const statusConfig = {
  active: { label: 'Active', icon: CheckCircle, color: 'text-green-400' },
  triggered: { label: 'Triggered', icon: AlertTriangle, color: 'text-red-400' },
  resolved: { label: 'Resolved', icon: CheckCircle, color: 'text-white/40' },
  muted: { label: 'Muted', icon: VolumeX, color: 'text-yellow-400' },
};

const conditionLabel: Record<string, string> = {
  gt: '>', lt: '<', eq: '=', neq: '≠'
};

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: '', event_type: '', condition: 'gt', threshold: 100,
    evaluation_window_minutes: 5,
    notification_channels: { email: [] as string[] },
  });

  const { data: alerts = [], isLoading } = useQuery<Alert[]>({
    queryKey: ['alerts'],
    queryFn: async () => { const { data } = await api.get('/alerts/'); return data; },
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof form) => api.post('/alerts/', data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['alerts'] }); setShowCreate(false); },
  });

  const resolveMutation = useMutation({
    mutationFn: (id: number) => api.post(`/alerts/${id}/resolve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  });

  const snoozeMutation = useMutation({
    mutationFn: ({ id, minutes }: { id: number; minutes: number }) =>
      api.post(`/alerts/${id}/snooze`, { minutes }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold">Alerts</h1>
          <p className="text-white/50 text-sm mt-1">Monitor metrics and get notified when thresholds are crossed</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          <Plus size={16} /> New Alert
        </button>
      </div>

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="card w-full max-w-md space-y-4">
            <h2 className="text-lg font-semibold">Create Alert Rule</h2>

            {[
              { key: 'name', label: 'Alert Name', placeholder: 'High Error Rate' },
              { key: 'event_type', label: 'Event Type', placeholder: 'error' },
            ].map(({ key, label, placeholder }) => (
              <div key={key}>
                <label className="block text-sm text-white/70 mb-1.5">{label}</label>
                <input
                  value={(form as any)[key]}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  placeholder={placeholder}
                  className="w-full bg-surface-100 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-brand-500"
                />
              </div>
            ))}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-white/70 mb-1.5">Condition</label>
                <select
                  value={form.condition}
                  onChange={(e) => setForm({ ...form, condition: e.target.value })}
                  className="w-full bg-surface-100 border border-white/10 rounded-lg px-3 py-2.5 text-sm focus:outline-none"
                >
                  <option value="gt">Greater than (&gt;)</option>
                  <option value="lt">Less than (&lt;)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-white/70 mb-1.5">Threshold</label>
                <input
                  type="number"
                  value={form.threshold}
                  onChange={(e) => setForm({ ...form, threshold: Number(e.target.value) })}
                  className="w-full bg-surface-100 border border-white/10 rounded-lg px-3 py-2.5 text-sm focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-white/70 mb-1.5">Evaluation Window (minutes)</label>
              <input
                type="number"
                value={form.evaluation_window_minutes}
                onChange={(e) => setForm({ ...form, evaluation_window_minutes: Number(e.target.value) })}
                className="w-full bg-surface-100 border border-white/10 rounded-lg px-3 py-2.5 text-sm focus:outline-none"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setShowCreate(false)}
                className="flex-1 border border-white/10 rounded-lg py-2 text-sm text-white/70 hover:text-white"
              >Cancel</button>
              <button
                onClick={() => createMutation.mutate(form)}
                disabled={!form.name || !form.event_type}
                className="flex-1 bg-brand-500 hover:bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-50"
              >Create Alert</button>
            </div>
          </div>
        </div>
      )}

      {/* Alerts list */}
      {isLoading ? (
        <div className="text-center text-white/40 py-20">Loading...</div>
      ) : alerts.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64">
          <Bell size={40} className="text-white/20 mb-4" />
          <p className="text-white/50">No alert rules configured</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => {
            const status = statusConfig[alert.status];
            const StatusIcon = status.icon;
            return (
              <div key={alert.id} className="card flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <StatusIcon size={18} className={status.color} />
                  <div>
                    <p className="text-sm font-medium">{alert.name}</p>
                    <p className="text-xs text-white/40 mt-0.5">
                      <code className="bg-surface-100 px-1.5 py-0.5 rounded text-white/60">{alert.event_type}</code>
                      {' '}{conditionLabel[alert.condition]} {alert.threshold}
                      {' '}over {alert.evaluation_window_minutes}m
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {alert.last_triggered_at && (
                    <div className="text-right">
                      <p className="text-xs text-white/40">Last triggered</p>
                      <p className="text-xs text-white/70">
                        {format(new Date(alert.last_triggered_at), 'MMM d, HH:mm')}
                        {alert.last_triggered_value != null && ` (${alert.last_triggered_value})`}
                      </p>
                    </div>
                  )}

                  <span className={clsx('text-xs font-medium px-2 py-1 rounded-full', {
                    'bg-green-500/15 text-green-400': alert.status === 'active',
                    'bg-red-500/15 text-red-400': alert.status === 'triggered',
                    'bg-white/5 text-white/30': alert.status === 'resolved',
                    'bg-yellow-500/15 text-yellow-400': alert.status === 'muted',
                  })}>
                    {status.label}
                  </span>

                  <div className="flex gap-2">
                    {alert.status === 'triggered' && (
                      <button
                        onClick={() => resolveMutation.mutate(alert.id)}
                        className="text-xs border border-white/10 rounded px-2 py-1 text-white/60 hover:text-white hover:border-white/20"
                      >
                        Resolve
                      </button>
                    )}
                    {alert.status !== 'muted' && (
                      <button
                        onClick={() => snoozeMutation.mutate({ id: alert.id, minutes: 60 })}
                        className="text-xs border border-white/10 rounded px-2 py-1 text-white/60 hover:text-white"
                      >
                        Snooze 1h
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
