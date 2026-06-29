import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { SiteConfigProvider } from '@/contexts/SiteConfigContext';
import Layout from '@/components/Layout';
import RequireAuth from '@/components/RequireAuth';
import RequireAdmin from '@/components/RequireAdmin';
import HomePage from '@/pages/HomePage';
import LoginPage from '@/pages/LoginPage';
import SignupPage from '@/pages/SignupPage';
import ForgotPasswordPage from '@/pages/ForgotPasswordPage';
import ResetPasswordPage from '@/pages/ResetPasswordPage';
import VerifyEmailPage from '@/pages/VerifyEmailPage';
import UploadPage from '@/pages/UploadPage';
import QuizPage from '@/pages/QuizPage';
import HistoryPage from '@/pages/HistoryPage';
import ProfilePage from '@/pages/ProfilePage';
import DashboardPage from '@/pages/DashboardPage';
import ReviewMistakesPage from '@/pages/ReviewMistakesPage';
import AdminPage from '@/pages/admin/AdminPage';
import MentionsLegalesPage from '@/pages/legal/MentionsLegalesPage';
import ConfidentialitePage from '@/pages/legal/ConfidentialitePage';
import CGUPage from '@/pages/legal/CGUPage';
import CookiesPage from '@/pages/legal/CookiesPage';

export default function App() {
  return (
    <ThemeProvider>
      <SiteConfigProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route element={<Layout />}>
                <Route index element={<HomePage />} />
                <Route path="login" element={<LoginPage />} />
                <Route path="signup" element={<SignupPage />} />
                <Route path="forgot-password" element={<ForgotPasswordPage />} />
                <Route path="reset-password" element={<ResetPasswordPage />} />
                <Route path="verify-email" element={<VerifyEmailPage />} />

                {/* Pages légales (publiques, à compléter par les étudiants) */}
                <Route path="legal/mentions-legales" element={<MentionsLegalesPage />} />
                <Route path="legal/confidentialite" element={<ConfidentialitePage />} />
                <Route path="legal/cgu" element={<CGUPage />} />
                <Route path="legal/cookies" element={<CookiesPage />} />

                {/* Routes protégées */}
                <Route
                  path="upload"
                  element={
                    <RequireAuth>
                      <UploadPage />
                    </RequireAuth>
                  }
                />
                <Route
                  path="quiz/:id"
                  element={
                    <RequireAuth>
                      <QuizPage />
                    </RequireAuth>
                  }
                />
                <Route
                  path="history"
                  element={
                    <RequireAuth>
                      <HistoryPage />
                    </RequireAuth>
                  }
                />
                <Route
                  path="profile"
                  element={
                    <RequireAuth>
                      <ProfilePage />
                    </RequireAuth>
                  }
                />
                <Route
                  path="dashboard"
                  element={
                    <RequireAuth>
                      <DashboardPage />
                    </RequireAuth>
                  }
                />
                <Route
                  path="review"
                  element={
                    <RequireAuth>
                      <ReviewMistakesPage />
                    </RequireAuth>
                  }
                />
                <Route
                  path="admin"
                  element={
                    <RequireAdmin>
                      <AdminPage />
                    </RequireAdmin>
                  }
                />

                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </SiteConfigProvider>
    </ThemeProvider>
  );
}
