import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

// Bug 2.1 fix: Python backend takes 1.5-3s to boot PyTorch/CUDA on startup.
// The UI renders in ~200ms, so initial queries fail. We retry up to 8 times
// with a 2-second delay so voices and models always load automatically.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 8,
      retryDelay: 2000,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
)
