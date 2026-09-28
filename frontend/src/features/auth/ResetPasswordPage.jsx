import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import AuthShell from "@/layouts/AuthShell";
import { authApi, extractAuthError } from "./api";
import { ROUTES } from "@/constants";

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const email = searchParams.get("email") || "";
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const mutation = useMutation({
    mutationFn: () => authApi.resetPassword({ email, otp, new_password: newPassword }),
    onSuccess: () => {
      toast.success("Password reset.", { description: "Sign in with your new password." });
      navigate(ROUTES.LOGIN, { replace: true, state: { prefillEmail: email } });
    },
    onError: (err) => {
      const { message, hint } = extractAuthError(err);
      toast.error(message, { description: hint });
    },
  });

  const resendMutation = useMutation({
    mutationFn: () => authApi.forgotPassword(email),
    onSuccess: () => {
      toast.success("New code sent.", { description: `Check ${email}.` });
    },
    onError: (err) => {
      const { message, hint } = extractAuthError(err);
      toast.error(message, { description: hint });
    },
  });

  const submit = (e) => {
    e.preventDefault();
    if (otp.length < 4 || newPassword.length < 8) return;
    mutation.mutate();
  };

  return (
    <AuthShell
      heroTitle="Set a new password."
      heroSubtitle={
        email
          ? `Enter the code we sent to ${email}, then choose a new password.`
          : "Enter the reset code and a new password."
      }
    >
      <p className="ds-eyebrow">Reset password</p>
      <h1 className="font-ds-serif font-medium text-[40px] leading-[48px] sm:text-[48px] sm:leading-[56px] tracking-tight text-ds-text mt-3">
        Set a new password
      </h1>
      <p className="ds-body text-ds-text-2 mt-2">Check your inbox for the 6-digit code.</p>

      <form onSubmit={submit} className="mt-8 space-y-6">
        <div>
          <label htmlFor="rp-code" className="ds-label mb-2.5">6-digit code</label>
          <input
            id="rp-code"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            placeholder="••••••"
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
            required
            minLength={4}
            className="ds-input tracking-[0.3em]"
          />
        </div>

        <div>
          <label htmlFor="rp-password" className="ds-label mb-2.5">New password</label>
          <div className="relative">
            <input
              id="rp-password"
              type={showPassword ? "text" : "password"}
              placeholder="At least 8 characters"
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
              className="ds-input pr-12"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-1 top-1/2 -translate-y-1/2 h-11 w-11 flex items-center justify-center text-ds-text-2 hover:text-ds-text rounded-ds"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
          {newPassword.length > 0 && newPassword.length < 8 && (
            <p className="mt-2 text-[14px] leading-[20px] text-ds-text-2">At least 8 characters.</p>
          )}
        </div>

        <button
          type="submit"
          disabled={mutation.isPending || otp.length < 4 || newPassword.length < 8}
          className="ds-btn-primary w-full min-h-[48px]"
        >
          {mutation.isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Resetting" /> : "Reset password"}
        </button>

        <p className="text-center">
          <button
            type="button"
            onClick={() => resendMutation.mutate()}
            disabled={resendMutation.isPending}
            className="ds-link-seal text-[15px] disabled:text-ds-text-2 disabled:no-underline"
          >
            {resendMutation.isPending ? "Sending…" : "Resend reset code"}
          </button>
        </p>
      </form>

      <p className="mt-8 text-center text-[16px] text-ds-text-2">
        Remembered your password?{" "}
        <Link to={ROUTES.LOGIN} className="ds-link-seal">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
