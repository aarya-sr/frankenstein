import { StrictMode, lazy, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import ChatApp from './ChatApp'
import './index.css'

const PreviewApp = lazy(() => import('./preview/PreviewApp'))

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/chat" element={<ChatApp />} />
        <Route path="/preview/:sessionId" element={
          <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-text-tertiary">Loading preview...</div>}>
            <PreviewApp />
          </Suspense>
        } />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
