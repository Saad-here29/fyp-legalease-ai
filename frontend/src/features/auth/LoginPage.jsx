import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import AuthShell from "@/layouts/AuthShell";
import AppButton from "@/components/ui/AppButton";
import { authApi, dashboardRouteFor, extractAuthError } from "./api";
import { useAuthStore } from "@/store/authStore";
import { ROUTES } from "@/constants";
import { cnInput } from "@/lib/formStyles";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address."),
  password: z.string().min(1, "Password is required."),
});

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((s) => s.setSession);
  const [showPassword, setShowPassword] = useState(false);

  const prefillEmail = location.state?.prefillEmail || "";
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: prefillEmail, password: "" },
  });
  const emailValue = watch("email");

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setSession({ user: data.user });
      toast.success(`Welcome back, ${data.user.full_name.split(" ")[0]}!`);
      const from = location.state?.from?.pathname;
      navigate(from || dashboardRouteFor(data.user.role), { replace: true });
    },
    onError: (err) => {
      const status = err?.response?.status;
      const { message, hint } = extractAuthError(err);
      // 423 + "Please verify your email" means the account exists but
      // hasn't completed OTP. Bounce them to the OTP page automatically.
      if (status === 423 && /verify/i.test(message)) {
        toast.message(message, {
          description: "Sending you to the verification page...",
        });
        const email = encodeURIComponent(emailValue || "");
        navigate(`${ROUTES.OTP}?email=${email}`);
        return;
      }
      toast.error(message, { description: hint });
    },
  });

  const onSubmit = (values) => loginMutation.mutate(values);

  return (
    <AuthShell
      heroTitle="Welcome back."
      heroSubtitle="Sign in to continue to your cases, research, and the AI legal assistant."
    >
      <h2 className="font-editorial text-2xl text-ink-text mb-1">Sign in</h2>
      <p className="text-sm text-ink-muted mb-6">
        Enter your details to access your account.
      </p>

      <div className="border-b border-hairline-subtle mb-8" />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
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

        <div>
          <div className="flex items-baseline justify-between mb-1.5">
            <label htmlFor="password" className="block text-sm text-ink-muted">
              Password
            </label>
            <Link
              to={ROUTES.FORGOT_PASSWORD}
              className="text-xs text-brick hover:underline underline-offset-2"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              autoComplete="current-password"
              className={cnInput(errors.password, "pr-8")}
              {...register("password")}
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
          {errors.password && (
            <p className="mt-1.5 text-xs text-brick">{errors.password.message}</p>
          )}
        </div>

        <AppButton
          type="submit"
          disabled={loginMutation.isPending}
          className="w-full mt-2"
        >
          {loginMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Sign in"}
        </AppButton>
      </form>

      <div className="mt-8 pt-6 border-t border-hairline-subtle text-center">
        <p className="text-sm text-ink-muted">
          Don't have an account?{" "}
          <Link
            to={ROUTES.WELCOME}
            className="text-brick hover:underline underline-offset-2"
          >
            Get started
          </Link>
        </p>
      </div>
    </AuthShell>
  );
}
