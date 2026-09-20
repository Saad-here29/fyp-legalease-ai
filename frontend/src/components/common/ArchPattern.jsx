/**
 * Faint repeating architectural-arch silhouette — evokes Pakistani
 * courthouse facades (a row of pointed/Mughal arches). Used only behind
 * the Login/AuthShell ink panel and the Landing page hero, per the design
 * system. Fully decorative: `pointer-events-none`, sits behind content via
 * `absolute inset-0`, and takes its color from the parent's text color so
 * it can render light-on-dark (ink panel) or dark-on-light (hero) —
 * opacity is controlled by the caller (6–15%) so it never affects legibility.
 */
export default function ArchPattern({ className = "" }) {
  return (
    <svg
      className={`absolute inset-0 w-full h-full pointer-events-none ${className}`}
      preserveAspectRatio="xMidYMax slice"
      aria-hidden="true"
    >
      <defs>
        <pattern id="archMotif" width="90" height="140" patternUnits="userSpaceOnUse">
          <path
            d="M12 140 L12 60 Q12 18 45 12 Q78 18 78 60 L78 140 Z"
            fill="currentColor"
          />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#archMotif)" />
    </svg>
  );
}
