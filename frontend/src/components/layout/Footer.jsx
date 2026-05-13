import { Link } from "react-router-dom";
import { Github, Linkedin, Mail } from "lucide-react";
import Logo from "@/components/common/Logo";
import Container from "@/components/layout/Container";
import { Separator } from "@/components/ui/separator";
import { ROUTES, APP_VERSION } from "@/constants";

const FOOTER_GROUPS = [
  {
    title: "Platform",
    links: [
      { label: "AI Chatbot", href: "#features" },
      { label: "Case Management", href: "#features" },
      { label: "Document Analysis", href: "#features" },
      { label: "Legal Research", href: "#features" },
    ],
  },
  {
    title: "Roles",
    links: [
      { label: "For Lawyers", href: ROUTES.WELCOME },
      { label: "For Clients", href: ROUTES.WELCOME },
      { label: "For Students", href: ROUTES.WELCOME },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Documentation", href: "#" },
      { label: "API Reference", href: "#" },
      { label: "Privacy Policy", href: "#" },
      { label: "Terms of Service", href: "#" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="relative border-t border-border/50 bg-card/30 backdrop-blur-sm">
      <Container className="py-16">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-5">
          <div className="lg:col-span-2 space-y-4">
            <Logo size="md" />
            <p className="text-sm text-muted-foreground max-w-sm leading-relaxed">
              AI-powered legal assistance, case management, and research for
              the Pakistani legal sector — built with care at NUCES Islamabad.
            </p>
            <div className="flex items-center gap-3 pt-2">
              <a
                href="mailto:saadullahlakho@gmail.com"
                aria-label="Email"
                className="rounded-lg border border-border/50 p-2 hover:border-legal-gold hover:text-legal-gold transition-colors"
              >
                <Mail className="h-4 w-4" />
              </a>
              <a
                href="https://github.com"
                aria-label="GitHub"
                className="rounded-lg border border-border/50 p-2 hover:border-legal-gold hover:text-legal-gold transition-colors"
              >
                <Github className="h-4 w-4" />
              </a>
              <a
                href="https://linkedin.com"
                aria-label="LinkedIn"
                className="rounded-lg border border-border/50 p-2 hover:border-legal-gold hover:text-legal-gold transition-colors"
              >
                <Linkedin className="h-4 w-4" />
              </a>
            </div>
          </div>

          {FOOTER_GROUPS.map((group) => (
            <div key={group.title}>
              <h4 className="text-sm font-semibold text-foreground mb-4">
                {group.title}
              </h4>
              <ul className="space-y-3">
                {group.links.map((link) => (
                  <li key={link.label}>
                    {link.href.startsWith("#") ? (
                      <a
                        href={link.href}
                        className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {link.label}
                      </a>
                    ) : (
                      <Link
                        to={link.href}
                        className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {link.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <Separator className="my-10 bg-border/40" />

        <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">
          <p>
            © {new Date().getFullYear()} LegalEase AI · FYP-1 · NUCES Islamabad
            · Session 2022-2026
          </p>
          <p>
            v{APP_VERSION} · Built with React, FastAPI, FAISS &amp; OpenAI
          </p>
        </div>
      </Container>
    </footer>
  );
}
