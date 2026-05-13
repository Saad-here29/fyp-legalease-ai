import AnimatedCard from "./AnimatedCard";

/**
 * Feature highlight card — icon tile + title + description.
 * Used by Features and AI Capabilities sections.
 */
export default function FeatureCard({ icon: Icon, title, description, delay = 0 }) {
  return (
    <AnimatedCard delay={delay}>
      <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-gold-gradient shadow-lg shadow-legal-gold/20">
        <Icon className="h-6 w-6 text-legal-navy" strokeWidth={2.2} />
      </div>
      <h3 className="font-serif text-xl font-semibold text-foreground mb-2">
        {title}
      </h3>
      <p className="text-sm text-muted-foreground leading-relaxed">
        {description}
      </p>
    </AnimatedCard>
  );
}
