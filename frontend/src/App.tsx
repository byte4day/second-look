import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout.tsx'
import { AcceptInvitation } from './pages/AcceptInvitation.tsx'
import { CheckMessage } from './pages/CheckMessage.tsx'
import { ConfirmRemoveContact } from './pages/ConfirmRemoveContact.tsx'
import { Debrief } from './pages/Debrief.tsx'
import { Family } from './pages/Family.tsx'
import { HelpNow } from './pages/HelpNow.tsx'
import { Home } from './pages/Home.tsx'
import { Practise } from './pages/Practise.tsx'
import { PractiseChat } from './pages/PractiseChat.tsx'
import { Result } from './pages/Result.tsx'
import { ScamsNearMe } from './pages/ScamsNearMe.tsx'
import { PreferencesProvider } from './hooks/usePreferences.ts'
import { Settings } from './pages/Settings.tsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <PreferencesProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="check" element={<CheckMessage />} />
            <Route path="check/result" element={<Result />} />
            <Route path="practise" element={<Practise />} />
            <Route path="practise/chat/:sessionId" element={<PractiseChat />} />
            <Route path="practise/debrief/:sessionId" element={<Debrief />} />
            <Route path="help" element={<HelpNow />} />
            <Route path="family" element={<Family />} />
            <Route path="family/remove/:contactId" element={<ConfirmRemoveContact />} />
            <Route path="scams-near-me" element={<ScamsNearMe />} />
            <Route path="settings" element={<Settings />} />
            <Route path="invite/:token" element={<AcceptInvitation />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
      </PreferencesProvider>
    </QueryClientProvider>
  )
}