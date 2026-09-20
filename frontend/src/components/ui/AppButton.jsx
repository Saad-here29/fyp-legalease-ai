import { forwardRef } from "react";
import { Link } from "react-router-dom";

// Shared button for the paper/ink editorial system.
//   - primary: solid ink-panel fill, paper text — the one "real" action.
//   - secondary: hairline border, transparent fill — everything else.
//   - inverted / inverted-secondary: same two roles, recolored for use
//     directly on top of an ink-panel background (e.g. a solid dark card)
//     where `primary`'s ink-panel fill would blend invisibly into it.
// Never accent-colored (brick is for text links only, see STYLE_GUIDE.md).
// Fixed padding/radius per spec: 12px vertical / 28px horizontal, 6px radius.
const BASE =
  "inline-flex items-center justify-center gap-2 py-3 px-7 rounded-md text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed";
const VARIANTS = {
  primary: "bg-ink-panel text-paper hover:bg-ink-panel/85",
  secondary: "border border-hairline bg-transparent text-ink-text hover:bg-hairline-subtle/50",
  inverted: "bg-paper text-ink-panel hover:bg-paper/90",
  "inverted-secondary": "border border-paper/40 bg-transparent text-paper hover:bg-paper/10",
};

const AppButton = forwardRef(
  ({ variant = "primary", as, to, className = "", children, ...props }, ref) => {
    const cls = `${BASE} ${VARIANTS[variant] || VARIANTS.primary} ${className}`;

    if (to) {
      return (
        <Link to={to} className={cls} {...props}>
          {children}
        </Link>
      );
    }

    const Comp = as || "button";
    return (
      <Comp ref={ref} className={cls} {...props}>
        {children}
      </Comp>
    );
  }
);
AppButton.displayName = "AppButton";

export default AppButton;
