import Container from "@/components/layout/Container";
import Section from "@/components/layout/Section";
import StatCard from "@/components/common/StatCard";

const STATS = [
  { value: "9", label: "Modules", helper: "Case management to AI legal research." },
  { value: "3", label: "User Roles", helper: "Lawyer, Client, and Law Student." },
  { value: "100+", label: "Concurrent Users", helper: "Tested at <1% error rate." },
  { value: "<5s", label: "AI Answer Time", helper: "Cached p95 response latency." },
];

export default function Stats() {
  return (
    <Section className="py-16 lg:py-20">
      <Container>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {STATS.map((stat, i) => (
            <StatCard
              key={stat.label}
              value={stat.value}
              label={stat.label}
              helper={stat.helper}
              delay={i * 0.1}
            />
          ))}
        </div>
      </Container>
    </Section>
  );
}
