import { Link, createFileRoute } from "@tanstack/react-router";

import { AuthShell } from "./login";

export const Route = createFileRoute("/signup")({
  head: () => ({
    meta: [
      { title: "Create your Charak account" },
      {
        name: "description",
        content:
          "Create a Charak account to save symptom analyses, hospital shortlists and comparisons across devices.",
      },
      { property: "og:title", content: "Create your Charak account" },
      {
        property: "og:description",
        content: "Save your analyses and hospital shortlists with a free Charak account.",
      },
    ],
  }),
  component: SignupPage,
});

function SignupPage() {
  return (
    <AuthShell
      withName
      title="Create your account"
      subtitle="Save analyses, shortlists and comparisons across devices."
      cta="Create account"
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-teal">
            Log in
          </Link>
        </>
      }
    />
  );
}
