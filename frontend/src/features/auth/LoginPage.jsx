import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import AuthShell from "@/layouts/AuthShell";
import { authApi, dashboardRouteFor, extractAuthError } from "./api";
import { useAuthStore } from "@/store/authStore";
import { ROUTES } from "@/constants";

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

  const fieldError = (e) =>
    e && <p className="mt-2 text-[14px] leading-[20px] text-ds-seal" role="alert">{e.message}</p>;

  return (
    <AuthShell
      heroTitle={<>Your chambers,<br />in order.</>}
      heroSubtitle="Cases, research, documents and contract drafts for Pakistani practice — with every AI answer tied to the statute it came from."
      heroPoints={[
        "Citations checked against the statute text",
        "Federal statutes of the Pakistan Code, in one search",
      ]}
    >
      <p className="ds-eyebrow">Welcome back</p>
      <h1 className="font-ds-serif font-medium text-[40px] leading-[48px] sm:text-[48px] sm:leading-[56px] tracking-tight text-ds-text mt-3">
        Sign in to LegalEase
      </h1>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-10 space-y-7" noValidate>
        <div>
          <label htmlFor="email" className="ds-label mb-2.5">Email</label>
          <input
            id="email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            aria-invalid={!!errors.email}
            className={`ds-input ${errors.email ? "border-ds-seal" : ""}`}
            {...register("email")}
          />
          {fieldError(errors.email)}
        </div>

        <div>
          <div className="flex items-baseline justify-between mb-2.5">
            <label htmlFor="password" className="ds-label mb-0">Password</label>
            <Link to={ROUTES.FORGOT_PASSWORD} className="ds-link-seal text-[15px]">
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              aria-invalid={!!errors.password}
              className={`ds-input pr-12 ${errors.password ? "border-ds-seal" : ""}`}
              {...register("password")}
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
          {fieldError(errors.password)}
        </div>

        <button type="submit" disabled={loginMutation.isPending} className="ds-btn-primary w-full min-h-[48px]">
          {loginMutation.isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Signing in" /> : "Sign in"}
        </button>
      </form>

      <p className="mt-8 text-center text-[16px] text-ds-text-2">
        New to LegalEase?{" "}
        <Link to={ROUTES.WELCOME} className="ds-link-seal">
          Create an account
        </Link>
      </p>
    </AuthShell>
  );
}
