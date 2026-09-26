/**
 * Feature/module highlight for landing sections — flat, top hairline rule
 * instead of a rounded shadowed card.
 */
export default function FeatureCard({ icon: Icon, title, description }) {
  return (
    <div className="pt-6 border-t-2 border-ink-text">
      <Icon className="h-5 w-5 text-brick mb-5" strokeWidth={2} />
      <h3 className="font-editorial text-2xl text-ink-text mb-3">{title}</h3>
      <p className="text-base text-ink-muted leading-relaxed">{description}</p>
    </div>
  );
}
