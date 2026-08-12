import { Link, createFileRoute } from "@tanstack/react-router";
import { Lock, Mail } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Log in to charak" },
      {
        name: "description",
        content: "Log in to charak to revisit your saved analyses, hospital shortlists and comparisons.",
      },
      { property: "og:title", content: "Log in to charak" },
      {
        property: "og:description",
        content: "Access your saved hospital recommendations and comparisons.",
      },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  return (
    <AuthShell
      title="Welcome back"
      subtitle="Log in to revisit your analyses and saved hospital shortlists."
      cta="Log in"
      footer={
        <>
          New to charak?{" "}
          <Link to="/signup" className="font-semibold text-teal">
            Create an account
          </Link>
        </>
      }
    />
  );
}

export function AuthShell({
  title,
  subtitle,
  cta,
  footer,
  withName = false,
}: {
  title: string;
  subtitle: string;
  cta: string;
  footer: React.ReactNode;
  withName?: boolean;
}) {
  return (
    <div className="hero-bg">
      <div className="mx-auto max-w-md px-5 py-20 lg:px-8">
        <div className="surface p-7">
          <h1 className="text-2xl font-extrabold">{title}</h1>
          <p className="mt-2 text-sm text-muted-foreground">{subtitle}</p>

          <form
            className="mt-7 space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              toast.info("Accounts activate in the next release of charak.");
            }}
          >
            {withName && (
              <div>
                <Label htmlFor="fullname" className="text-sm font-semibold">
                  Full name
                </Label>
                <Input
                  id="fullname"
                  maxLength={100}
                  className="mt-2.5 h-11 rounded-xl bg-background"
                  placeholder="Your name"
                />
              </div>
            )}
            <div>
              <Label htmlFor="email" className="text-sm font-semibold">
                Email
              </Label>
              <div className="relative mt-2.5">
                <Mail className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  maxLength={255}
                  className="h-11 rounded-xl bg-background pl-10"
                  placeholder="you@example.com"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="password" className="text-sm font-semibold">
                Password
              </Label>
              <div className="relative mt-2.5">
                <Lock className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  maxLength={128}
                  className="h-11 rounded-xl bg-background pl-10"
                  placeholder="••••••••"
                />
              </div>
            </div>
            <Button type="submit" size="lg" className="w-full rounded-full">
              {cta}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">{footer}</p>
        </div>
      </div>
    </div>
  );
}