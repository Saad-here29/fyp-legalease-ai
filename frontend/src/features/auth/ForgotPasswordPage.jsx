import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { MailCheck } from "lucide-react";
import AuthLayout from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Spinner from "@/components/common/Spinner";
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
    <AuthLayout
      title="Reset your password"
      subtitle="Enter your email and we'll send you a verification code."
      footer={
        <>
          Remembered it?{" "}
          <Link to={ROUTES.LOGIN} className="text-legal-gold hover:underline font-medium">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(mutation.mutate)} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            {...register("email")}
          />
          {errors.email && (
            <p className="text-xs text-destructive">{errors.email.message}</p>
          )}
        </div>

        <Button
          type="submit"
          variant="gold"
          size="lg"
          className="w-full"
          disabled={mutation.isPending}
        >
          {mutation.isPending ? (
            <Spinner size={18} />
          ) : (
            <>
              <MailCheck className="h-4 w-4" />
              Send reset code
            </>
          )}
        </Button>
      </form>
    </AuthLayout>
  );
}
