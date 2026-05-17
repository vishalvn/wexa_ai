'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export function Providers({ children }: { children: React.ReactNode }) {
  // useState ensures each browser session gets its own QueryClient
  const [queryClient] = useState(
    () => new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 30 * 1000,       // data is fresh for 30 seconds
          retry: 1,                    // retry failed queries once
          refetchOnWindowFocus: true,  // refresh when user returns to tab
        },
      },
    })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
