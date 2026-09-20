import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import AuthShell from "@/layouts/AuthShell";
import AppButton from "@/components/ui/AppButton";
import { authApi, extractAuthError } from "./api";
import { ROUTES } from "@/constants";
import { cnInput } from "@/lib/formStyles";

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
      <h2 className="font-editorial text-2xl text-ink-text mb-1">Forgot password</h2>
      <p className="text-sm text-ink-muted mb-6">
        We'll email you a 6-digit code to reset it.
      </p>

      <div className="border-b border-hairline-subtle mb-8" />

      <form onSubmit={handleSubmit(mutation.mutate)} className="space-y-6">
        <div>
          <label htmlFor="email" className="block text-sm text-ink-muted mb-1.5">
            Email
          </label>
          <input
            id="email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            className={cnInput(errors.email)}
            {...register("email")}
          />
          {errors.email && (
            <p className="mt-1.5 text-xs text-brick">{errors.email.message}</p>
          )}
        </div>

        <AppButton type="submit" disabled={mutation.isPending} className="w-full">
          {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Send reset code"}
        </AppButton>
      </form>

      <div className="mt-8 pt-6 border-t border-hairline-subtle text-center">
        <p className="text-sm text-ink-muted">
          Remembered it?{" "}
          <Link to={ROUTES.LOGIN} className="text-brick hover:underline underline-offset-2">
            Sign in
          </Link>
        </p>
      </div>
    </AuthShell>
  );
}
