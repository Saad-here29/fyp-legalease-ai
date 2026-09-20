import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { Menu, X } from "lucide-react";
import Logo from "@/components/common/Logo";
import AppButton from "@/components/ui/AppButton";
import { ROUTES } from "@/constants";

const NAV_LINKS = [
  { label: "How it works", href: "#how-it-works" },
  { label: "Features", href: "#features" },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 bg-paper transition-shadow ${
        scrolled ? "border-b border-hairline" : "border-b border-transparent"
      }`}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-8">
        <Link to={ROUTES.LANDING} className="shrink-0">
          <Logo />
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm text-ink-muted hover:text-ink-text transition-colors"
            >
              {link.label}
            </a>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-6">
          <NavLink to={ROUTES.LOGIN} className="text-sm text-brick hover:underline underline-offset-2">
            Sign in
          </NavLink>
          <AppButton to={ROUTES.WELCOME}>Get started</AppButton>
        </div>

        <button
          className="md:hidden p-2 text-ink-text"
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </nav>

      {open && (
        <div className="md:hidden border-t border-hairline bg-paper">
          <div className="flex flex-col gap-4 p-6">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="text-sm text-ink-muted hover:text-ink-text"
              >
                {link.label}
              </a>
            ))}
            <div className="flex flex-col gap-3 pt-4 border-t border-hairline-subtle">
              <NavLink
                to={ROUTES.LOGIN}
                onClick={() => setOpen(false)}
                className="text-sm text-brick"
              >
                Sign in
              </NavLink>
              <AppButton to={ROUTES.WELCOME} onClick={() => setOpen(false)} className="justify-center">
                Get started
              </AppButton>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
