// Mirrors backend/app/ai/contract_templates.py's required_fields exactly.
// No GET /contracts/templates endpoint exists — this wasn't part of the
// confirmed backend design (config, not an admin-editable resource), so the
// 3 types are hardcoded here rather than fetched.
import { CONTRACT_TYPES } from "@/constants";

export const CONTRACT_TEMPLATES = {
  [CONTRACT_TYPES.NDA]: {
    label: "Non-Disclosure Agreement",
    fields: [
      { key: "disclosing_party", label: "Disclosing party" },
      { key: "receiving_party", label: "Receiving party" },
      { key: "effective_date", label: "Effective date" },
      { key: "confidentiality_duration", label: "Confidentiality duration" },
    ],
  },
  [CONTRACT_TYPES.EMPLOYMENT]: {
    label: "Employment Agreement",
    fields: [
      { key: "employer_name", label: "Employer name" },
      { key: "employee_name", label: "Employee name" },
      { key: "job_title", label: "Job title" },
      { key: "start_date", label: "Start date" },
      { key: "compensation", label: "Compensation" },
    ],
  },
  [CONTRACT_TYPES.SERVICE_AGREEMENT]: {
    label: "Service Agreement",
    fields: [
      { key: "service_provider", label: "Service provider" },
      { key: "client_name", label: "Client" },
      { key: "scope_of_services", label: "Scope of services" },
      { key: "fee", label: "Fee" },
      { key: "effective_date", label: "Effective date" },
    ],
  },
};
