# STRICT_GROUNDING: old vs new answers (2026-10-06)

The flag is **still off**; this is the measurement you approved.

**Method:**
- The new prompt (`STRICT_GROUNDING_RULES`) was run once on six saved answers,
  over each answer's **own saved passages**: the same passages, only the
  prompt differs.
- The old answers are the saved ones. The two controls were written with the
  September prompt, which had no language instruction yet.

**Groq:** 8 calls, **13,006 tokens**, including two
talaq rewrites (786 tokens) for the separate live score check. Model calls
stopped afterwards.

| Question | Old answer (words) | New answer (words) | Citation check (new) | Tokens |
|---|---:|---:|---|---:|
| Q3 (review) | 420 | 238 | 0 verified, 0 unverified, 0 case citations removed, 0 bad [n] markers removed | 2,698 |
| Q4 (review) | 250 | 90 | 0 verified, 0 unverified, 0 case citations removed, 0 bad [n] markers removed | 2,039 |
| Q6 (review) | 390 | 120 | 1 verified, 0 unverified, 0 case citations removed, 0 bad [n] markers removed | 1,815 |
| Q8 (review) | 226 | 91 | 0 verified, 0 unverified, 0 case citations removed, 0 bad [n] markers removed | 1,198 |
| Control: talaq procedure | 292 | 120 | 2 verified, 0 unverified, 0 case citations removed, 0 bad [n] markers removed | 2,335 |
| Control: murder, PPC s.302 | 202 | 106 | 5 verified, 0 unverified, 0 case citations removed, 0 bad [n] markers removed | 2,135 |

---

## Q3 (review)

**Question:** Can a spouse lawfully retain the other's personal property merely because the marriage has ended?

**Passages (same for both):** Muslim Family Laws Ordinance, 1961; THE MUSLIM FAMILY LAWS ORDINAN CE, 1961; THE COMPANIES ACT, 2017; THE WEST PAKISTAN FAMILY COURTS ACT, 1964; THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939; THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939

| Old (saved) | New (strict prompt) |
|---|---|
| 420 words | 238 words; citation check: 0 verified, 0 unverified, 0 case citations removed, 0 bad [n] markers removed |

### Old
> Short answer: Under Pakistani statutes a spouse may not lawfully keep the other’s personal property simply because the marriage has ended; the aggrieved party can seek a maintenance order, a share of movable property, or other relief through the family court or an Arbitration Council.  
>
> **Detailed breakdown**
>
> 1. **Maintenance and arbitration** – If a husband fails to maintain his wife adequately, the wife may apply to the Chairman to constitute an Arbitration Council, which can issue a certificate specifying the amount of maintenance the husband must pay [1]. This remedy is available irrespective of whether the marriage has been dissolved, and it obliges the husband to provide for the wife’s needs rather than retain her personal belongings.
>
> 2. **Share in movable property** – The Muslim Family Laws Ordinance, 1961 provides that a widow (or, by analogy, a wife after separation) is entitled to her share in the corpus of her husband’s movable property [2]. This statutory right prevents the husband from lawfully retaining the wife’s personal property after the marital relationship ends.
>
> 3. **Dissolution of marriage** – The Dissolution of Muslim Marriages Act, 1939 allows a woman to obtain a decree of dissolution on various grounds, such as the husband’s failure to provide maintenance for two years [6]. Once a decree is granted, the family court has jurisdiction to enforce the wife’s rights to maintenance and property under the relevant statutes [4].
>
> 4. **Family court jurisdiction** – The West Pakistan Family Courts Act, 1964 designates Family Courts as the appropriate forum for matters relating to marriage, maintenance, and property disputes arising from the dissolution of a marriage [4]. The court can order the return of personal property to its rightful owner and enforce maintenance certificates issued by an Arbitration Council.
>
> 5. **Remedies available** – Accordingly, a spouse whose personal property is being retained can:
>    - File an application with the Arbitration Council for a maintenance certificate (per [1]).
>    - Seek a share of the husband’s movable property as provided in the Muslim Family Laws Ordinance [2].
>    - Initiate dissolution proceedings under the Dissolution of Muslim Marriages Act [6] and, after obtaining a decree, approach the Family Court for enforcement of property rights [4].
>
> **Conclusion** – Pakistani law does not permit a spouse to keep the other’s personal property merely because the marriage has ended; statutory mechanisms exist to compel the return of such property and to provide financial support. If further procedural guidance is needed, the relevant family court rules and the prescribed forms for arbitration applications should be consulted.

