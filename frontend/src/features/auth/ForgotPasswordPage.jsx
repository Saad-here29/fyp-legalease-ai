import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import AuthShell from "@/layouts/AuthShell";
import { authApi, extractAuthError } from "./api";
import { ROUTES } from "@/constants";

const schema = z.object({
  email: z.string().email("Please enter a valid email address."),
});

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { email: "" },
  });

  const mutation = useMutation({
    mutationFn: (values) => authApi.forgotPassword(values.email),
    onSuccess: (_, values) => {
      toast.success("Reset code sent.", {
        description: "If your email is registered, a code is on its way.",
      });
      navigate(`${ROUTES.RESET_PASSWORD}?email=${encodeURIComponent(values.email)}`);
    },
    onError: (err) => {
      const { message, hint } = extractAuthError(err);
      toast.error(message, { description: hint });
    },
  });

  return (
    <AuthShell
      heroTitle="Reset your password."
      heroSubtitle="Enter your email and we'll send you a verification code."
    >
      <p className="ds-eyebrow">Forgot password</p>
      <h1 className="font-ds-serif font-medium text-[40px] leading-[48px] sm:text-[48px] sm:leading-[56px] tracking-tight text-ds-text mt-3">
        Reset your password
      </h1>
      <p className="ds-body text-ds-text-2 mt-2">We&apos;ll email you a 6-digit code to reset it.</p>

      <form onSubmit={handleSubmit(mutation.mutate)} className="mt-8 space-y-6" noValidate>
        <div>
          <label htmlFor="fp-email" className="ds-label mb-2.5">Email</label>
          <input
            id="fp-email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            aria-invalid={!!errors.email}
            className={`ds-input ${errors.email ? "border-ds-seal" : ""}`}
            {...register("email")}
          />
          {errors.email && (
            <p className="mt-2 text-[14px] leading-[20px] text-ds-seal" role="alert">{errors.email.message}</p>
          )}
        </div>

        <button type="submit" disabled={mutation.isPending} className="ds-btn-primary w-full min-h-[48px]">
          {mutation.isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Sending" /> : "Send reset code"}
        </button>
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
