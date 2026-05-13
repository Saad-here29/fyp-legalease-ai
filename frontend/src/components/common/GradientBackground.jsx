/**
 * Decorative background — animated gradient blobs over the dark legal theme.
 * Sits behind hero/landing content via absolute positioning.
 */
export default function GradientBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute inset-0 bg-legal-gradient" />

      {/* Animated gold blob — top right */}
      <div
        className="absolute -top-32 -right-32 h-[500px] w-[500px] rounded-full opacity-30 blur-3xl animate-pulse"
        style={{
          background:
            "radial-gradient(circle at center, rgba(201,169,97,0.5) 0%, transparent 70%)",
        }}
      />

      {/* Animated navy blob — bottom left */}
      <div
        className="absolute -bottom-32 -left-32 h-[600px] w-[600px] rounded-full opacity-40 blur-3xl"
        style={{
          background:
            "radial-gradient(circle at center, rgba(40,80,140,0.55) 0%, transparent 70%)",
        }}
      />

      {/* Subtle grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />
    </div>
  );
}
