import { Routes, Route } from "react-router-dom";
import { ROUTES, ROLES } from "@/constants";
import LandingPage from "@/features/landing/LandingPage";
import WelcomePage from "@/features/auth/WelcomePage";
import LoginPage from "@/features/auth/LoginPage";
import SignupPage from "@/features/auth/SignupPage";
import ForgotPasswordPage from "@/features/auth/ForgotPasswordPage";
import ResetPasswordPage from "@/features/auth/ResetPasswordPage";
import OtpVerificationPage from "@/features/auth/OtpVerificationPage";
import LawyerDashboard from "@/features/dashboard/LawyerDashboard";
import ClientDashboard from "@/features/dashboard/ClientDashboard";
import StudentDashboard from "@/features/dashboard/StudentDashboard";
import CasesPage from "@/features/case-management/CasesPage";
import ChatPage from "@/features/chatbot/ChatPage";
import ResearchPage from "@/features/legal-research/ResearchPage";
import ResearchDetailPage from "@/features/legal-research/ResearchDetailPage";
import DocumentsPage from "@/features/document-analysis/DocumentsPage";
import CaseDetailPage from "@/features/case-management/CaseDetailPage";
import ContractsPage from "@/features/contract-drafting/ContractsPage";
import ContractDetailPage from "@/features/contract-drafting/ContractDetailPage";
import NotFoundPage from "@/components/common/NotFoundPage";
import ProtectedRoute from "./ProtectedRoute";

const ALL_ROLES = [ROLES.LAWYER, ROLES.CLIENT, ROLES.STUDENT];

export default function AppRouter() {
  return (
    <Routes>
      {/* Public */}
      <Route path={ROUTES.LANDING} element={<LandingPage />} />
      <Route path={ROUTES.WELCOME} element={<WelcomePage />} />
      <Route path={ROUTES.LOGIN} element={<LoginPage />} />
      <Route path={ROUTES.SIGNUP} element={<SignupPage />} />
      <Route path={ROUTES.FORGOT_PASSWORD} element={<ForgotPasswordPage />} />
      <Route path={ROUTES.RESET_PASSWORD} element={<ResetPasswordPage />} />
      <Route path={ROUTES.OTP} element={<OtpVerificationPage />} />

      {/* Role dashboards */}
      <Route
        path={ROUTES.LAWYER_DASHBOARD}
        element={
          <ProtectedRoute allowedRoles={[ROLES.LAWYER]}>
            <LawyerDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.CLIENT_DASHBOARD}
        element={
          <ProtectedRoute allowedRoles={[ROLES.CLIENT]}>
            <ClientDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.STUDENT_DASHBOARD}
        element={
          <ProtectedRoute allowedRoles={[ROLES.STUDENT]}>
            <StudentDashboard />
          </ProtectedRoute>
        }
      />

      {/* Module pages — accessible to all authenticated roles, internal RBAC
          enforced server-side per use case (e.g. only lawyers can create cases). */}
      <Route
        path={ROUTES.CASES}
        element={
          <ProtectedRoute allowedRoles={[ROLES.LAWYER, ROLES.CLIENT]}>
            <CasesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.CASE_DETAIL}
        element={
          <ProtectedRoute allowedRoles={[ROLES.LAWYER, ROLES.CLIENT]}>
            <CaseDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.CHATBOT}
        element={
          <ProtectedRoute allowedRoles={ALL_ROLES}>
            <ChatPage />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.RESEARCH}
        element={
          <ProtectedRoute allowedRoles={ALL_ROLES}>
            <ResearchPage />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.RESEARCH_DETAIL}
        element={
          <ProtectedRoute allowedRoles={ALL_ROLES}>
            <ResearchDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.DOCUMENTS}
        element={
          <ProtectedRoute allowedRoles={[ROLES.LAWYER, ROLES.CLIENT]}>
            <DocumentsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.CONTRACTS}
        element={
          <ProtectedRoute allowedRoles={[ROLES.LAWYER, ROLES.CLIENT]}>
            <ContractsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.CONTRACT_DETAIL}
        element={
          <ProtectedRoute allowedRoles={[ROLES.LAWYER, ROLES.CLIENT]}>
            <ContractDetailPage />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