### New
> Short answer: A spouse cannot lawfully keep the other’s personal property simply because the marriage has ended; the statutes only grant a widow a statutory share of the deceased husband’s movable assets and do not provide a right for a surviving spouse to retain all of the other’s property after divorce.
>
> **Detailed breakdown**
>
> 1. **Widow’s entitlement to a share of movable property** – Under the Muslim Family Laws Ordinance, 1961, a widow is expressly entitled to “her share in the corpus of movable property of her deceased husband” [2]. This provision limits a widow’s claim to a defined share rather than allowing her to retain all of the husband’s personal property.
>
> 2. **No statutory provision for retaining a former spouse’s personal property after divorce** – The Dissolution of Muslim Marriages Act, 1939, which governs the grounds and procedure for obtaining a decree of dissolution, contains no clause that confers upon a divorced spouse the right to retain the other’s personal (movable) property [5][6]. The Act focuses solely on the grounds for dissolution and does not address property distribution.
>
> 3. **Absence of applicable law in the retrieved passages** – The other cited statutes (e.g., the Companies Act, 2017 and the West Pakistan Family Courts Act, 1964) do not deal with the division of personal property between former spouses. Consequently, there is no statutory basis for a spouse to retain the other’s personal property merely because the marriage has ended.

---

## Q4 (review)

**Question:** What is a suit for restitution of conjugal rights?

**Passages (same for both):** THE WEST PAKISTAN FAMILY COURTS ACT, 1964; Muslim Family Laws Ordinance, 1961; THE WEST PAKISTAN FAMILY COURTS ACT, 1964; THE HINDU MARRIAGE ACT, 2017; THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939; THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939

| Old (saved) | New (strict prompt) |
|---|---|
| 250 words | 90 words; citation check: 0 verified, 0 unverified, 0 case citations removed, 0 bad [n] markers removed |

### Old
> Short answer: LegalEase’s statute library does not contain a specific provision describing a “suit for restitution of conjugal rights,” but the closest relevant authority is the West Pakistan Family Courts Act, 1964, which gives Family Courts jurisdiction over marriage‑related matters.  
>
> **Detailed breakdown**
>
> - The passages provided from the West Pakistan Family Courts Act, 1964 set out the general jurisdiction of Family Courts over matrimonial disputes, maintenance, and related procedures [1][4]. The Act does not contain a separate section that defines or regulates a suit for restitution of conjugal rights.
>
> - Because the statute library does not include a specific provision on restitution of conjugal rights, the exact nature, filing requirements, and remedies of such a suit cannot be detailed from the available texts.
>
> - However, where a marital dispute arises—including issues of marital co‑habitation or the enforcement of marital duties—the Family Court is the designated forum under the Act [1][4]. Parties may approach the Family Court for relief that the statute contemplates (e.g., maintenance, arbitration, dissolution), and the Court would apply the procedural rules prescribed for family matters.
>
> **Conclusion**  
> The specific concept of a “suit for restitution of conjugal rights” is not covered in the statutes currently available in LegalEase’s library; the nearest applicable provision is the general jurisdiction of Family Courts over marriage‑related cases under the West Pakistan Family Courts Act, 1964. For precise procedural guidance, one would need to consult the full text of the relevant family law statutes or rules that expressly address restitution of conjugal rights.

### New
> Short answer: The retrieved statutory provisions do not contain a definition or description of a suit for restitution of conjugal rights.  
>
> The passages provided—such as the West Pakistan Family Courts Act, 1964 [1], the Muslim Family Laws Ordinance, 1961 [2], the Hindu Marriage Act, 2017 [4], and the Dissolution of Muslim Marriages Act, 1939 [5][6]—address matters like family‑court jurisdiction, maintenance, marriage registration, and dissolution of marriage, but none of them define or regulate a suit for restitution of conjugal rights. Consequently, LegalEase’s statute library does not cover that specific concept.

---

## Q6 (review)

**Question:** Can a family-law advocate knowingly present false facts before the court merely to secure relief for the client?

**Passages (same for both):** THE SINDH INCUMBERED ESTATES ACT, 1896; THE SUCCESSION ACT, 1925; THE PAKISTAN AIR FORCE ACT, 1953

| Old (saved) | New (strict prompt) |
|---|---|
| 390 words | 120 words; citation check: 1 verified, 0 unverified, 0 case citations removed, 0 bad [n] markers removed |

