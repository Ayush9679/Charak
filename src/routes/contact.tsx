import { createFileRoute } from "@tanstack/react-router";
import { Mail, MapPin, MessageSquare, Phone } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { z } from "zod";

import { DisclaimerBar } from "@/components/disclaimer-bar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export const Route = createFileRoute("/contact")({
  head: () => ({
    meta: [
      { title: "Contact Team CHANAKYA — charak" },
      {
        name: "description",
        content:
          "Reach Team CHANAKYA about charak, hospital integrations, data partnerships or product feedback.",
      },
      { property: "og:title", content: "Contact Team CHANAKYA — charak" },
      {
        property: "og:description",
        content: "Talk to us about hospital integrations, partnerships or feedback on charak.",
      },
    ],
  }),
  component: ContactPage,
});

const schema = z.object({
  name: z.string().trim().min(1, "Please enter your name").max(100),
  email: z.string().trim().email("Enter a valid email address").max(255),
  organisation: z.string().trim().max(120).optional(),
  message: z.string().trim().min(1, "Please add a message").max(1000),
});

function ContactPage() {
  const [values, setValues] = useState({
    name: "",
    email: "",
    organisation: "",
    message: "",
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = schema.safeParse(values);
    if (!parsed.success) {
      toast.error(parsed.error.issues[0]?.message ?? "Please check the form");
      return;
    }
    toast.success("Thanks — we'll get back to you shortly.");
    setValues({ name: "", email: "", organisation: "", message: "" });
  };

  return (
    <div className="hero-bg">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-16 lg:grid-cols-[1fr_1.1fr] lg:px-8">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-teal">Contact</p>
          <h1 className="mt-3 text-4xl font-extrabold">Let's talk healthcare navigation</h1>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">
            Hospitals interested in an integration, health authorities, and patients with feedback are
            all welcome.
          </p>

          <ul className="mt-8 space-y-4">
            <ContactItem icon={<Mail className="h-4 w-4" />} label="Email" value="team@charak.health" />
            <ContactItem icon={<Phone className="h-4 w-4" />} label="Phone" value="+91 90000 00000" />
            <ContactItem
              icon={<MapPin className="h-4 w-4" />}
              label="Base"
              value="New Delhi, India"
            />
            <ContactItem
              icon={<MessageSquare className="h-4 w-4" />}
              label="Integrations"
              value="integrations@charak.health"
            />
          </ul>

          <DisclaimerBar className="mt-8" />
        </div>

        <form onSubmit={submit} className="surface p-6 sm:p-7">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              id="name"
              label="Name"
              value={values.name}
              onChange={(v) => setValues((s) => ({ ...s, name: v }))}
              placeholder="Your full name"
            />
            <Field
              id="email"
              label="Email"
              type="email"
              value={values.email}
              onChange={(v) => setValues((s) => ({ ...s, email: v }))}
              placeholder="you@example.com"
            />
          </div>
          <div className="mt-4">
            <Field
              id="organisation"
              label="Hospital / organisation (optional)"
              value={values.organisation}
              onChange={(v) => setValues((s) => ({ ...s, organisation: v }))}
              placeholder="Organisation name"
            />
          </div>
          <div className="mt-4">
            <Label htmlFor="message" className="text-sm font-semibold">
              Message
            </Label>
            <Textarea
              id="message"
              value={values.message}
              maxLength={1000}
              onChange={(e) => setValues((s) => ({ ...s, message: e.target.value }))}
              placeholder="How can we help?"
              className="mt-2.5 min-h-36 rounded-2xl bg-background"
            />
          </div>
          <Button type="submit" size="lg" className="mt-6 w-full rounded-full">
            Send message
          </Button>
          <p className="mt-3 text-xs text-muted-foreground">
            Please do not share medical records or personal health information through this form.
          </p>
        </form>
      </div>
    </div>
  );
}

function Field({
  id,
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div>
      <Label htmlFor={id} className="text-sm font-semibold">
        {label}
      </Label>
      <Input
        id={id}
        type={type}
        value={value}
        maxLength={255}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="mt-2.5 h-11 rounded-xl bg-background"
      />
    </div>
  );
}

function ContactItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <li className="flex items-center gap-3.5 rounded-2xl border border-border bg-card px-4 py-3.5">
      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-muted text-teal">
        {icon}
      </span>
      <span className="min-w-0">
        <span className="block text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {label}
        </span>
        <span className="block truncate text-sm font-semibold">{value}</span>
      </span>
    </li>
  );
}