/**
 * Feature/module highlight for landing sections — flat, top hairline rule
 * instead of a rounded shadowed card.
 */
export default function FeatureCard({ icon: Icon, title, description }) {
  return (
    <div className="pt-6 border-t border-hairline">
      <Icon className="h-5 w-5 text-ink-muted mb-4" strokeWidth={2} />
      <h3 className="font-editorial text-lg text-ink-text mb-2">{title}</h3>
      <p className="text-sm text-ink-muted leading-relaxed">{description}</p>
    </div>
  );
}