### Old
> Short answer: No – a family‑law advocate who knowingly presents false facts before a court commits an offence under the Pakistan Penal Code and may also be punished under statutes that penalise false declarations, in addition to facing professional discipline.  
>
> **Detailed breakdown**
>
> 1. **Criminal liability for false statements** – The *Succession Act, 1925* expressly provides that a person who knowingly makes a false statement, or who knows that a statement is false, “shall be deemed to have committed an offence under section 193 of the Pakistan Penal Code (XLV of 1860)” [2]. This provision applies to any person who, in a legal proceeding, deliberately furnishes false information, which would include a family‑law advocate.
>
> 2. **Punishment for false declarations** – The *Pakistan Air Force Act, 1953* (which, although drafted for a specific service, contains a general offence of falsifying official documents) states that any person who “knowingly makes… any false or fraudulent statement” in a report, return, list, certificate, book or other document “shall, on conviction by court‑martial, be liable to suffer short imprisonment” [3]. The spirit of this provision reflects the broader legal principle that knowingly presenting false facts in any official document or testimony is punishable.
>
> 3. **Professional consequences** – While the statutes above do not name the legal profession, the same criminal provisions apply to advocates. An advocate who deliberately misleads the court breaches the duty of candour and honesty owed to the tribunal and to the administration of justice. Consequently, the advocate may be:
>    - Prosecuted under section 193 of the Pakistan Penal Code for giving false evidence, and/or under any applicable penal provision for falsification.
>    - Subject to disciplinary action by the relevant Bar Council or Supreme Court Bar Association, which can impose suspension or disbarment for professional misconduct.
>
> 4. **Implications for the client** – Relief obtained on the basis of false facts is vulnerable to being set aside. If the falsehood is discovered, the court may dismiss the claim, award costs against the advocate’s client, and refer the matter for criminal prosecution of the advocate.
>
> **Conclusion** – Under Pakistani law, knowingly presenting false facts before a family court is a criminal offence (section 193 PPC as reflected in the *Succession Act*) and is punishable as a false declaration (as per the *Pakistan Air Force Act*), and it also exposes the advocate to severe professional sanctions.

### New
> Short answer: No, a family‑law advocate who knowingly presents false facts before the court would be deemed to have given false evidence, which is an offence under the Pakistan Penal Code.  
>
> The Sindh Incumbered Estates Act provides that a person who “does not know or believe to be true” any statement made before a court “shall be deemed to have intentionally given false evidence within the meaning of the Pakistan Penal Code”[1]. Similarly, the Succession Act states that a person who makes a false statement “shall be deemed to have committed an offence under section 193 of the Pakistan Penal Code”[2]. Both provisions indicate that knowingly presenting false facts before a judicial authority constitutes false evidence and attracts criminal liability.

---

## Q8 (review)

**Question:** If a wife claims unpaid dower, who must establish the relevant facts?

**Passages (same for both):** THE QANUNESHAHADAT , 1984

| Old (saved) | New (strict prompt) |
|---|---|
| 226 words | 91 words; citation check: 0 verified, 0 unverified, 0 case citations removed, 0 bad [n] markers removed |

### Old
> Short answer: The wife, as the plaintiff, must prove the existence and non‑payment of the dower; the burden of establishing those facts rests on her.  
>
> **Detailed breakdown**
>
> 1. **Burden of proof in civil suits** – Under the law of evidence, a party may present evidence of “facts in issue” and of “relevant facts” in any suit or proceeding [1]. The party who asserts a particular fact bears the responsibility to prove it.
>
> 2. **Application to a dower claim** – In a suit where the wife alleges that the husband has failed to pay the dower (mahr), the claim of non‑payment is a *fact in issue*. Consequently, the wife must produce admissible evidence (e.g., the marriage contract, receipts, witnesses to the dower agreement, or any written acknowledgment) to establish that the dower was stipulated and remains unpaid.
>
> 3. **Effect of the husband’s denial** – The husband’s denial that the dower is unpaid does not shift the burden; it merely constitutes a defence. He may adduce his own evidence to rebut the wife’s claim, but the initial burden of proving the unpaid dower remains with the wife.  
>
> **Conclusion** – In a Pakistani family‑law suit for unpaid dower, the wife must establish the relevant facts concerning the dower’s amount, the obligation to pay, and the failure to do so, as required by the evidentiary rules governing facts in issue.

### New
> Short answer: The wife, as the claimant, must establish the relevant facts.  
>
> The provision on relevance of facts states that “Evidence may be given … of the existence or nonexistence of every fact in issue and of such other facts as are … declared to be relevant” [1]. It further notes that a person may not give evidence of a fact “which he is disentitled to prove” [1]. Accordingly, the party asserting a claim—here, the wife seeking unpaid dower—must present evidence to prove the facts in issue and any relevant facts.

---

## Control: talaq procedure

**Question:** What is the correct legal procedure for a husband to pronounce Talaq (divorce)?

**Passages (same for both):** THE CHILD MARRIAGE RESTRAINT ACT, 1929; THE WEST PAKISTAN FAMILY COURTS ACT, 1964; THE MUSLIM FAMILY LAWS ORDINAN CE, 1961; Muslim Family Laws Ordinance, 1961; THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939

