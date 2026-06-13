import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from '@/components/layout/AppLayout'
import LoginPage from '@/pages/LoginPage'
import HomePage from '@/pages/HomePage'
import ClaimSummaryPage from '@/pages/ClaimSummaryPage'
import AssistantPage from '@/pages/AssistantPage'
import DraftNotePage from '@/pages/DraftNotePage'
import ApprovalPage from '@/pages/ApprovalPage'
import AuditTimelinePage from '@/pages/AuditTimelinePage'
import ExecutiveDashboardPage from '@/pages/ExecutiveDashboardPage'
import PlaceholderPage from '@/pages/PlaceholderPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<ExecutiveDashboardPage />} />
        <Route path="home" element={<HomePage />} />
        <Route path="claims/:claimId/summary" element={<ClaimSummaryPage />} />
        <Route path="claims/:claimId/assistant" element={<AssistantPage />} />
        <Route path="claims/:claimId/draft-note" element={<DraftNotePage />} />
        <Route path="claims/:claimId/approval" element={<ApprovalPage />} />
        <Route path="claims/:claimId/write-progress" element={<PlaceholderPage title="Governed Write" description="Validated note write-back to ClaimCenter after approval." step={7} />} />
        <Route path="claims/:claimId/write-completed" element={<PlaceholderPage title="Write Completed" description="Confirmation and final audit record of the completed write." step={7} />} />
        <Route path="claims/:claimId/audit" element={<AuditTimelinePage />} />
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
