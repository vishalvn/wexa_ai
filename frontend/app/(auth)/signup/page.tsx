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
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  organization_name: z.string().min(2, 'Organization name is required'),
});

type FormData = z.infer<typeof schema>;

export default function SignupPage() {
  const router = useRouter();
  const { signup, isLoading } = useAuthStore();
  const [error, setError] = useState('');

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setError('');
    try {
      await signup(data);
      router.push('/dashboards');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Signup failed. Please try again.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface px-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm">
        <div className="flex items-center gap-2 justify-center mb-8">
          <div className="w-9 h-9 bg-brand-500 rounded-lg flex items-center justify-center">
            <BarChart3 size={20} className="text-white" />
          </div>
          <span className="text-xl font-semibold tracking-tight">DataPulse</span>
        </div>

        <div className="card space-y-5">
          <div>
            <h1 className="text-2xl font-semibold">Create account</h1>
            <p className="text-sm text-white/50 mt-1">Start tracking your metrics today</p>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg px-4 py-3 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {[
              { name: 'full_name' as const, label: 'Full Name', placeholder: 'Jane Smith', type: 'text' },
              { name: 'email' as const, label: 'Work Email', placeholder: 'jane@company.com', type: 'email' },
              { name: 'organization_name' as const, label: 'Organization', placeholder: 'Acme Inc.', type: 'text' },
              { name: 'password' as const, label: 'Password', placeholder: '8+ characters', type: 'password' },
            ].map(({ name, label, placeholder, type }) => (
              <div key={name}>
                <label className="block text-sm text-white/70 mb-1.5">{label}</label>
                <input
                  {...register(name)}
                  type={type}
                  placeholder={placeholder}
                  className="w-full bg-surface-100 border border-white/10 rounded-lg px-4 py-2.5 text-sm placeholder-white/30 focus:outline-none focus:border-brand-500 transition-colors"
                />
                {errors[name] && <p className="text-red-400 text-xs mt-1">{errors[name]?.message}</p>}
              </div>
            ))}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-brand-500 hover:bg-brand-600 text-white rounded-lg py-2.5 text-sm font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoading && <Loader2 size={16} className="animate-spin" />}
              Create account
            </button>
          </form>

          <p className="text-center text-sm text-white/50">
            Already have an account?{' '}
            <Link href="/login" className="text-brand-light hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