| Old (saved) | New (strict prompt) |
|---|---|
| 292 words | 120 words; citation check: 2 verified, 0 unverified, 0 case citations removed, 0 bad [n] markers removed |

### Old
> The statutory framework that governs a husband’s right to pronounce **talaq** (divorce) for Muslims in Pakistan is set out in the **Muslim Family Laws Ordinance, 1961**, specifically **Section 7 – “Talaq.”**  That section is the only provision in the retrieved material that deals directly with the procedure for a husband to effect a talaq [3].
>
> The passages you have been provided with do not contain the full text of Section 7, so the detailed steps—such as the form of the declaration, any required notice periods, the role of the arbitration council (if any), and the filing of a decree in a family court—are **not covered by LegalEase’s statute library**.  Consequently, I cannot give a complete procedural checklist from the statutes that were retrieved.
>
> **What the library does show**
>
> * The **Muslim Family Laws Ordinance, 1961** includes a dedicated section on talaq (Section 7) [3].
> * For dissolution of marriage **other than by talaq** (e.g., khula, judicial dissolution), the **Dissolution of Muslim Marriages Act, 1939** provides the procedural regime [5].
>
> **Next steps for you**
>
> To obtain the exact legal procedure a husband must follow to pronounce talaq, you should consult **Section 7 of the Muslim Family Laws Ordinance, 1961** directly.  That provision will set out:
>
> 1. The form and manner in which the talaq must be uttered (e.g., oral, written, or electronic).  
> 2. Any required waiting period (iddah) and conditions that must be satisfied before the divorce becomes final.  
> 3. Whether the husband must obtain permission from an **Arbitration Council** (if applicable under the ordinance).  
> 4. The process for registering the divorce with the relevant Union Council or family court.  
>
> If you need assistance locating the full text of Section 7 or interpreting its requirements once you have it, feel free to ask.

### New
> Short answer: The retrieved statutes do not provide the detailed legal procedure for a husband to pronounce Talaq [3].  
>
> Detailed breakdown:  
> - The Muslim Family Laws Ordinance, 1961 lists a “Talaq” provision as Section 7, indicating that the Ordinance contains rules on the husband’s right to pronounce divorce [3].  
> - However, the excerpt supplied does not include the text of Section 7 or any procedural requirements, so the library does not contain the specific steps a husband must follow to effect a Talaq.  
> - Consequently, LegalEase’s statute library cannot supply the exact legal procedure for pronouncing Talaq; the user would need to consult the full text of the Muslim Family Laws Ordinance, 1961 or other relevant statutes for that information.

---

## Control: murder, PPC s.302

**Question:** What is murder under Section 302 of the Pakistan Penal Code?

**Passages (same for both):** Code of Criminal Procedure, 1898; THE CODE OF CRIMINAL PROCEDURE , 1898; Code of Criminal Procedure, 1898; THE CODE OF CRIMINAL PROCEDURE , 1898; THE CODE OF CRIMINAL PROCEDURE , 1898

| Old (saved) | New (strict prompt) |
|---|---|
| 202 words | 106 words; citation check: 5 verified, 0 unverified, 0 case citations removed, 0 bad [n] markers removed |

### Old
> Section 302 (unverified) of the Pakistan Penal Code is the provision that deals with the offence of **murder**.  In the passages supplied, Section 302 is repeatedly referred to as the statutory basis for a charge of murder (e.g., “committed murder … punishable under section 302 (unverified) of the Pakistan Penal Code” [1], [2]).  
>
> The library excerpts do not contain the full textual definition of murder itself; that definition is set out in Sections 299 and 300 of the Pakistan Penal Code, which are not included in the material provided.  Consequently, LegalEase’s statute library can confirm that:
>
> * Murder is the offence charged under **Section 302 (unverified)** of the Pakistan Penal Code, and it is tried within the cognizance of the Court of Session or a High Court [1], [2].
>
> For the precise legal definition (the elements required to constitute murder), one would need to consult the text of Sections 299‑300 of the Pakistan Penal Code, which is not covered by the current statutory excerpts.
>
> Note: the following references were not found in the statute text retrieved for this answer, so they are unverified. Check them against the statute before relying on them: Section 302 (Pakistan Penal Code); section 302 (Pakistan Penal Code).

### New
> Short answer: Murder is the offence defined in sections 299 and 300 of the Pakistan Penal Code, and Section 302 prescribes the punishment for that offence.  
>
> The retrieved provisions explain that a charge of murder under Section 302 is based on conduct that “fell within the definition of murder given in sections 299 and 300 of the Pakistan Penal Code”[2]. The same illustration appears in another passage, confirming that a murder charge assumes the act meets the definition set out in those sections[4]. The passages do not contain the substantive definition of murder itself; they only refer to the definition located in sections 299 and 300.
