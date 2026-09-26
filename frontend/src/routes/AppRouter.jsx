import { Routes, Route, Navigate } from "react-router-dom";
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
import ComingSoonPage from "@/components/common/ComingSoonPage";
import DesignSystemPage from "@/features/design-system/DesignSystemPage";
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
      {/* Design system v1 token test page — not linked from the app */}
      <Route path="/design-system" element={<DesignSystemPage />} />

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

      {/* In-progress modules — show a clean "Coming Soon" page inside the
          dashboard shell instead of bouncing to landing. */}
      <Route
        path="/lawyer/clients"
        element={
          <ProtectedRoute allowedRoles={[ROLES.LAWYER]}>
            <ComingSoonPage
              title="Clients"
              description="A unified directory of all your clients with case counts, contact details, and quick assign-to-case actions. Currently you can manage clients via the case-create form (email-based assignment)."
              eta="Iteration 3"
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="/lawyer/schedule"
        element={
          <ProtectedRoute allowedRoles={[ROLES.LAWYER]}>
            <ComingSoonPage
              title="Schedule"
              description="Calendar view of all your hearings, deadlines, and client meetings with email reminders. Hearings can be tracked today via case status (HEARING_SCHEDULED)."
              eta="Iteration 3"
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="/client/upload"
        element={
          <ProtectedRoute allowedRoles={[ROLES.CLIENT]}>
            <ComingSoonPage
              title="Upload & OCR"
              description="Use the Documents tab to upload PDFs and images. OCR runs automatically on upload."
              eta="Available now via Documents"
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="/student/library"
        element={
          <ProtectedRoute allowedRoles={[ROLES.STUDENT]}>
            <ComingSoonPage
              title="Library"
              description="Curated reading lists, landmark judgments, and drafting templates for law students. Until then, use Legal Research to explore the full Pakistani corpus."
              eta="Iteration 3"
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="/student/progress"
        element={
          <ProtectedRoute allowedRoles={[ROLES.STUDENT]}>
            <ComingSoonPage
              title="Progress"
              description="Track exercises completed, average scores, and learning streaks across the practice simulator."
              eta="Iteration 3"
            />
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
      <Route
        path={ROUTES.SIMULATOR}
        element={
          <ProtectedRoute allowedRoles={[ROLES.STUDENT]}>
            <ComingSoonPage
              title="Practice Simulator"
              description="Interactive scenarios for law students — drafting petitions, cross-examination, and applying statutes to fact patterns, with AI feedback."
              eta="Iteration 3"
            />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.NOTIFICATIONS}
        element={
          <ProtectedRoute allowedRoles={ALL_ROLES}>
            <ComingSoonPage
              title="Notifications"
              description="In-app + email alerts for hearings, deadlines, document uploads, and case status changes."
              eta="Iteration 3"
            />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.PROFILE}
        element={
          <ProtectedRoute allowedRoles={ALL_ROLES}>
            <ComingSoonPage
              title="Profile"
              description="Edit your name, phone, password, and role-specific fields (bar license, CNIC, etc.)."
              eta="Iteration 3"
            />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to={ROUTES.LANDING} replace />} />
    </Routes>
  );
}
