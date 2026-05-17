'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Copy, RefreshCw, Check, Eye, EyeOff } from 'lucide-react';
import api from '@/lib/api';
import { useAuthStore } from '@/lib/store';

export default function SettingsPage() {
  const { user, loadUser } = useAuthStore();
  const [apiKeyVisible, setApiKeyVisible] = useState(false);
  const [copied, setCopied] = useState(false);

  const rotateMutation = useMutation({
    mutationFn: () => api.post('/auth/rotate-api-key'),
    onSuccess: () => loadUser(),
  });

  const copyApiKey = () => {
    if (user?.organization.api_key) {
      navigator.clipboard.writeText(user.organization.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!user) return null;

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-semibold mb-8">Settings</h1>

      {/* Organization section */}
      <section className="card mb-6">
        <h2 className="text-base font-semibold mb-4">Organization</h2>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-white/40 uppercase tracking-wider">Name</label>
            <p className="text-sm mt-1">{user.organization.name}</p>
          </div>
          <div>
            <label className="text-xs text-white/40 uppercase tracking-wider">Slug</label>
            <p className="text-sm mt-1 font-mono text-white/70">{user.organization.slug}</p>
          </div>
        </div>
      </section>

      {/* API Key section */}
      <section className="card mb-6">
        <h2 className="text-base font-semibold mb-1">API Key</h2>
        <p className="text-xs text-white/40 mb-4">
          Use this key to ingest events from your application. Keep it secret.
        </p>

        <div className="flex items-center gap-2">
          <div className="flex-1 bg-surface-100 border border-white/10 rounded-lg px-4 py-2.5 font-mono text-sm text-white/80 overflow-hidden">
            {apiKeyVisible
              ? user.organization.api_key
              : '•'.repeat(Math.min(40, user.organization.api_key.length))
            }
          </div>
          <button
            onClick={() => setApiKeyVisible(!apiKeyVisible)}
            className="p-2.5 border border-white/10 rounded-lg text-white/50 hover:text-white hover:border-white/20 transition-colors"
          >
            {apiKeyVisible ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
          <button
            onClick={copyApiKey}
            className="p-2.5 border border-white/10 rounded-lg text-white/50 hover:text-white hover:border-white/20 transition-colors"
          >
            {copied ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
          </button>
        </div>

        <button
          onClick={() => {
            if (confirm('Rotating the API key will revoke the current key. All integrations using the old key will stop working. Continue?')) {
              rotateMutation.mutate();
            }
          }}
          disabled={rotateMutation.isPending}
          className="mt-3 flex items-center gap-2 text-sm text-red-400 hover:text-red-300 disabled:opacity-50"
        >
          <RefreshCw size={14} className={rotateMutation.isPending ? 'animate-spin' : ''} />
          Rotate API key
        </button>
      </section>

      {/* SDK Usage */}
      <section className="card mb-6">
        <h2 className="text-base font-semibold mb-3">Quick Integration</h2>
        <p className="text-xs text-white/40 mb-3">Send events from your application using the REST API:</p>
        <pre className="bg-surface-100 rounded-lg p-4 text-xs font-mono text-white/70 overflow-x-auto">{`curl -X POST ${process.env.NEXT_PUBLIC_API_URL}/events/ \\
  -H "Authorization: Bearer ${user.organization.api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "event_type": "page_view",
    "user_id": "user_123",
    "properties": { "page": "/home" }
  }'`}</pre>
      </section>

      {/* Account */}
      <section className="card">
        <h2 className="text-base font-semibold mb-4">Account</h2>
        <div className="space-y-3">
          {[
            { label: 'Name', value: user.full_name },
            { label: 'Email', value: user.email },
            { label: 'Role', value: user.role.charAt(0).toUpperCase() + user.role.slice(1) },
          ].map(({ label, value }) => (
            <div key={label} className="flex justify-between items-center py-2 border-b border-white/5 last:border-0">
              <span className="text-sm text-white/50">{label}</span>
              <span className="text-sm">{value}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
