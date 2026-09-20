import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import AuthShell from "@/layouts/AuthShell";
import AppButton from "@/components/ui/AppButton";
import { authApi, extractAuthError } from "./api";
import { ROUTES } from "@/constants";
import { cnInput } from "@/lib/formStyles";

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
      <h2 className="font-editorial text-2xl text-ink-text mb-1">Reset password</h2>
      <p className="text-sm text-ink-muted mb-6">
        Check your inbox for the 6-digit code.
      </p>

      <div className="border-b border-hairline-subtle mb-8" />

      <form onSubmit={submit} className="space-y-6">
        <div>
          <label className="block text-sm text-ink-muted mb-1.5">6-digit code</label>
          <input
            inputMode="numeric"
            maxLength={6}
            placeholder="••••••"
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
            required
            minLength={4}
            className={cnInput(false)}
          />
        </div>

        <div>
          <label className="block text-sm text-ink-muted mb-1.5">New password</label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="At least 8 characters"
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
              className={cnInput(false, "pr-8")}
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-0 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink-text"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        <AppButton
          type="submit"
          disabled={mutation.isPending || otp.length < 4 || newPassword.length < 8}
          className="w-full"
        >
          {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Reset password"}
        </AppButton>

        <div className="text-center">
          <button
            type="button"
            onClick={() => resendMutation.mutate()}
            disabled={resendMutation.isPending}
            className="text-xs text-brick hover:underline underline-offset-2 disabled:text-ink-muted"
          >
            {resendMutation.isPending ? "Sending…" : "Resend reset code"}
          </button>
        </div>
      </form>

      <div className="mt-8 pt-6 border-t border-hairline-subtle text-center">
        <Link to={ROUTES.LOGIN} className="text-sm text-brick hover:underline underline-offset-2">
          Back to sign in
        </Link>
      </div>
    </AuthShell>
  );
}
