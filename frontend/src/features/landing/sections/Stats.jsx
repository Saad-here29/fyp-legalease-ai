import { useQuery } from "@tanstack/react-query";
import Container from "@/components/layout/Container";
import Section from "@/components/layout/Section";
import StatCard from "@/components/common/StatCard";
import { researchApi } from "@/features/legal-research/api";

// Every number here must be true and checkable:
//  - modules: built and working today — Case management, AI legal chat,
//    AI legal research, Document analysis, Contract drafting. Practice
//    simulator and Notifications aren't built; OCR for scanned files needs
//    Tesseract, which isn't installed. Update when a module ships.
//  - passages / documents: read live from the search index
//    (GET /research/stats), so they can't go stale after a rebuild.
export default function Stats() {
  const { data } = useQuery({
    queryKey: ["research-stats"],
    queryFn: researchApi.stats,
    staleTime: Infinity,
  });

  const stats = [
    { value: "5", label: "Working modules", helper: "Cases, chat, research, documents, contracts." },
    { value: "3", label: "User roles", helper: "Lawyer, client, student." },
    data?.chunks
      ? {
          value: data.chunks.toLocaleString(),
          label: "Indexed statute passages",
          helper: `From ${data.documents.toLocaleString()} Pakistani statute documents.`,
        }
      : { value: "—", label: "Indexed statute passages", helper: "Pakistani statute library." },
  ];

  return (
    <Section className="py-16 border-t border-hairline">
      <Container>
        <div className="grid gap-8 sm:grid-cols-3">
          {stats.map((stat, i) => (
            <StatCard
              key={stat.label}
              value={stat.value}
              label={stat.label}
              helper={stat.helper}
              last={i === stats.length - 1}
            />
          ))}
        </div>
      </Container>
    </Section>
  );
}
