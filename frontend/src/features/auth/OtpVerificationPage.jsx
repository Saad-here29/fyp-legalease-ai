import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, RotateCcw } from "lucide-react";
import AuthShell from "@/layouts/AuthShell";
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
    <AuthShell
      heroTitle="Verify your email."
      heroSubtitle={
        email ? `We sent a 6-digit code to ${email}.` : "Enter the 6-digit code we sent."
      }
    >
      <p className="ds-eyebrow">Verify your email</p>
      <h1 className="font-ds-serif font-medium text-[40px] leading-[48px] sm:text-[48px] sm:leading-[56px] tracking-tight text-ds-text mt-3">
        Enter your code
      </h1>
      <p className="ds-body text-ds-text-2 mt-2">Check your inbox for the 6-digit verification code.</p>

      <div className="mt-8 space-y-6">
        <fieldset>
          <legend className="ds-label mb-2.5">6-digit code</legend>
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
                aria-label={`Digit ${i + 1}`}
                disabled={expired}
                className="h-14 w-full max-w-[56px] text-center font-ds-sans font-semibold text-[22px] text-ds-text bg-ds-sheet border border-ds-rule rounded-ds
                  focus:outline-none focus:border-ds-ink focus:ring-2 focus:ring-ds-ink/10 disabled:opacity-50"
              />
            ))}
          </div>
        </fieldset>

        <div className="flex items-center justify-between gap-4">
          <span className={`text-[15px] ${expired ? "text-ds-seal font-semibold" : "text-ds-text-2"}`} role={expired ? "alert" : undefined}>
            {expired ? "Code expired — request a new one" : `Expires in ${formatMMSS(secondsLeft)}`}
          </span>
          <button
            type="button"
            onClick={() => resendMutation.mutate()}
            disabled={resendMutation.isPending || resendCooldown > 0}
            className="inline-flex items-center gap-1.5 min-h-[44px] ds-link-seal text-[15px] disabled:text-ds-text-2 disabled:no-underline disabled:font-normal disabled:cursor-not-allowed"
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            {resendMutation.isPending ? "Sending…" : resendCooldown > 0 ? `Resend in ${resendCooldown}s` : "Resend code"}
          </button>
        </div>

        <button
          type="button"
          disabled={otp.length !== OTP_LENGTH || verifyMutation.isPending || expired}
          onClick={() => verifyMutation.mutate()}
          className="ds-btn-primary w-full min-h-[48px]"
        >
          {verifyMutation.isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Verifying" /> : "Verify email"}
        </button>
      </div>

      <div className="mt-8 text-center space-y-3">
        <p className="ds-meta">
          Didn&apos;t receive a code? Check your spam folder, or use Resend above.
        </p>
        <p className="text-[16px] text-ds-text-2">
          Wrong email?{" "}
          <Link to={ROUTES.WELCOME} className="ds-link-seal">
            Start over
          </Link>
        </p>
        <p className="text-[16px] text-ds-text-2">
          Already verified?{" "}
          <Link to={ROUTES.LOGIN} className="ds-link-seal">
            Sign in
          </Link>
        </p>
      </div>
    </AuthShell>
  );
}
