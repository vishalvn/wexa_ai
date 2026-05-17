'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { Plus, RefreshCw, Share2, MoreHorizontal } from 'lucide-react';
import api from '@/lib/api';
import { format } from 'date-fns';

const COLORS = ['#4f63e7', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

interface Widget {
  id: number;
  title: string;
  widget_type: 'line_chart' | 'bar_chart' | 'pie_chart' | 'kpi_card' | 'table';
  query_config: {
    event_type?: string;
    interval?: string;
    metric?: string;
  };
  position_x: number;
  position_y: number;
  width: number;
  height: number;
}

interface Dashboard {
  id: number;
  name: string;
  refresh_interval: number;
  widgets: Widget[];
}

function WidgetCard({ widget }: { widget: Widget }) {
  const { data, isLoading } = useQuery({
    queryKey: ['widget-data', widget.id, widget.query_config],
    queryFn: async () => {
      if (!widget.query_config.event_type) return [];
      const { data } = await api.get('/events/query', {
        params: {
          event_type: widget.query_config.event_type,
          interval: widget.query_config.interval || '1h',
        }
      });
      return data;
    },
    enabled: !!widget.query_config.event_type,
    refetchInterval: 60000, // refresh every minute
  });

  const chartData = (data || []).map((d: any) => ({
    ...d,
    time: format(new Date(d.timestamp), 'HH:mm'),
  }));

  const renderChart = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-32 text-white/30 text-sm">
          Loading data...
        </div>
      );
    }

    if (!chartData.length) {
      return (
        <div className="flex items-center justify-center h-32 text-white/30 text-sm">
          No data for selected time range
        </div>
      );
    }

    switch (widget.widget_type) {
      case 'line_chart':
        return (
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <Tooltip
                contentStyle={{ background: '#22263a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Line type="monotone" dataKey="value" stroke="#4f63e7" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'bar_chart':
        return (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ background: '#22263a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
              <Bar dataKey="value" fill="#4f63e7" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'kpi_card':
        const total = chartData.reduce((sum: number, d: any) => sum + d.value, 0);
        const latest = chartData[chartData.length - 1]?.value || 0;
        return (
          <div className="flex flex-col justify-center h-full py-4">
            <p className="text-4xl font-bold text-white">{latest.toLocaleString()}</p>
            <p className="text-sm text-white/40 mt-1">Total: {total.toLocaleString()}</p>
          </div>
        );

      case 'pie_chart':
        return (
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={chartData.slice(0, 6)} dataKey="value" nameKey="time" cx="50%" cy="50%" outerRadius={70}>
                {chartData.slice(0, 6).map((_: any, i: number) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#22263a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        return <div className="text-white/30 text-sm text-center py-8">Chart type not supported</div>;
    }
  };

  return (
    <div className="card h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium">{widget.title}</h3>
        <button className="text-white/30 hover:text-white/70 p-1 rounded">
          <MoreHorizontal size={14} />
        </button>
      </div>
      <div className="flex-1">
        {renderChart()}
      </div>
    </div>
  );
}

export default function DashboardDetailPage() {
  const params = useParams();
  const dashboardId = params?.id as string;
  const [autoRefresh, setAutoRefresh] = useState(false);

  const { data: dashboard, isLoading, refetch } = useQuery<Dashboard>({
    queryKey: ['dashboard', dashboardId],
    queryFn: async () => {
      const { data } = await api.get(`/dashboards/${dashboardId}`);
      return data;
    },
  });

  // Auto-refresh based on dashboard's configured interval
  useEffect(() => {
    if (!dashboard?.refresh_interval) return;
    const interval = setInterval(() => refetch(), dashboard.refresh_interval * 1000);
    return () => clearInterval(interval);
  }, [dashboard?.refresh_interval, refetch]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-white/40">
        Loading dashboard...
      </div>
    );
  }

  if (!dashboard) return <div className="p-8 text-white/40">Dashboard not found</div>;

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold">{dashboard.name}</h1>
          <p className="text-white/40 text-sm mt-1">{dashboard.widgets.length} widgets</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 border border-white/10 hover:border-white/20 text-white/70 hover:text-white rounded-lg px-3 py-2 text-sm transition-colors"
          >
            <RefreshCw size={14} /> Refresh
          </button>
          <button className="flex items-center gap-2 border border-white/10 hover:border-white/20 text-white/70 hover:text-white rounded-lg px-3 py-2 text-sm transition-colors">
            <Share2 size={14} /> Share
          </button>
          <button className="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 text-white rounded-lg px-3 py-2 text-sm transition-colors">
            <Plus size={14} /> Add Widget
          </button>
        </div>
      </div>

      {/* Widget grid */}
      {dashboard.widgets.length === 0 ? (
        <div className="grid-bg rounded-2xl border border-dashed border-white/10 flex flex-col items-center justify-center h-80 text-center">
          <p className="text-white/30 mb-3">No widgets yet</p>
          <button className="text-brand-light text-sm hover:underline">Add your first widget</button>
        </div>
      ) : (
        <div className="grid grid-cols-12 gap-4">
          {dashboard.widgets.map((widget) => (
            <div
              key={widget.id}
              className={`col-span-${Math.min(widget.width, 12)}`}
              style={{ gridColumn: `span ${Math.min(widget.width, 12)}` }}
            >
              <WidgetCard widget={widget} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
