import { useState, useEffect } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import AuthShell from "@/layouts/AuthShell";
import { authApi, extractAuthError } from "./api";
import { ROLES, ROUTES } from "@/constants";
import { cnInput } from "@/lib/formStyles";

// Simplified to exactly 6 fields for every role — no bar license, CNIC,
// university fields, etc., since no verification system exists for those
// yet. NOTE: the backend's signup schema (backend/app/schemas/auth.py)
// still requires role-specific fields for lawyer/student — see the
// flagged note handed back with this pass. This form intentionally no
// longer sends them.
const signupSchema = z
  .object({
    full_name: z.string().min(2, "Please enter your full name.").max(150),
    email: z.string().email("Please enter a valid email address."),
    phone: z.string().min(1, "Phone number is required.").max(20),
    password: z.string().min(8, "Password must be at least 8 characters.").max(128),
    confirm_password: z.string(),
    role: z.enum([ROLES.LAWYER, ROLES.CLIENT, ROLES.STUDENT]),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords don't match.",
    path: ["confirm_password"],
  });

export default function SignupPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [showPassword, setShowPassword] = useState(false);

  // The role is chosen on Welcome and passed as ?role=. Without a valid one
  // the page redirects to Welcome (below) rather than defaulting to client.
  const chosenRole = [ROLES.LAWYER, ROLES.CLIENT, ROLES.STUDENT].find((r) => r === searchParams.get("role"));
  const initialRole = chosenRole || ROLES.CLIENT;

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(signupSchema),
    defaultValues: { role: initialRole, email: "", password: "", confirm_password: "", full_name: "", phone: "" },
  });

  const role = watch("role");

  useEffect(() => {
    const roleParam = searchParams.get("role");
    if (roleParam && [ROLES.LAWYER, ROLES.CLIENT, ROLES.STUDENT].includes(roleParam)) {
      setValue("role", roleParam);
    }
  }, [searchParams, setValue]);

  const signupMutation = useMutation({
    mutationFn: authApi.signup,
    onSuccess: (data) => {
      toast.success("Almost done — check your email.", {
        description: `We've sent a 6-digit code to ${data.email}. It expires in 10 minutes.`,
      });
      navigate(`${ROUTES.OTP}?email=${encodeURIComponent(data.email)}`, {
        replace: true,
      });
    },
    onError: (err) => {
      const { message, hint } = extractAuthError(err);
      toast.error(message, { description: hint });
    },
  });

  const onSubmit = (values) => {
    // confirm_password is checked by the form only; the API doesn't take it.
    // eslint-disable-next-line no-unused-vars
    const { confirm_password, ...payload } = values;
    signupMutation.mutate(payload);
  };

  if (!chosenRole) return <Navigate to={ROUTES.WELCOME} replace />;

  return (
    <AuthShell heroAlign="center" heroTitle="Create your account." heroSubtitle={`Setting up as a ${role}.`}>
      <h2 className="font-editorial text-2xl text-ink-text mb-1">Create an account</h2>
      <p className="text-sm text-ink-muted mb-6">Tell us a bit about yourself.</p>

      <div className="border-b border-hairline-subtle mb-8" />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <div>
          <span className="block text-sm text-ink-muted mb-2">I am a</span>
          <div className="flex border border-hairline rounded-md overflow-hidden">
            {[ROLES.LAWYER, ROLES.CLIENT, ROLES.STUDENT].map((r, i) => (
              <button
                type="button"
                key={r}
                onClick={() => setValue("role", r)}
                className={`flex-1 text-sm py-2 transition-colors ${
                  i > 0 ? "border-l border-hairline" : ""
                } ${
                  role === r
                    ? "bg-ink-panel text-paper"
                    : "text-ink-muted hover:text-ink-text hover:bg-hairline-subtle/50"
                }`}
              >
                {r === ROLES.LAWYER ? "Lawyer" : r === ROLES.CLIENT ? "Client" : "Student"}
              </button>
            ))}
          </div>
        </div>

        <Field label="Full name" error={errors.full_name?.message}>
          <input
            placeholder="John Doe"
            autoComplete="name"
            className={cnInput(errors.full_name)}
            {...register("full_name")}
          />
        </Field>

        <Field label="Email" error={errors.email?.message}>
          <input
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            className={cnInput(errors.email)}
            {...register("email")}
          />
        </Field>

        <Field label="Phone number" error={errors.phone?.message}>
          <input
            placeholder="+92 300 1234567"
            autoComplete="tel"
            className={cnInput(errors.phone)}
            {...register("phone")}
          />
        </Field>

        <Field label="Password" error={errors.password?.message}>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="At least 8 characters"
              autoComplete="new-password"
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
        </Field>

        <Field label="Confirm password" error={errors.confirm_password?.message}>
          <input
            type={showPassword ? "text" : "password"}
            placeholder="Re-enter your password"
            autoComplete="new-password"
            className={cnInput(errors.confirm_password)}
            {...register("confirm_password")}
          />
        </Field>

        <button type="submit" disabled={signupMutation.isPending} className="ds-btn-primary w-full min-h-[48px] mt-2">
          {signupMutation.isPending ? <Loader2 className="h-5 w-5 animate-spin" aria-label="Creating your account" /> : "Create an account"}
        </button>
      </form>

      <p className="mt-8 text-center text-[16px] text-ds-text-2">
        Already have an account?{" "}
        <Link to={ROUTES.LOGIN} className="ds-link-seal">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}

function Field({ label, error, children }) {
  return (
    <div>
      <label className="block text-sm text-ink-muted mb-1.5">{label}</label>
      {children}
      {error && <p className="mt-1.5 text-xs text-brick">{error}</p>}
    </div>
  );
}
