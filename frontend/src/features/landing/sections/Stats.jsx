import Container from "@/components/layout/Container";
import Section from "@/components/layout/Section";
import StatCard from "@/components/common/StatCard";

const STATS = [
  { value: "9", label: "Modules", helper: "One platform, every workflow." },
  { value: "3", label: "User roles", helper: "Lawyer, client, student." },
  { value: "<5s", label: "AI answer time", helper: "Cached p95 latency." },
];

export default function Stats() {
  return (
    <Section className="py-16 border-t border-hairline">
      <Container>
        <div className="grid gap-8 sm:grid-cols-3">
          {STATS.map((stat, i) => (
            <StatCard
              key={stat.label}
              value={stat.value}
              label={stat.label}
              helper={stat.helper}
              last={i === STATS.length - 1}
            />
          ))}
        </div>
      </Container>
    </Section>
  );
}
