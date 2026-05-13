import { motion } from "framer-motion";
import { Brain, Search, FileSearch, Languages, Quote, ShieldX } from "lucide-react";
import Container from "@/components/layout/Container";
import Section from "@/components/layout/Section";
import FeatureCard from "@/components/common/FeatureCard";
import { Badge } from "@/components/ui/badge";
import { fadeInUp } from "@/animations/variants";

const CAPABILITIES = [
  {
    icon: Brain,
    title: "RAG-Powered Q&A",
    description:
      "Retrieval-Augmented Generation pulls the top 5 most relevant passages from a FAISS vector index of Pakistani statutes and judgments before generating any answer.",
  },
  {
    icon: Languages,
    title: "Bilingual: English & Urdu",
    description:
      "Automatic language detection (≥95% accuracy) routes questions through multilingual sentence transformers and responds in the user's language.",
  },
  {
    icon: Quote,
    title: "Citation-Backed Answers",
    description:
      "Every AI response includes inline citations linking to the exact source statute or judgment. No hallucinations — at least one citation per answer.",
  },
  {
    icon: ShieldX,
    title: "Refuses What It Doesn't Know",
    description:
      "If no passage scores ≥0.7 similarity, the assistant transparently refuses instead of guessing. ≥90% correct refusal on out-of-library questions.",
  },
  {
    icon: FileSearch,
    title: "Document Intelligence",
    description:
      "Auto-summarise contracts and judgments to 5-10% of length, extract clauses (parties, jurisdiction, indemnity), and flag missing terms against templates.",
  },
  {
    icon: Search,
    title: "Semantic Legal Search",
    description:
      "Search the legal library by meaning, not keywords. Filter by court, year, and case type. Mean Reciprocal Rank ≥ 0.60 on the evaluation set.",
  },
];

export default function AICapabilities() {
  return (
    <Section id="ai-capabilities" className="relative">
      <Container>
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="max-w-3xl mx-auto text-center mb-16"
        >
          <Badge variant="gold" className="mb-4">
            AI Capabilities
          </Badge>
          <h2 className="font-serif text-4xl lg:text-5xl font-bold tracking-tight mb-5">
            Trustworthy AI, grounded in{" "}
            <span className="gold-text">Pakistani law</span>.
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            The platform combines retrieval, embeddings, and large language
            models — but every output is tied back to a verifiable source so
            lawyers can trust it in practice.
          </p>
        </motion.div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {CAPABILITIES.map((cap, i) => (
            <FeatureCard
              key={cap.title}
              icon={cap.icon}
              title={cap.title}
              description={cap.description}
              delay={(i % 3) * 0.1}
            />
          ))}
        </div>
      </Container>
    </Section>
  );
}
