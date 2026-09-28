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

  const roleLabel = { [ROLES.LAWYER]: "Lawyer", [ROLES.CLIENT]: "Client", [ROLES.STUDENT]: "Law student" };

  return (
    <AuthShell heroAlign="center" heroTitle="Create your account." heroSubtitle={`Setting up as a ${roleLabel[role].toLowerCase()}.`}>
      <p className="ds-eyebrow">Step 2 of 2</p>
      <h1 className="font-ds-serif font-medium text-[40px] leading-[48px] sm:text-[48px] sm:leading-[56px] tracking-tight text-ds-text mt-3">
        Create an account
      </h1>
      <p className="ds-body text-ds-text-2 mt-2">Tell us a bit about yourself.</p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-6" noValidate>
        <div>
          <p className="ds-label mb-2.5" id="role-label">I am a</p>
          <div role="radiogroup" aria-labelledby="role-label" className="grid grid-cols-3 gap-2">
            {[ROLES.LAWYER, ROLES.CLIENT, ROLES.STUDENT].map((r) => (
              <button
                type="button"
                role="radio"
                aria-checked={role === r}
                key={r}
                onClick={() => setValue("role", r)}
                className={`min-h-[48px] px-2 rounded-ds border-2 font-ds-sans font-semibold text-[15px] transition-colors
                  focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ds-ink ${
                  role === r ? "border-ds-seal bg-ds-seal-tint text-ds-seal" : "border-ds-rule bg-ds-sheet text-ds-text hover:border-ds-text-2"
                }`}
              >
                {roleLabel[r]}
              </button>
            ))}
          </div>
        </div>

        <Field id="su-name" label="Full name" error={errors.full_name?.message}>
          <input id="su-name" placeholder="Ayesha Khan" autoComplete="name" aria-invalid={!!errors.full_name}
            className={inputClass(errors.full_name)} {...register("full_name")} />
        </Field>

        <Field id="su-email" label="Email" error={errors.email?.message}>
          <input id="su-email" type="email" placeholder="you@example.com" autoComplete="email" aria-invalid={!!errors.email}
            className={inputClass(errors.email)} {...register("email")} />
        </Field>

        <Field id="su-phone" label="Phone number" error={errors.phone?.message}>
          <input id="su-phone" placeholder="+92 300 1234567" autoComplete="tel" aria-invalid={!!errors.phone}
            className={inputClass(errors.phone)} {...register("phone")} />
        </Field>

        <Field id="su-password" label="Password" error={errors.password?.message}>
          <div className="relative">
            <input id="su-password" type={showPassword ? "text" : "password"} placeholder="At least 8 characters"
              autoComplete="new-password" aria-invalid={!!errors.password}
              className={`${inputClass(errors.password)} pr-12`} {...register("password")} />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-1 top-1/2 -translate-y-1/2 h-11 w-11 flex items-center justify-center text-ds-text-2 hover:text-ds-text rounded-ds"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
        </Field>

        <Field id="su-confirm" label="Confirm password" error={errors.confirm_password?.message}>
          <input id="su-confirm" type={showPassword ? "text" : "password"} placeholder="Re-enter your password"
            autoComplete="new-password" aria-invalid={!!errors.confirm_password}
            className={inputClass(errors.confirm_password)} {...register("confirm_password")} />
        </Field>

        <button type="submit" disabled={signupMutation.isPending} className="ds-btn-primary w-full min-h-[48px]">
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

const inputClass = (error) => `ds-input ${error ? "border-ds-seal" : ""}`;

function Field({ id, label, error, children }) {
  return (
    <div>
      <label htmlFor={id} className="ds-label mb-2.5">{label}</label>
      {children}
      {error && <p className="mt-2 text-[14px] leading-[20px] text-ds-seal" role="alert">{error}</p>}
    </div>
  );
}
