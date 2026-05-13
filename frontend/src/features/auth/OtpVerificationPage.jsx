import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { ShieldCheck, RotateCcw } from "lucide-react";
import AuthLayout from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";
import Spinner from "@/components/common/Spinner";
import { authApi, extractAuthError } from "./api";
import { ROUTES } from "@/constants";

const OTP_LENGTH = 6;
const OTP_TTL_SECONDS = 10 * 60;
const RESEND_COOLDOWN_SECONDS = 60;

const formatMMSS = (s) => {
  const m = Math.floor(s / 60).toString().padStart(2, "0");
  const r = (s % 60).toString().padStart(2, "0");
  return `${m}:${r}`;
};

export default function OtpVerificationPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const email = searchParams.get("email") || "";

  const [digits, setDigits] = useState(Array(OTP_LENGTH).fill(""));
  const inputsRef = useRef([]);

  // Countdowns — both tick once per second
  const [secondsLeft, setSecondsLeft] = useState(OTP_TTL_SECONDS);
  const [resendCooldown, setResendCooldown] = useState(RESEND_COOLDOWN_SECONDS);

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const id = setInterval(() => setSecondsLeft((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(id);
  }, [secondsLeft]);

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const id = setInterval(() => setResendCooldown((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(id);
  }, [resendCooldown]);

  const otp = digits.join("");
  const expired = secondsLeft === 0;

  const handleChange = (i, val) => {
    const v = val.replace(/\D/g, "").slice(-1);
    setDigits((d) => {
      const next = [...d];
      next[i] = v;
      return next;
    });
    if (v && i < OTP_LENGTH - 1) inputsRef.current[i + 1]?.focus();
  };

  const handleKeyDown = (i, e) => {
    if (e.key === "Backspace" && !digits[i] && i > 0) {
      inputsRef.current[i - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    const text = (e.clipboardData?.getData("text") || "").replace(/\D/g, "").slice(0, OTP_LENGTH);
    if (text.length === 0) return;
    e.preventDefault();
    const next = Array(OTP_LENGTH).fill("");
    for (let i = 0; i < text.length; i++) next[i] = text[i];
    setDigits(next);
    inputsRef.current[Math.min(text.length, OTP_LENGTH - 1)]?.focus();
  };

  const verifyMutation = useMutation({
    mutationFn: () => authApi.verifyOtp({ email, otp }),
    onSuccess: (data) => {
      toast.success("Email verified.", {
        description: "Sign in to continue to your dashboard.",
      });
      navigate(ROUTES.LOGIN, {
        replace: true,
        state: { prefillEmail: data.email || email },
      });
    },
    onError: (err) => {
      const { message, hint } = extractAuthError(err);
      toast.error(message, { description: hint });
    },
  });

  const resendMutation = useMutation({
    mutationFn: () => authApi.resendOtp(email),
    onSuccess: () => {
      setSecondsLeft(OTP_TTL_SECONDS);
      setResendCooldown(RESEND_COOLDOWN_SECONDS);
      setDigits(Array(OTP_LENGTH).fill(""));
      inputsRef.current[0]?.focus();
      toast.success("New code sent.", { description: `Check ${email} again.` });
    },
    onError: (err) => {
      const { message, hint } = extractAuthError(err);
      toast.error(message, { description: hint });
    },
  });

  return (
    <AuthLayout
      title="Verify your email"
      subtitle={
        email
          ? `We sent a 6-digit code to ${email}.`
          : "Enter the 6-digit code we sent."
      }
      footer={
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">
            Didn't receive a code? Double-check the email is spelled correctly,
            check your spam folder, or use Resend.
          </p>
          <p className="text-sm">
            Wrong email?{" "}
            <Link
              to={ROUTES.SIGNUP}
              className="text-legal-gold hover:underline font-medium"
            >
              Start over
            </Link>
            {" · "}
            <Link
              to={ROUTES.LOGIN}
              className="text-legal-gold hover:underline font-medium"
            >
              Back to sign in
            </Link>
          </p>
        </div>
      }
    >
      <div className="space-y-6">
        <div className="flex justify-between gap-2" onPaste={handlePaste}>
          {digits.map((d, i) => (
            <input
              key={i}
              ref={(el) => (inputsRef.current[i] = el)}
              value={d}
              onChange={(e) => handleChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              maxLength={1}
              inputMode="numeric"
              autoComplete="one-time-code"
              disabled={expired}
              className="h-14 w-12 text-center text-xl font-bold rounded-lg border border-input bg-background/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-legal-gold/50 focus-visible:border-legal-gold transition-colors disabled:opacity-50"
            />
          ))}
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className={expired ? "text-destructive font-medium" : "text-muted-foreground"}>
            {expired ? "Code expired" : `Expires in ${formatMMSS(secondsLeft)}`}
          </span>
          <button
            type="button"
            onClick={() => resendMutation.mutate()}
            disabled={resendMutation.isPending || resendCooldown > 0}
            className="inline-flex items-center gap-1 text-legal-gold hover:underline disabled:text-muted-foreground disabled:no-underline disabled:cursor-not-allowed"
          >
            <RotateCcw className="h-3 w-3" />
            {resendMutation.isPending
              ? "Sending..."
              : resendCooldown > 0
              ? `Resend in ${resendCooldown}s`
              : "Resend code"}
          </button>
        </div>

        <Button
          type="button"
          variant="gold"
          size="lg"
          className="w-full"
          disabled={otp.length !== OTP_LENGTH || verifyMutation.isPending || expired}
          onClick={() => verifyMutation.mutate()}
        >
          {verifyMutation.isPending ? (
            <Spinner size={18} />
          ) : (
            <>
              <ShieldCheck className="h-4 w-4" />
              Verify email
            </>
          )}
        </Button>
      </div>
    </AuthLayout>
  );
}
