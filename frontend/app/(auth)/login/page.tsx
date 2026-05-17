'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthStore } from '@/lib/store';
import { BarChart3, Loader2 } from 'lucide-react';

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
});

type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();
  const [error, setError] = useState('');

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setError('');
    try {
      await login(data.email, data.password);
      router.push('/dashboards');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Login failed. Check your credentials.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface px-4">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center gap-2 justify-center mb-8">
          <div className="w-9 h-9 bg-brand-500 rounded-lg flex items-center justify-center">
            <BarChart3 size={20} className="text-white" />
          </div>
          <span className="text-xl font-semibold tracking-tight">DataPulse</span>
        </div>

        <div className="card space-y-5">
          <div>
            <h1 className="text-2xl font-semibold">Sign in</h1>
            <p className="text-sm text-white/50 mt-1">Welcome back to your analytics dashboard</p>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg px-4 py-3 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm text-white/70 mb-1.5">Email</label>
              <input
                {...register('email')}
                type="email"
                placeholder="you@company.com"
                className="w-full bg-surface-100 border border-white/10 rounded-lg px-4 py-2.5 text-sm placeholder-white/30 focus:outline-none focus:border-brand-500 transition-colors"
              />
              {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm text-white/70 mb-1.5">Password</label>
              <input
                {...register('password')}
                type="password"
                placeholder="••••••••"
                className="w-full bg-surface-100 border border-white/10 rounded-lg px-4 py-2.5 text-sm placeholder-white/30 focus:outline-none focus:border-brand-500 transition-colors"
              />
              {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-brand-500 hover:bg-brand-600 text-white rounded-lg py-2.5 text-sm font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoading && <Loader2 size={16} className="animate-spin" />}
              Sign in
            </button>
          </form>

          <p className="text-center text-sm text-white/50">
            Don&apos;t have an account?{' '}
            <Link href="/signup" className="text-brand-light hover:underline">
              Sign up free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
