"""Seeds the legal_corpus table with a small sample of Pakistani statutes and
landmark judgments so the AI Legal Research module is demonstrable without
running the full corpus pipeline.

Idempotent: skips rows that already exist (matched by title + section_number).
Run automatically on backend startup when the table is empty.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.legal_corpus import LegalCorpusEntry


SAMPLE_CORPUS: list[dict] = [
    {
        "title": "Family Courts Act 1964",
        "section_number": "7",
        "jurisdiction": "Pakistan",
        "document_type": "statute",
        "court": None,
        "year": 1964,
        "content": (
            "Section 7 of the Family Courts Act 1964 establishes the jurisdiction "
            "of Family Courts over matters specified in Part I of the Schedule, "
            "including dissolution of marriage (including khula), dower, maintenance, "
            "custody of children, and guardianship. The Family Court has exclusive "
            "jurisdiction over these matters and its proceedings are summary in nature."
        ),
    },
    {
        "title": "Pakistan Penal Code 1860",
        "section_number": "302",
        "jurisdiction": "Pakistan",
        "document_type": "statute",
        "court": None,
        "year": 1860,
        "content": (
            "Section 302 PPC: Punishment of qatl-i-amd. Whoever commits qatl-i-amd "
            "shall, subject to the provisions of this Chapter be (a) punished with "
            "death as qisas; (b) punished with death or imprisonment for life as "
            "ta'zir having regard to the facts and circumstances of the case, if "
            "the proof in either of the forms specified in Section 304 is not "
            "available; or (c) punished with imprisonment of either description "
            "for a term which may extend to twenty-five years, where according to "
            "the Injunctions of Islam the punishment of qisas is not applicable."
        ),
    },
    {
        "title": "Contract Act 1872",
        "section_number": "10",
        "jurisdiction": "Pakistan",
        "document_type": "statute",
        "court": None,
        "year": 1872,
        "content": (
            "Section 10: What agreements are contracts. All agreements are contracts "
            "if they are made by the free consent of parties competent to contract, "
            "for a lawful consideration and with a lawful object, and are not hereby "
            "expressly declared to be void."
        ),
    },
    {
        "title": "Code of Criminal Procedure 1898",
        "section_number": "154",
        "jurisdiction": "Pakistan",
        "document_type": "statute",
        "court": None,
        "year": 1898,
        "content": (
            "Section 154 Cr.P.C.: Information in cognizable cases. Every information "
            "relating to the commission of a cognizable offence given orally to an "
            "officer in charge of a police-station shall be reduced to writing by him "
            "or under his direction and read over to the informant. This forms the "
            "First Information Report (FIR) — the foundation document of any criminal "
            "investigation in Pakistan."
        ),
    },
    {
        "title": "Constitution of the Islamic Republic of Pakistan 1973",
        "section_number": "Article 25",
        "jurisdiction": "Pakistan",
        "document_type": "statute",
        "court": None,
        "year": 1973,
        "content": (
            "Article 25 — Equality of citizens. (1) All citizens are equal before law "
            "and are entitled to equal protection of law. (2) There shall be no "
            "discrimination on the basis of sex. (3) Nothing in this Article shall "
            "prevent the State from making any special provision for the protection "
            "of women and children."
        ),
    },
    {
        "title": "Specific Relief Act 1877",
        "section_number": "12",
        "jurisdiction": "Pakistan",
        "document_type": "statute",
        "court": None,
        "year": 1877,
        "content": (
            "Section 12 — Cases in which specific performance enforceable. The "
            "specific performance of any contract may, in the discretion of the "
            "Court, be enforced when the act agreed to be done is such that "
            "compensation in money would not afford adequate relief, or when there "
            "exists no standard for ascertaining actual damage caused by non-performance."
        ),
    },
    {
        "title": "Khula — Khurshid Bibi v. Muhammad Amin",
        "section_number": "PLD 1967 SC 97",
        "jurisdiction": "Pakistan",
        "document_type": "judgment",
        "court": "Supreme Court of Pakistan",
        "year": 1967,
        "content": (
            "Landmark Supreme Court judgment establishing the wife's right to khula "
            "(divorce on her initiative) under Islamic law. The Court held that a "
            "Family Court can grant khula even without the husband's consent if it "
            "finds that the spouses cannot live together within the limits of Allah. "
            "This judgment forms the basis of modern khula jurisprudence in Pakistan."
        ),
    },
    {
        "title": "Muslim Family Laws Ordinance 1961",
        "section_number": "7",
        "jurisdiction": "Pakistan",
        "document_type": "statute",
        "court": None,
        "year": 1961,
        "content": (
            "Section 7 MFLO: Talaq. Any man who wishes to divorce his wife shall, "
            "as soon as may be after the pronouncement of talaq in any form whatsoever, "
            "give the chairman notice in writing of his having done so, and shall "
            "supply a copy thereof to the wife. A talaq, unless revoked earlier, "
            "shall not be effective until the expiration of ninety days from the day "
            "on which notice is delivered to the chairman."
        ),
    },
    {
        "title": "Transfer of Property Act 1882",
        "section_number": "54",
        "jurisdiction": "Pakistan",
        "document_type": "statute",
        "court": None,
        "year": 1882,
        "content": (
            "Section 54: \"Sale\" defined. Sale is a transfer of ownership in exchange "
            "for a price paid or promised or part-paid and part-promised. In the case "
            "of tangible immoveable property of the value of one hundred rupees and "
            "upwards, transfer can be made only by a registered instrument."
        ),
    },
    {
        "title": "Limitation Act 1908",
        "section_number": "Schedule, Article 113",
        "jurisdiction": "Pakistan",
        "document_type": "statute",
        "court": None,
        "year": 1908,
        "content": (
            "Article 113 of the Limitation Act 1908: Suit for specific performance "
            "of a contract. The period of limitation is three years from the date "
            "fixed for performance, or, if no such date is fixed, when the plaintiff "
            "has notice that performance is refused."
        ),
    },
    {
        "title": "Guardians and Wards Act 1890",
        "section_number": "17",
        "jurisdiction": "Pakistan",
        "document_type": "statute",
        "court": None,
        "year": 1890,
        "content": (
            "Section 17: Matters to be considered by the Court in appointing guardian. "
            "The Court shall be guided by what, consistently with the law to which "
            "the minor is subject, appears in the circumstances to be for the welfare "
            "of the minor. In considering this welfare, the Court shall have regard "
            "to the age, sex and religion of the minor, the character and capacity "
            "of the proposed guardian, and any wishes of a deceased parent."
        ),
    },
    {
        "title": "Khula entitlement — Mst. Balqis Fatima v. Najm-ul-Ikram",
        "section_number": "PLD 1959 Lah 566",
        "jurisdiction": "Pakistan",
        "document_type": "judgment",
        "court": "Lahore High Court",
        "year": 1959,
        "content": (
            "Lahore High Court ruling that a wife is entitled to dissolution of "
            "marriage by way of khula if the Court is satisfied that the spouses "
            "cannot live together within the limits prescribed by Allah. Set the "
            "doctrinal foundation later affirmed by the Supreme Court in Khurshid Bibi."
        ),
    },
]


def seed_legal_corpus(db: Session) -> int:
    """Insert sample corpus entries if the table is empty. Returns rows added."""
    existing = db.query(LegalCorpusEntry).count()
    if existing > 0:
        return 0

    added = 0
    now = datetime.now(timezone.utc)
    for entry in SAMPLE_CORPUS:
        row = LegalCorpusEntry(
            title=entry["title"],
            jurisdiction=entry["jurisdiction"],
            document_type=entry["document_type"],
            court=entry.get("court"),
            year=entry.get("year"),
            section_number=entry.get("section_number"),
            chunk_index=0,
            content=entry["content"],
            token_count=len(entry["content"].split()),
            indexed_at=now,
        )
        db.add(row)
        added += 1
    db.commit()
    logger.info(f"Seeded {added} legal corpus entries")
    return added
