/**
 * Faint repeating architectural-arch silhouette — evokes Pakistani
 * courthouse facades (a row of pointed/Mughal arches). Used only behind
 * the Login/AuthShell ink panel and the Landing page hero, per the design
 * system. Fully decorative: `pointer-events-none`, sits behind content via
 * `absolute inset-0`, and takes its color from the parent's text color so
 * it can render light-on-dark (ink panel) or dark-on-light (hero) —
 * opacity is controlled by the caller (6–15%) so it never affects legibility.
 */
/**
 * Design system v1 motif: large pointed arches drawn as thin outlines,
 * nested in pairs, rising from the bottom of an ink panel (design pages 2
 * and 7). Decorative; colour comes from the caller's text colour.
 */
export function ArchOutlines({ className = "" }) {
  const arch = (cx, w, top) =>
    `M${cx - w} 800V${top + w * 1.1}C${cx - w} ${top + w * 0.45} ${cx - w * 0.4} ${top + w * 0.12} ${cx} ${top}` +
    `C${cx + w * 0.4} ${top + w * 0.12} ${cx + w} ${top + w * 0.45} ${cx + w} ${top + w * 1.1}V800`;
  return (
    <svg
      className={`absolute inset-x-0 bottom-0 w-full h-[62%] pointer-events-none ${className}`}
      viewBox="0 0 860 800"
      preserveAspectRatio="xMidYMax slice"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      aria-hidden="true"
    >
      {[290, 762].map((cx) => (
        <g key={cx}>
          <path d={arch(cx, 208, 20)} />
          <path d={arch(cx, 152, 100)} />
          <path d={arch(cx, 96, 190)} />
        </g>
      ))}
    </svg>
  );
}

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
