import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { ShieldCheck, Eye, EyeOff } from "lucide-react";
import AuthLayout from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Spinner from "@/components/common/Spinner";
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
    mutationFn: () =>
      authApi.resetPassword({ email, otp, new_password: newPassword }),
    onSuccess: () => {
      toast.success("Password reset.", {
        description: "Sign in with your new password.",
      });
      navigate(ROUTES.LOGIN, {
        replace: true,
        state: { prefillEmail: email },
      });
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
    <AuthLayout
      title="Set a new password"
      subtitle={
        email
          ? `Enter the code we sent to ${email}, then choose a new password.`
          : "Enter the reset code and a new password."
      }
      footer={
        <Link
          to={ROUTES.LOGIN}
          className="text-legal-gold hover:underline font-medium text-sm"
        >
          Back to sign in
        </Link>
      }
    >
      <form onSubmit={submit} className="space-y-5">
        <div className="space-y-2">
          <Label>6-digit code</Label>
          <Input
            inputMode="numeric"
            maxLength={6}
            placeholder="••••••"
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
            required
            minLength={4}
          />
        </div>

        <div className="space-y-2">
          <Label>New password</Label>
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              placeholder="At least 8 characters"
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        <Button
          type="submit"
          variant="gold"
          size="lg"
          className="w-full"
          disabled={mutation.isPending || otp.length < 4 || newPassword.length < 8}
        >
          {mutation.isPending ? (
            <Spinner size={18} />
          ) : (
            <>
              <ShieldCheck className="h-4 w-4" />
              Reset password
            </>
          )}
        </Button>

        <div className="text-center text-xs">
          <button
            type="button"
            onClick={() => resendMutation.mutate()}
            disabled={resendMutation.isPending}
            className="text-legal-gold hover:underline disabled:text-muted-foreground"
          >
            {resendMutation.isPending ? "Sending..." : "Resend reset code"}
          </button>
        </div>
      </form>
    </AuthLayout>
  );
}
