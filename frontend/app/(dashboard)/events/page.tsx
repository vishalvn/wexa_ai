'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, Circle, Upload, ChevronDown } from 'lucide-react';
import api from '@/lib/api';
import { format } from 'date-fns';
import { clsx } from 'clsx';

interface Event {
  id: number;
  event_type: string;
  user_id: string | null;
  properties: Record<string, any>;
  timestamp: string;
  source: string;
}

const SOURCE_COLORS: Record<string, string> = {
  api: 'bg-brand-500/20 text-brand-light',
  csv: 'bg-green-500/20 text-green-400',
  webhook: 'bg-purple-500/20 text-purple-400',
};

export default function EventsPage() {
  const [liveMode, setLiveMode] = useState(true);
  const [events, setEvents] = useState<Event[]>([]);
  const [filter, setFilter] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Initial fetch + polling for live mode
  const { data: initialEvents, refetch } = useQuery<Event[]>({
    queryKey: ['events', 'stream'],
    queryFn: async () => {
      const { data } = await api.get('/events/stream?limit=100');
      return data;
    },
  });

  useEffect(() => {
    if (initialEvents) setEvents(initialEvents);
  }, [initialEvents]);

  // Poll every 5 seconds in live mode
  useEffect(() => {
    if (!liveMode) return;
    const interval = setInterval(() => refetch(), 5000);
    return () => clearInterval(interval);
  }, [liveMode, refetch]);

  // Auto-scroll to top when new events arrive
  useEffect(() => {
    if (liveMode && listRef.current) {
      listRef.current.scrollTop = 0;
    }
  }, [events, liveMode]);

  const handleCsvUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/events/upload-csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadResult(data);
      refetch();
    } catch (err: any) {
      setUploadResult({ error: err?.response?.data?.detail || 'Upload failed' });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const filteredEvents = filter
    ? events.filter(e =>
        e.event_type.includes(filter.toLowerCase()) ||
        e.user_id?.toLowerCase().includes(filter.toLowerCase())
      )
    : events;

  return (
    <div className="p-8 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Live Events</h1>
          {liveMode && (
            <span className="flex items-center gap-1.5 text-xs text-green-400 bg-green-500/10 px-2 py-1 rounded-full">
              <Circle size={6} className="fill-green-400 animate-pulse" />
              Live
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* CSV Upload */}
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            onChange={handleCsvUpload}
            className="hidden"
          />
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="flex items-center gap-2 border border-white/10 hover:border-white/20 text-white/70 hover:text-white rounded-lg px-3 py-2 text-sm transition-colors disabled:opacity-50"
          >
            <Upload size={14} />
            {uploading ? 'Uploading...' : 'Upload CSV'}
          </button>

          {/* Live toggle */}
          <button
            onClick={() => setLiveMode(!liveMode)}
            className={clsx(
              'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors',
              liveMode
                ? 'bg-green-500/15 text-green-400 hover:bg-green-500/20'
                : 'border border-white/10 text-white/60 hover:text-white'
            )}
          >
            <Activity size={14} />
            {liveMode ? 'Live On' : 'Live Off'}
          </button>
        </div>
      </div>

      {/* Upload result banner */}
      {uploadResult && (
        <div className={clsx(
          'mb-4 rounded-lg px-4 py-3 text-sm',
          uploadResult.error
            ? 'bg-red-500/10 border border-red-500/20 text-red-400'
            : 'bg-green-500/10 border border-green-500/20 text-green-400'
        )}>
          {uploadResult.error
            ? uploadResult.error
            : `Accepted ${uploadResult.accepted} events. Rejected ${uploadResult.rejected}.`
          }
        </div>
      )}

      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        {[
          { label: 'Total Events', value: events.length },
          { label: 'Event Types', value: new Set(events.map(e => e.event_type)).size },
          { label: 'Unique Users', value: new Set(events.filter(e => e.user_id).map(e => e.user_id)).size },
          { label: 'Last Minute', value: events.filter(e => new Date(e.timestamp) > new Date(Date.now() - 60000)).length },
        ].map(({ label, value }) => (
          <div key={label} className="card py-4">
            <p className="text-2xl font-bold">{value}</p>
            <p className="text-xs text-white/40 mt-1">{label}</p>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="mb-4">
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter by event type or user ID..."
          className="w-full max-w-sm bg-surface-50 border border-white/10 rounded-lg px-4 py-2 text-sm placeholder-white/30 focus:outline-none focus:border-brand-500 transition-colors"
        />
      </div>

      {/* Event stream */}
      <div
        ref={listRef}
        className="flex-1 overflow-y-auto space-y-1.5 min-h-0"
      >
        {filteredEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-white/30">
            <Activity size={32} className="mb-3 opacity-50" />
            <p className="text-sm">No events yet. Start ingesting data or upload a CSV.</p>
          </div>
        ) : (
          filteredEvents.map((event, i) => (
            <EventRow key={event.id} event={event} isNew={liveMode && i < 3} />
          ))
        )}
      </div>
    </div>
  );
}

function EventRow({ event, isNew }: { event: Event; isNew: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const hasProperties = Object.keys(event.properties).length > 0;

  return (
    <div className={clsx(
      'bg-surface-50 border border-white/8 rounded-lg overflow-hidden transition-all',
      isNew && 'border-brand-500/30 bg-brand-500/5'
    )}>
      <div
        className="flex items-center gap-4 px-4 py-3 cursor-pointer hover:bg-white/[0.02]"
        onClick={() => hasProperties && setExpanded(!expanded)}
      >
        {/* Timestamp */}
        <span className="text-xs text-white/30 w-20 flex-shrink-0 font-mono">
          {format(new Date(event.timestamp), 'HH:mm:ss')}
        </span>

        {/* Event type */}
        <span className="text-sm font-medium text-white/90 min-w-[120px]">
          {event.event_type}
        </span>

        {/* User ID */}
        <span className="text-xs text-white/40 flex-1 truncate">
          {event.user_id ? `user: ${event.user_id}` : 'anonymous'}
        </span>

        {/* Source badge */}
        <span className={clsx(
          'text-xs px-2 py-0.5 rounded-full',
          SOURCE_COLORS[event.source] || 'bg-white/10 text-white/50'
        )}>
          {event.source}
        </span>

        {/* Expand chevron */}
        {hasProperties && (
          <ChevronDown
            size={14}
            className={clsx('text-white/30 transition-transform flex-shrink-0', expanded && 'rotate-180')}
          />
        )}
      </div>

      {/* Expanded properties */}
      {expanded && hasProperties && (
        <div className="px-4 pb-3 border-t border-white/5">
          <pre className="text-xs text-white/50 font-mono mt-2 overflow-x-auto">
            {JSON.stringify(event.properties, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
