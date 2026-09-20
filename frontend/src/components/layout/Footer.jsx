import { Link } from "react-router-dom";
import { Github, Linkedin, Mail } from "lucide-react";
import Logo from "@/components/common/Logo";
import Container from "@/components/layout/Container";
import { ROUTES, APP_VERSION } from "@/constants";

const FOOTER_GROUPS = [
  {
    title: "Platform",
    links: [
      { label: "AI chatbot", href: "#features" },
      { label: "Case management", href: "#features" },
      { label: "Document analysis", href: "#features" },
      { label: "Legal research", href: "#features" },
    ],
  },
  {
    title: "Roles",
    links: [
      { label: "For lawyers", href: ROUTES.WELCOME },
      { label: "For clients", href: ROUTES.WELCOME },
      { label: "For students", href: ROUTES.WELCOME },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Documentation", href: "#" },
      { label: "API reference", href: "#" },
      { label: "Privacy policy", href: "#" },
      { label: "Terms of service", href: "#" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-hairline bg-paper">
      <Container className="py-16">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-5">
          <div className="lg:col-span-2 space-y-4">
            <Logo size="md" />
            <p className="text-sm text-ink-muted max-w-sm leading-relaxed">
              AI-powered legal assistance, case management, and research for
              the Pakistani legal sector — built with care at NUCES Islamabad.
            </p>
            <div className="flex items-center gap-4 pt-2">
              <a
                href="mailto:saadullahlakho@gmail.com"
                aria-label="Email"
                className="text-ink-muted hover:text-ink-text transition-colors"
              >
                <Mail className="h-4 w-4" />
              </a>
              <a
                href="https://github.com"
                aria-label="GitHub"
                className="text-ink-muted hover:text-ink-text transition-colors"
              >
                <Github className="h-4 w-4" />
              </a>
              <a
                href="https://linkedin.com"
                aria-label="LinkedIn"
                className="text-ink-muted hover:text-ink-text transition-colors"
              >
                <Linkedin className="h-4 w-4" />
              </a>
            </div>
          </div>

          {FOOTER_GROUPS.map((group) => (
            <div key={group.title}>
              <h4 className="text-sm font-medium text-ink-text mb-4">{group.title}</h4>
              <ul className="space-y-3">
                {group.links.map((link) => (
                  <li key={link.label}>
                    {link.href.startsWith("#") ? (
                      <a href={link.href} className="text-sm text-ink-muted hover:text-ink-text transition-colors">
                        {link.label}
                      </a>
                    ) : (
                      <Link to={link.href} className="text-sm text-ink-muted hover:text-ink-text transition-colors">
                        {link.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 pt-8 border-t border-hairline-subtle flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-ink-muted">
          <p>© {new Date().getFullYear()} LegalEase AI · FYP-1 · NUCES Islamabad · Session 2022-2026</p>
          <p>v{APP_VERSION} · Built with React, FastAPI, FAISS &amp; OpenAI</p>
        </div>
      </Container>
    </footer>
  );
}
