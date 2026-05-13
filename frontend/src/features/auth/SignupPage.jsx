import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Eye, EyeOff, UserPlus } from "lucide-react";
import AuthLayout from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Spinner from "@/components/common/Spinner";
import { authApi, extractAuthError } from "./api";
import { ROLES, ROUTES } from "@/constants";

const baseSchema = {
  email: z.string().email("Please enter a valid email address."),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters.")
    .max(128, "Password is too long."),
  full_name: z.string().min(2, "Please enter your full name.").max(150),
  phone: z.string().max(20).optional().or(z.literal("")),
  role: z.enum(["LAWYER", "CLIENT", "STUDENT"]),
};

const signupSchema = z.discriminatedUnion("role", [
  z.object({
    ...baseSchema,
    role: z.literal("LAWYER"),
    bar_license_no: z.string().min(1, "Bar license number is required."),
    specialization: z.string().min(1, "Specialization is required."),
    bar_year: z.coerce.number().int().min(1950).max(2100),
    bar_council: z.string().optional().or(z.literal("")),
  }),
  z.object({
    ...baseSchema,
    role: z.literal("CLIENT"),
    address: z.string().optional().or(z.literal("")),
    cnic: z.string().optional().or(z.literal("")),
  }),
  z.object({
    ...baseSchema,
    role: z.literal("STUDENT"),
    university_id: z.string().min(1, "University ID is required."),
    university_name: z.string().min(1, "University name is required."),
    current_year: z.coerce.number().int().min(1).max(7),
  }),
]);

export default function SignupPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [showPassword, setShowPassword] = useState(false);

  const initialRole =
    [ROLES.LAWYER, ROLES.CLIENT, ROLES.STUDENT].find(
      (r) => r === searchParams.get("role")
    ) || ROLES.CLIENT;

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(signupSchema),
    defaultValues: { role: initialRole, email: "", password: "", full_name: "" },
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
    // Strip empty optional fields
    const payload = Object.fromEntries(
      Object.entries(values).filter(([, v]) => v !== "" && v !== undefined)
    );
    signupMutation.mutate(payload);
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle={`Setting up as a ${role.toLowerCase()}.`}
      footer={
        <>
          Already have an account?{" "}
          <Link to={ROUTES.LOGIN} className="text-legal-gold hover:underline font-medium">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Role selector */}
        <div className="space-y-2">
          <Label>I am a</Label>
          <div className="grid grid-cols-3 gap-2">
            {[ROLES.LAWYER, ROLES.CLIENT, ROLES.STUDENT].map((r) => (
              <button
                type="button"
                key={r}
                onClick={() => setValue("role", r)}
                className={`text-xs font-medium py-2 rounded-lg border transition-all ${
                  role === r
                    ? "bg-legal-gold/15 border-legal-gold/60 text-legal-gold"
                    : "bg-secondary/30 border-border/50 text-muted-foreground hover:border-border"
                }`}
              >
                {r === "LAWYER" ? "Lawyer" : r === "CLIENT" ? "Client" : "Student"}
              </button>
            ))}
          </div>
        </div>

        {/* Common fields */}
        <Field label="Full name" error={errors.full_name?.message}>
          <Input
            placeholder="John Doe"
            autoComplete="name"
            {...register("full_name")}
          />
        </Field>

        <Field label="Email" error={errors.email?.message}>
          <Input
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            {...register("email")}
          />
        </Field>

        <Field label="Password" error={errors.password?.message}>
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              placeholder="At least 8 characters"
              autoComplete="new-password"
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
        </Field>

        <Field label="Phone (optional)" error={errors.phone?.message}>
          <Input
            placeholder="+92 300 1234567"
            autoComplete="tel"
            {...register("phone")}
          />
        </Field>

        {/* Role-specific fields */}
        {role === ROLES.LAWYER && (
          <>
            <Field label="Bar license no." error={errors.bar_license_no?.message}>
              <Input placeholder="PB-12345" {...register("bar_license_no")} />
            </Field>
            <Field label="Specialization" error={errors.specialization?.message}>
              <Input placeholder="Family Law" {...register("specialization")} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Bar year" error={errors.bar_year?.message}>
                <Input type="number" placeholder="2018" {...register("bar_year")} />
              </Field>
              <Field label="Bar council" error={errors.bar_council?.message}>
                <Input placeholder="Punjab" {...register("bar_council")} />
              </Field>
            </div>
          </>
        )}

        {role === ROLES.CLIENT && (
          <>
            <Field label="Address (optional)" error={errors.address?.message}>
              <Input placeholder="House #1, Street 2, Lahore" {...register("address")} />
            </Field>
            <Field label="CNIC (optional)" error={errors.cnic?.message}>
              <Input placeholder="35202-1234567-1" {...register("cnic")} />
            </Field>
          </>
        )}

        {role === ROLES.STUDENT && (
          <>
            <Field label="University name" error={errors.university_name?.message}>
              <Input placeholder="Punjab University" {...register("university_name")} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="University ID" error={errors.university_id?.message}>
                <Input placeholder="LLB-2022-001" {...register("university_id")} />
              </Field>
              <Field label="Current year" error={errors.current_year?.message}>
                <Input type="number" min="1" max="7" placeholder="3" {...register("current_year")} />
              </Field>
            </div>
          </>
        )}

        <Button
          type="submit"
          variant="gold"
          size="lg"
          className="w-full"
          disabled={signupMutation.isPending}
        >
          {signupMutation.isPending ? (
            <Spinner size={18} />
          ) : (
            <>
              <UserPlus className="h-4 w-4" />
              Create account
            </>
          )}
        </Button>
      </form>
    </AuthLayout>
  );
}

function Field({ label, error, children }) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
