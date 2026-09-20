"""Contract template configuration — Contract Drafting & Compliance module.

Static config, not a DB table: these are curated legal-template structures
for a fixed, small set of contract types, not user- or admin-editable data.
See the design note handed back with this module for the reasoning.

Each entry has three parts, used by different steps of the pipeline:
    - required_fields: what the caller must supply in POST /contracts/draft.
      ContractService.draft() validates every key is present before calling
      the AI client at all.
    - template_structure: a skeleton fed to the LLM as grounding context —
      it's a guide for what the generated contract should contain, not a
      string substituted directly into the output (the LLM writes real
      prose from the filled fields, not a mail-merge).
    - required_clauses: keyword patterns used by ContractService's
      deterministic compliance checker (POST /contracts/{id}/check-
      compliance) — plain case-insensitive substring search against the
      generated text, no LLM call involved. A clause "passes" if ANY one
      of its keywords is found.
"""

from app.models.enums import ContractType

CONTRACT_TEMPLATES: dict[ContractType, dict] = {
    ContractType.NDA: {
        "label": "Non-Disclosure Agreement",
        "required_fields": [
            {"key": "disclosing_party", "label": "Disclosing party"},
            {"key": "receiving_party", "label": "Receiving party"},
            {"key": "effective_date", "label": "Effective date"},
            {"key": "confidentiality_duration", "label": "Confidentiality duration"},
        ],
        "template_structure": (
            "NON-DISCLOSURE AGREEMENT\n\n"
            "This Non-Disclosure Agreement (\"Agreement\") is entered into as of "
            "{{effective_date}} between {{disclosing_party}} (\"Disclosing Party\") "
            "and {{receiving_party}} (\"Receiving Party\").\n\n"
            "1. Definition of Confidential Information\n"
            "2. Obligations of the Receiving Party\n"
            "3. Term — confidentiality obligations survive for {{confidentiality_duration}} "
            "from the Effective Date\n"
            "4. Exclusions from Confidential Information\n"
            "5. Governing Law and Jurisdiction\n"
            "6. Remedies — acknowledgement that breach may cause irreparable harm, "
            "entitling the Disclosing Party to injunctive relief in addition to any "
            "other remedies\n"
            "7. General Provisions (entire agreement, amendment, severability)"
        ),
        "required_clauses": [
            {
                "name": "Confidentiality clause",
                "keywords": ["confidential information", "non-disclosure", "proprietary information"],
            },
            {
                "name": "Term/duration clause",
                "keywords": ["term of this agreement", "duration", "shall remain in effect", "survive"],
            },
            {
                "name": "Governing law clause",
                "keywords": ["governing law", "governed by the laws of", "jurisdiction"],
            },
            {
                "name": "Remedies clause",
                "keywords": ["injunctive relief", "irreparable harm", "remedies"],
            },
        ],
    },
    ContractType.EMPLOYMENT: {
        "label": "Employment Agreement",
        "required_fields": [
            {"key": "employer_name", "label": "Employer name"},
            {"key": "employee_name", "label": "Employee name"},
            {"key": "job_title", "label": "Job title"},
            {"key": "start_date", "label": "Start date"},
            {"key": "compensation", "label": "Compensation"},
        ],
        "template_structure": (
            "EMPLOYMENT AGREEMENT\n\n"
            "This Employment Agreement is entered into between {{employer_name}} "
            "(\"Employer\") and {{employee_name}} (\"Employee\"), for the position of "
            "{{job_title}}, commencing {{start_date}}.\n\n"
            "1. Position and Duties\n"
            "2. Compensation — {{compensation}}, and payment schedule\n"
            "3. Term of Employment and Termination — notice periods, grounds for "
            "termination by either party\n"
            "4. Confidentiality Obligations\n"
            "5. Governing Law and Jurisdiction\n"
            "6. General Provisions"
        ),
        "required_clauses": [
            {
                "name": "Compensation clause",
                "keywords": ["compensation", "salary", "remuneration"],
            },
            {
                "name": "Term/termination clause",
                "keywords": ["term of employment", "termination", "notice period"],
            },
            {
                "name": "Confidentiality clause",
                "keywords": ["confidential", "non-disclosure", "proprietary information"],
            },
            {
                "name": "Governing law clause",
                "keywords": ["governing law", "governed by the laws of", "jurisdiction"],
            },
        ],
    },
    ContractType.SERVICE_AGREEMENT: {
        "label": "Service Agreement",
        "required_fields": [
            {"key": "service_provider", "label": "Service provider"},
            {"key": "client_name", "label": "Client"},
            {"key": "scope_of_services", "label": "Scope of services"},
            {"key": "fee", "label": "Fee"},
            {"key": "effective_date", "label": "Effective date"},
        ],
        "template_structure": (
            "SERVICE AGREEMENT\n\n"
            "This Service Agreement is entered into as of {{effective_date}} between "
            "{{service_provider}} (\"Service Provider\") and {{client_name}} (\"Client\").\n\n"
            "1. Scope of Services — {{scope_of_services}}\n"
            "2. Fees and Payment Terms — {{fee}}\n"
            "3. Term and Termination\n"
            "4. Confidentiality\n"
            "5. Limitation of Liability\n"
            "6. Governing Law and Jurisdiction\n"
            "7. General Provisions"
        ),
        "required_clauses": [
            {
                "name": "Scope of services clause",
                "keywords": ["scope of services", "scope of work", "services to be provided"],
            },
            {
                "name": "Payment/fees clause",
                "keywords": ["fees", "payment terms", "compensation"],
            },
            {
                "name": "Term/termination clause",
                "keywords": ["term of this agreement", "termination", "notice period"],
            },
            {
                "name": "Governing law clause",
                "keywords": ["governing law", "governed by the laws of", "jurisdiction"],
            },
        ],
    },
}


def get_template(contract_type: ContractType) -> dict:
    return CONTRACT_TEMPLATES[contract_type]
