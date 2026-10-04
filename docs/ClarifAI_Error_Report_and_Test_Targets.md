# ClarifAI: Error Report and Test Targets

**Basis:** 4 generated reports compared against their source contracts (Consulting Agreement, Cloud Infrastructure Consulting Agreement x2 runs, Commercial Lease), plus the repo PR history.
**Note:** The source code was not readable during this review. Each error below describes the symptom and the likely cause. Confirm the cause in the code before fixing.

**Headline:** The report is mostly wrong. Zero of 12 Cloud clause rows are fully correct, about 40% of rows are empty filler, and the Executive Overview contradicts the contract. Recent patches removed some visible symptoms but did not fix the underlying cause (summaries are filled from templates, not from the clause text).

---

## PART 1: ERROR SUMMARY (S1-S17)

This is the grouped summary. The full item-by-item list (A1-K4) is in **Part 4**. Items in Part 4 are tagged with their status in the latest Cloud run (report `0a71e9fb`).

### P0: Output is wrong (fix first)

**S1. Summaries are generated from templates, not from the clause text.**
Identical boilerplate appears across different contracts: "billing cadence", "reasonable care", "restrict access to authorized personnel", "strict secrecy", "land parcel", "easement", "reserved rent", "subscriber", "ordering party", "Employer and Employee", "designated territories". None of these words are in the source contracts.

**S2. There is no verification step.**
Nothing checks the generated text against the source clause. When one invented sentence is removed, another replaces it. Cloud confidentiality changed from "termination for convenience of contractual confidentiality covenants" to "material breach of contractual confidentiality covenants". Neither is in the contract.

**S3. Invented content (recurring).**
- A consequential-damages waiver ("both parties waive claims for lost profits, business interruption, or indirect losses") appears in liability clauses that have no such waiver (Consulting, Cloud run 1 and run 2).
- "Defense duty" and "defend" appear in the Cloud indemnity. The contract says only "indemnify and hold harmless".
- "Hold harmless" and "breach" are added as triggers in the Consulting indemnity. The only trigger is gross negligence.
- "Work made for hire" is applied to the Cloud IP clause. It is a payment-conditioned assignment.
- Lease report: "land parcel", "rights of easement", "reserved rent", "fixed long-term duration", "Replacement Value: rs.", and Overview duties "tenantable repair" and "discharge all municipal rates and taxes". Taxes are not in the lease, and repairs are split between Landlord and Tenant.
- Cloud non-compete: "designated territories" and "advise" are invented.
- Cloud confidentiality: invented duties (reasonable care, restricted access, strict secrecy) and an invented consequence.
- "Billing cadence" is invented in every Payment clause.

**S4. Misread or wrong facts.**
1. Cloud payment is 45 days from invoice date. Overview says "Net 30" (both runs).
2. Consulting: due on receipt, with interest only on balances more than 30 days past due. The report reads the 30 days as the payment term.
3. Consulting liability cap exceptions are gross negligence and breach of confidentiality. The report lists "indemnification, gross negligence, willful misconduct".
4. Consulting confidentiality runs 3 years after **expiration**. The report says **termination**.
5. Lease late fee is a flat 5% fee. The report calls it a "Late Interest Rate".
6. Cloud Overview calls immediate termination "vendor convenience". It is for cause and mutual. Convenience termination needs 30 days' notice and is also mutual.
7. Cloud Overview calls the non-solicit "mutual". It binds only the Consultant.
8. Cloud IP: "work made for hire" and "receipt of payment" instead of an assignment effective on **full payment of all applicable fees**.
9. Courts are shown without "state", "federal" or "county". Consulting says state courts in Travis County. Cloud says state and federal courts in New York County.
10. Consulting and lease Overviews call the document a generic "Commercial Agreement".

**S5. Specifics are dropped (your own eval reports only 56.7% fact retention).**
Missing from the reports:
- Cloud: 45 days, 30 days' notice, immediate termination for cause with no cure period, 3-year survival, consent requirement, 2-year term with no auto-renewal, 24 months, client-introduced scope and the "materially involved" employee limit, 12-month fee cap with no carve-outs, pre-existing IP carve-out, officers/directors/employees coverage, "New York" and "without regard to conflict of laws".
- Consulting: quarterly efficiency assessments, directors/staff indemnity coverage, compounding of interest, 3-year confidentiality tail.
- Lease: 3-year term (Nov 1, 2026 to Oct 31, 2029), 2,500 sq ft, address, rent due on the 1st, grace until the 5th, Landlord/Tenant repair split, consent for structural alterations, improvements becoming Landlord's property.

**S6. Failures are shown as normal content.**
- Raw enum `RISK_CLASSIFICATION_UNAVAILABLE` is printed in the Severity column in every report.
- The same fallback paragraph is shown as analysis ("This clause defines standard operative contractual provisions governing rights, access, or performance obligations between the parties...").
- Failed clauses are rated SAFE.
- Empty fields are printed ("Financial Terms: rs.", "Replacement Value: rs.").
- Unresolved placeholders are printed ("Obligated Party", "counterparty", "The designated contracting parties").

### P1: Structure and classification

**S7. Wrong categories (category seems to follow template position, not the clause heading).**
- Cloud: Term labeled "Termination". Non-compete labeled "Liability". Governing Law labeled "Dispute Resolution".
- Lease: Term labeled "Payment". Use of Premises labeled "Intellectual Property". Maintenance labeled "Liability". Governing Law labeled "Dispute Resolution".
- No categories exist for Term, Governing Law, Restrictive Covenants, Scope of Services, Property Use/Maintenance, Entire Agreement.

**S8. Severity logic is wrong.**
- Cloud liability cap (no carve-outs, floating cap) is rated LOW. It should be HIGH.
- Confidentiality is rated LOW although the tail is only 3 years for technical information.
- Severity is shown on clauses with no extracted content (filler rated SAFE).
- The report never says whose perspective severity is scored for.
- Lease Overview says "no high-severity risks" while most clauses have no real analysis.

**S9. Clause segmentation does not follow the contract's own numbered headings.**
- Lease has 7 clauses but the report has 8 rows. The Rent clause is split across rows 3 and 4 and every later row is offset.
- Page-break text is glued to the previous row ("...ordering party.4 HIGH Liability", "...covenants.4 HIGH", "...survive.9 HIGH", "...in this clause.4 SAFE").
- Stray empty bullets from the PDF are not removed.
- Preamble and signature block are not handled separately.

**S10. The Executive Overview is wrong and not tied to clause data.**
- Generic Purpose ("Commercial Agreement"), no agreement type, parties, date or term.
- The Overview text was identical across two Cloud runs although the clause rows changed. It is probably generated or cached separately from clause results.
- Key Terms contradict the clause table (Net 30, "work made for hire", "RS", mutual non-solicit).
- Overview mentions non-solicitation, but the Clause 10 row in run 2 does not.
- Key Risks miss the real ones: liability cap with no carve-outs, one-sided non-compete, 2% monthly compounding (about 26.8% a year), exclusive forum, missing signatures.

### P2: Missing analysis and output format

**S11. Document-level issues are never flagged.**
- Consulting Clause 5 double negative: "neither party's liability shall **not** exceed $50,000" (literally means liability must exceed $50,000).
- Lease Clause 2 refers to early termination "in accordance with the provisions herein" but the lease has no termination or default clause.
- Missing standard clauses: governing law, term, termination (Consulting); insurance, assignment/subletting, holdover, utilities, taxes, notices, deposit return, renewal (Lease); blank signature blocks (Cloud).
- Missing pre-existing IP carve-out and backup assignment (Consulting), no confidentiality exclusions (Consulting), no cure period (Cloud).

**S12. Locale and currency are hardcoded.**
- "rs." and "RS" appear in a USD document.
- "USD" is extracted as an amount ("$5,000.00, USD, $10,000.00") and the figures are not labeled (rent vs. deposit).

**S13. Report format problems.**
- Column "Original Text / Summary" never shows the original clause text.
- No per-clause confidence or "analysis failed" state.
- Header shows only the filename and Report ID. No contract title, parties, date or perspective.
- No document hash or fingerprint ties the report to its source file.

### Process and testing

**S14. The evaluation does not catch these errors.**
- It reports 100% "no-invention" while reports contain invented content. The check is too weak or tests the wrong thing.
- No clause-level ground truth for numbers, durations, parties, triggers, carve-outs.
- No checks for banned strings, wrong categories, row count vs clause count, Overview/clause consistency.

**S15. CI and release discipline.**
- Several PRs merged with failing checks (6 of 8, 7 of 9, 6 of 8 passed).
- Release report claims "100% production-ready, zero known limitations", contradicted by these reports.

**S16. Fixes are symptom patches.**
Between the two Cloud runs, blank gaps, "Employer and Employee" and one nonsense sentence were removed, but invented content, wrong facts and filler remain.

**S17. The summaries have no consistent structure or layout.**
- Each clause summary is one wall of text inside a single table cell. Section labels ("WHAT THIS CLAUSE MEANS:", "WHO IS AFFECTED:", "OBLIGATIONS & RIGHTS:", "IMPORTANT DETAILS:", "WHAT HAPPENS IF THE CONDITION IS NOT MET:") run together inline with no line breaks, and bullets ("•") are inline in the same paragraph.
- The sections are not the same from clause to clause. Some rows have IMPORTANT DETAILS, others do not. Some have the consequence section, others do not. The reader cannot scan for the same field across clauses.
- Rows have no clause number or heading from the contract, so the reader cannot match a row to the contract section.
- The Executive Overview is four one-line sentences (Purpose, Obligations, Key Terms, Key Risks). It has no parties, dates, term, key figures table, ranked risks, or risk counts.
- Severity is plain text. There is no colour or badge, no summary table of all clauses, and no way to see the high-severity clauses at a glance.
- The original clause text is not shown, and the summary, details and consequences are mixed together instead of separated.
- Page breaks fall in the middle of a clause and glue the next row's number and severity onto the previous text.

### Do not regress (things that work)
- Cloud clause count matches (12 rows for 12 clauses).
- Cloud non-compete binds the Consultant only.
- Lease labels Landlord (Lessor) and Tenant (Lessee) correctly.
- 2.0% per month, payment-conditioned IP transfer, and the $5,000 / $10,000 / 5% lease figures are extracted.

### Root causes to look for
1. Generation is template-driven, not extraction-driven.
2. No post-generation grounding check.
3. Classification and extraction failures are swallowed and replaced by filler.
4. Category assigned by position or template, not by heading and clause text.
5. Segmentation is not heading-based.
6. Overview is built independently of clause results (or cached).
7. Locale and currency defaults are hardcoded.
8. Eval harness has no clause-level ground truth.

---

## PART 2: TEST TARGETS (ground truth)

Use these as fixtures. "Must contain" means the report's clause row must include the fact (wording can differ). "Must NOT contain" means the fact or phrase is absent from the contract.

### Contract A: Cloud Infrastructure Consulting Agreement
Parties: Cascade Robotics Inc. (New York corporation, **Client**) and Vantage Point Cloud Solutions LLC (New York LLC, **Consultant**). Effective Nov 3, 2026. Signature blocks are blank.

| # | Heading | Correct category | Must contain | Must NOT contain | Expected severity (Client view / Consultant view) |
|---|---|---|---|---|---|
| 1 | Services | Scope of Services | cloud infrastructure design, DevOps automation, technical advisory, under Statements of Work | | LOW / LOW |
| 2 | Fees and Payment | Payment | 45 days from invoice date, undisputed invoices, 2.0% per month on past-due balance until paid | billing cadence, Net 30 | MEDIUM / MEDIUM |
| 3 | Confidentiality | Confidentiality | mutual, no disclosure without prior written consent, survives 3 years after termination | reasonable care, authorized personnel, strict secrecy, material breach | MEDIUM |
| 4 | Intellectual Property | Intellectual Property | assignment of deliverables, source code, documentation; effective on full payment of all fees; Consultant retains pre-existing tools, frameworks, methodologies | work made for hire, subscriber, analysis reports, ordering party | LOW / HIGH |
| 5 | Indemnification | Indemnification | mutual, third-party claims, own gross negligence or willful misconduct, covers officers, directors, employees | defend, defense duty, Employer, Employee | MEDIUM |
| 6 | Limitation of Liability | Limitation of Liability | total liability capped at fees paid by Client in prior 12 months; applies to contract, tort or otherwise; no carve-outs | consequential damages waiver, lost profits waiver | HIGH |
| 7 | Term | Term | fixed 2-year term from Effective Date, auto-terminates unless a new written agreement is signed, no auto-renewal | | MEDIUM |
| 8 | Termination | Termination | either party may terminate immediately on written notice for material breach (no cure period); either party may terminate for convenience on 30 days' written notice | vendor convenience only, post-termination obligations survive | MEDIUM |
| 9 | Dispute Resolution | Dispute Resolution | exclusive jurisdiction, state and federal courts, New York County, New York | | LOW / LOW |
| 10 | Non-Compete and Non-Solicitation | Restrictive Covenants | binds Consultant only; during term plus 24 months; no competing business with any client introduced by Client; no soliciting Client employees materially involved in performance | mutual, designated territories, hire, advise | LOW / HIGH |
| 11 | Governing Law | Governing Law | laws of the State of New York, without regard to conflict of laws principles | designated jurisdiction | LOW |
| 12 | Entire Agreement | General / Boilerplate | Agreement plus Statements of Work is the entire agreement; supersedes prior understandings, written or oral | | LOW |

**Overview must say:** Cloud Infrastructure Consulting Agreement; Cascade Robotics Inc. (Client) and Vantage Point Cloud Solutions LLC (Consultant); effective Nov 3, 2026; 2-year term; 45-day payment; 2% monthly late interest; mutual gross negligence/willful misconduct indemnity; fees-paid-12-months liability cap; Consultant-only 24-month non-compete.
**Overview must NOT say:** Net 30, work made for hire, vendor convenience, mutual non-solicit.
**Document-level findings to flag:** liability cap has no carve-outs (also caps indemnity and confidentiality), cap floats with fees paid, no cure period for breach, non-compete binds only Consultant, signature blocks are blank, no assignment or notices clause.

### Contract B: Strategic Consulting Services Agreement (Consulting Agreement, Dec 15, 2026)
Parties: Vantage Advisory Partners LLC (**Consultant**) and Vanguard Manufacturing Group (**Client**).

| # | Heading | Correct category | Must contain | Must NOT contain |
|---|---|---|---|---|
| 1 | Engagement and Deliverables | Scope of Services | strategic supply-chain advisory, quarterly efficiency assessments, per project schedules | strategic management, technical advisory, statements of work |
| 2 | Invoicing and Finance Charges | Payment | invoices due upon receipt; balances more than 30 days past due accrue 2.0% per month, compounding monthly (about 26.8% a year) | thirty days from invoice receipt as the payment term, billing cadence |
| 3 | Work Product Ownership | Intellectual Property | analysis reports, spreadsheets, custom models are work made for hire and Client's exclusive IP | modules, "transfers or operational performance" |
| 4 | Indemnity Obligations | Indemnification | Consultant defends and indemnifies Client, its directors and staff, against third-party claims from Consultant's gross negligence only | breach as a trigger, hold harmless |
| 5 | Aggregate Liability Cap | Limitation of Liability | $50,000 cap; exceptions are gross negligence and breach of confidentiality | indemnification and willful misconduct as exceptions, consequential damages waiver |
| 6 | Governing Forum | Dispute Resolution | exclusive jurisdiction, state courts, Travis County, Texas | |
| 7 | Confidentiality Covenant | Confidentiality | each party; non-public commercial and technical information; 3 years following **expiration** of the engagement | termination (as the trigger), reasonable care, authorized personnel |

**Document-level findings to flag:** Clause 5 double negative ("shall not exceed" preceded by "shall not"); no governing-law clause (forum only); no term, termination, fee amount or signature block; work-made-for-hire may not cover reports under US copyright law and there is no backup assignment or pre-existing IP carve-out; no standard confidentiality exclusions (public information, compelled disclosure). Confidentiality breach is uncapped.
**Overview must NOT say:** generic "Commercial Agreement" without saying consulting.

### Contract C: Commercial Lease Agreement (Sept 27, 2026)
Parties: Vanguard Commercial Properties LLC (**Landlord**, New York) and Quantum Analytics Inc. (**Tenant**, Boston). Signed by James Vance (Managing Director) and Sarah Jenkins (CEO). Currency: USD.

| # | Heading | Correct category | Must contain | Must NOT contain |
|---|---|---|---|---|
| 1 | Leased Premises | Property / Premises | about 2,500 sq ft office space at 450 Artisan Way, Suite 210, Boston, Massachusetts | land parcel, easement, reserved rent, fixed long-term |
| 2 | Term | Term | 3 years, Nov 1, 2026 to Oct 31, 2029, unless terminated earlier per the lease | |
| 3 | Rent and Financial Terms | Payment | base rent $5,000/month due on or before the 1st; security deposit $10,000 on execution; **flat** late fee of 5% of the overdue balance if paid after the 5th | rs., RS, "interest rate", USD as an amount |
| 4 | Use of Premises | Property Use | general corporate offices, professional services, software development, related admin; comply with zoning, ordinances, building regulations | Intellectual Property |
| 5 | Maintenance and Repairs | Maintenance | Landlord: structure, foundation, exterior walls, roof, plumbing, HVAC main lines; Tenant: interior, minor repairs, light fixtures, janitorial | Replacement Value, municipal rates and taxes |
| 6 | Alterations and Improvements | Alterations | no structural alterations without Landlord's prior written consent; permanent improvements become Landlord's property at expiration | |
| 7 | Governing Law | Governing Law | Massachusetts law, without regard to conflict of law principles | Dispute Resolution category, forum |

**Row count must be 7.** Rent (clause 3) must be one row.
**Overview must say:** commercial lease of office space in Boston; 3-year term; $5,000 monthly rent; $10,000 deposit; 5% flat late fee; Massachusetts law.
**Overview must NOT say:** RS, municipal rates and taxes, tenantable repair, no high-severity risks (unless severity analysis supports it).
**Document-level findings to flag:** Section 2 references early termination "in accordance with the provisions herein" but the lease has no termination or default clause; no deposit-return terms; no insurance, indemnity, assignment/subletting, holdover, utilities, taxes allocation, notices, renewal option or entire-agreement clause; no forum clause (governing law only); improvements revert to Landlord (tenant-side concern); stray empty bullets in the source PDF.

---

## PART 3: ACCEPTANCE CRITERIA (CI gates)

All must pass on contracts A, B, C and the 5 existing unseen docs. The build fails if any gate fails.

1. **Row count:** report rows equal the contract's numbered clause count (A=12, B=7, C=7).
2. **Category accuracy:** at least 98% match the table above (category derived from the heading first).
3. **Fact retention:** at least 95% of "Must contain" facts present (currently about 56.7%).
4. **No-invention:** 100%. No "Must NOT contain" phrase appears, and every number, party, trigger and exception in the output is found in the clause text.
5. **Banned strings anywhere in output:** `RISK_CLASSIFICATION_UNAVAILABLE`, "standard operative contractual provisions", "Obligated Party", "Counterparty", "designated contracting parties", "rs.", "RS", "billing cadence", "subscriber", "ordering party", "land parcel", "termination for convenience of contractual confidentiality", "material breach of contractual confidentiality covenants".
6. **Failure handling:** a clause that fails analysis shows "Analysis incomplete" with its verbatim text, never filler and never SAFE.
7. **Overview consistency:** every number, party and term in the Overview equals the clause-level value. Overview is built from verified clause results.
8. **Document-level checks:** all findings listed per contract above are reported.
9. **Header:** shows contract title, parties, date, "reviewing as" perspective, and a document hash.
10. **Original text:** each row shows the verbatim clause text separately from the summary.
11. **No page-break artifacts:** no digit or severity word glued to the end of the previous row.
12. **Severity:** matches the severity column above for the stated perspective, and every severity lists its reason or rule.
13. **Structure:** every clause card follows the fixed layout in Part 5, each section on its own line, same order in every clause, empty sections omitted, no run-on paragraphs.
14. **Overview structure:** the Overview has the sections listed in Part 5 (parties, key figures table, ranked risks, gaps, risk counts).
15. **CI:** all checks green before merge. Remove the "zero known limitations" claim until the gates pass.

---

## PART 4: DETAILED ERROR CATALOGUE (A1-K4)

Status tags refer to the latest Cloud run (report `0a71e9fb`) compared with the earlier Cloud run (`16946631`). Items with no tag were observed in at least one report and are not yet confirmed fixed. "STILL PRESENT" means it appears in the latest run.

### A. Hallucinated or invented content (not in the contract)
- **A1.** Invents a "billing cadence" in Payment clauses (Contracts 1 and 2). *STILL PRESENT.*
- **A2.** Invents confidentiality duties: "at least reasonable care", "restrict access strictly to authorized personnel", "strict secrecy". *STILL PRESENT.*
- **A3.** Invents the sentence "Unauthorized disclosure constitutes a termination for convenience of contractual confidentiality covenants". It appears in every confidentiality clause and makes no sense. *CHANGED: the latest run says "constitutes a material breach of contractual confidentiality covenants", which is also not in the contract. STILL PRESENT in a new form.*
- **A4.** Invents a consequential-damages waiver ("both parties waive claims for lost profits, business interruption, or indirect losses") in Liability Cap clauses where none exists. *STILL PRESENT.*
- **A5.** Says "work made for hire" for the Cloud contract, which uses a direct assignment ("hereby assigns"). *STILL PRESENT.*
- **A6.** Invents "defense duty" and "defend" in the Cloud indemnity, which says only "indemnify and hold harmless". *STILL PRESENT.*
- **A7.** Invents "hold harmless" and "breach" as an indemnity trigger in Contract 1, where the only trigger is gross negligence.
- **A8.** Invents the wrong cap exceptions in Contract 1: "indemnification, gross negligence, willful misconduct". The real ones are gross negligence and breach of confidentiality.
- **A9.** Invents land-lease language in the commercial lease: "land parcel", "rights of easement", "reserved rent", "fixed long-term duration".
- **A10.** Invents "Replacement Value: rs." in the lease Maintenance row.
- **A11.** Invents "designated territories" and "hire" in the non-compete (Cloud contract). *PARTLY FIXED: "hire" is gone. "designated territories" and "advise" are still present.*
- **A12.** Invents "Employer and Employee" as parties in B2B contracts (Cloud Indemnity and Non-compete). *FIXED in the latest Cloud run (now "designated contracting parties" or "Consultant and the Client"). Still present in the lease run's earlier-pattern risk; add a test.*
- **A13.** Uses the word "subscriber" in the Cloud IP clause. *STILL PRESENT.*
- **A14.** Says "analysis reports" and "custom modules" in the IP clauses. The Cloud contract says "deliverables, source code, and documentation". *STILL PRESENT ("analysis reports").*
- **A15.** Invents tenant duties in the lease Overview: "tenantable repair" and "discharge all municipal rates and taxes". Taxes are not mentioned, and repairs are split between Landlord and Tenant.
- **A16.** Invents "strategic management and technical advisory" and "statements of work" in Contract 1. The contract says supply-chain advisory and quarterly efficiency assessments per project schedules.

### B. Wrong facts
- **B1.** The Cloud contract's payment term is 45 days from invoice date, but the Overview says "Net 30". *STILL PRESENT.*
- **B2.** Contract 1's payment term is due on receipt, but the report says "thirty days from invoice receipt". It misreads the 30-day interest grace period as the payment term.
- **B3.** Cloud Overview says "immediate termination for vendor convenience". Immediate termination is for cause only and is mutual. Termination for convenience needs 30 days' notice. *STILL PRESENT.*
- **B4.** Cloud Overview and Clause 10 call the non-solicit "mutual", but the clause binds only the Consultant. *PARTLY FIXED: the Clause 10 row now says the Consultant is bound (though it says "restricts parties"). The Overview still says "mutual". STILL PRESENT in the Overview.*
- **B5.** Cloud Overview says IP vests "as work made for hire", but it is a payment-conditioned assignment with the Consultant's pre-existing IP excluded. *STILL PRESENT.*
- **B6.** Confidentiality says "termination" where Contract 1 says "expiration".
- **B7.** Forum: Contract 1 says "state courts" in Travis County, but the report drops "state". The Cloud contract says "state and federal courts in New York County", but the report says only "courts of New York". *STILL PRESENT.*
- **B8.** The lease's late fee is a flat 5% fee after the 5th, but the report labels it "Late Interest Rate".
- **B9.** The report extracts "$5,000.00, USD, $10,000.00" as the Financial Amount. It treats the currency label "USD" as a value, labels no amounts, and never says which is rent and which is the deposit.
- **B10.** The lease Overview and Payment rows use "RS"/"rs." (rupees) in a USD document.
- **B11.** The Contract 1 Overview calls it a generic "Commercial Agreement" instead of a consulting agreement. The lease Overview calls it a "Commercial Agreement" instead of a commercial lease. *STILL PRESENT (Cloud Overview is also a generic "Commercial Agreement").*
- **B12.** The Cloud non-compete is described as covering the other party's employees. The actual clause covers only Client employees materially involved in the work and only clients introduced by Client. *CHANGED: the latest run drops the non-solicit part entirely. See C8.*

### C. Missing specifics (dropped facts)
- **C1.** Cloud Payment: the 45-day window is missing from the clause row. *STILL PRESENT.*
- **C2.** Cloud Confidentiality: the 3-year survival after termination and the prior-written-consent rule are missing. *STILL PRESENT.*
- **C3.** Cloud IP: the Consultant's pre-existing tools, frameworks and methodologies carve-out is missing. *STILL PRESENT.*
- **C4.** Cloud Indemnity: the gross negligence/willful misconduct trigger and the officers/directors/employees coverage are missing. *STILL PRESENT.*
- **C5.** Cloud Liability Cap: the formula (fees paid in the prior 12 months) and the lack of carve-outs are missing. *STILL PRESENT.*
- **C6.** Cloud Term: the 2-year fixed term and no auto-renewal are missing. *STILL PRESENT (row is filler).*
- **C7.** Cloud Termination: the 30-day convenience notice and immediate termination with no cure period are missing. The earlier run also had blank gaps ("notice requirements, , and conditions", "breach and ."). *Blank gaps FIXED. 30-day notice and "immediate" are STILL MISSING.*
- **C8.** Cloud Non-compete: the 24-month tail and the client-introduced scope are missing. *STILL PRESENT. The non-solicit half of the clause is also missing in the latest run.*
- **C9.** Cloud Governing Law: it says "designated jurisdiction" and never says New York or "without regard to conflict of laws". *STILL PRESENT.*
- **C10.** Lease: the 2,500 sq ft, address, 3-year term (Nov 1, 2026 to Oct 31, 2029), rent due on the 1st, grace until the 5th, Landlord/Tenant maintenance split, no structural alterations without consent, and improvements becoming Landlord's property are all missing.
- **C11.** Contract 1: the quarterly efficiency assessments, the directors/staff indemnity coverage, and the 2% compounding rate are missing from the Key Risks.

### D. Failure states shown as real output
- **D1.** The raw enum `RISK_CLASSIFICATION_UNAVAILABLE` appears in the Severity column (Contract 1 row 1, Cloud rows 1 and 12, Lease rows 1, 3 and 7). *STILL PRESENT.*
- **D2.** The identical fallback paragraph "standard operative contractual provisions governing rights, access, or performance obligations" is shown as analysis (Cloud rows 1, 7 and 12, Lease rows 2, 3, 5, 6 and 7). *STILL PRESENT.*
- **D3.** Failed or empty clauses are rated SAFE (Cloud rows 7 and 11, Lease rows 2, 5, 6 and 8). *STILL PRESENT.*
- **D4.** Empty field values are printed: "Financial Terms: rs.", "Replacement Value: rs.".
- **D5.** Blank gaps appear in generated text ("notice requirements, , and conditions"). *FIXED in the latest Cloud run.*
- **D6.** Unresolved placeholders are shown: "Obligated Party", "Counterparty", "The designated contracting parties", "Payment Due Window" with no value. *STILL PRESENT ("Obligated Party", "counterparty", "designated contracting parties").*

### E. Wrong categories
- **E1.** Cloud Term (Section 7) is labeled "Termination". *STILL PRESENT.*
- **E2.** Cloud Non-compete is labeled "Liability". *STILL PRESENT.*
- **E3.** Cloud Governing Law is labeled "Dispute Resolution". *STILL PRESENT.*
- **E4.** Lease Term is labeled "Payment".
- **E5.** Lease Use of Premises is labeled "Intellectual Property".
- **E6.** Lease Maintenance is labeled "Liability".
- **E7.** Lease Governing Law is labeled "Dispute Resolution".
- **E8.** Category appears to follow template position instead of the clause heading, even though the contract headings are in the text.

### F. Wrong or questionable severity
- **F1.** Cloud Liability Cap is rated LOW. It should be HIGH, because there are no carve-outs, so it also caps indemnity, confidentiality and willful misconduct, and it floats with fees paid. *STILL PRESENT.*
- **F2.** Confidentiality is rated LOW in Contract 1 and the Cloud contract. A 3-year tail for technical information is short, and confidentiality breaches are uncapped in Contract 1. *STILL PRESENT.*
- **F3.** Cloud Dispute Resolution is rated HIGH, which is arguably overrated because both parties are New York entities and the clause is mutual. *STILL PRESENT.*
- **F4.** The report never states whose perspective severity is scored from, so IP, non-compete and late-fee clauses are rated without knowing which party is affected. *STILL PRESENT.*
- **F5.** The lease Overview says "No high-severity legal risks were identified" although the report contains no real analysis of most clauses.

### G. Clause segmentation problems
- **G1.** The lease has 7 clauses but the report has 8 rows. The Rent clause is split across rows 3 and 4, and everything after is offset.
- **G2.** Page-break text is concatenated to the previous row ("...ordering party.4 HIGH Liability", "...covenants.4 HIGH", "...survive.9 HIGH", "...in this clause.4 SAFE Payment"). *STILL PRESENT.*
- **G3.** Stray empty bullets from the source PDF are not stripped.
- **G4.** The preamble and signature block are not handled separately from clauses.

### H. Executive Overview errors
- **H1.** Cloud Purpose is garbled: "This More Statements Of Work Executed By Both Parties Under This Agreement establishes...". A clause-1 fragment was mistaken for the title. *FIXED in the latest Cloud run (Purpose is now generic instead).*
- **H2.** No Overview names the parties, date, term or premises. *STILL PRESENT.*
- **H3.** Key Terms contradict the clause data (see B1, B5, B10). *STILL PRESENT.*
- **H4.** Key Risks leave out important items: the 2% monthly compounding interest (about 26.8% a year), the exclusive forum, and the liability cap exceptions. *STILL PRESENT.*
- **H5.** Lease Key Terms say "specify RS, payable per agreed schedule" and omit the actual $5,000, $10,000 and 5%.
- **H6 (new).** The Cloud Overview text is identical in both runs even though the clause rows changed, so it is probably generated or cached separately from the clause results. It also now mentions non-solicitation, which the Clause 10 row no longer mentions.

### I. Document-level issues the report never flags
- **I1.** Contract 1, Clause 5 has a double negative ("neither party's liability shall not exceed $50,000"), which literally means liability must exceed $50,000.
- **I2.** The lease, Clause 2 refers to early termination "in accordance with the provisions herein", but the lease has no termination or default clause.
- **I3.** Missing standard clauses are not flagged: governing law (Contract 1), term and termination (Contract 1), insurance, assignment/subletting, holdover, utilities, taxes, notices and deposit return (lease), and a signature block (Contracts 1 and 2).
- **I4.** Contract 1, Clause 3 has no pre-existing IP carve-out or backup assignment.
- **I5.** Contract 1, Clause 7 has no standard confidentiality exclusions (public information, compelled disclosure).
- **I6.** Contract 1 has no fee amounts and no term.
- **I7 (new).** Cloud: Clause 6 has no carve-outs, Clause 8 has no cure period, Clause 10 binds only the Consultant, and the signature blocks are blank. None of this is flagged.

### J. Output and format issues
- **J1.** The column "Original Text / Summary" never shows the original clause text. *STILL PRESENT.*
- **J2.** No per-clause confidence or "analysis failed" state is shown. *STILL PRESENT.*
- **J3.** Output uses the same template text for many different clauses, which suggests generation from templates instead of from the clause text. *STILL PRESENT.*
- **J4 (new).** The report header shows only a filename and Report ID, with no contract title, parties, date, or document hash tying the report to its source file.

- **J5 (new).** Each clause summary is a single run-on paragraph. Section labels and "•" bullets are inline, with no line breaks. *STILL PRESENT in every report.*
- **J6 (new).** The sections are inconsistent between clauses (IMPORTANT DETAILS and WHAT HAPPENS IF... appear on some rows and not others), so fields cannot be compared across clauses.
- **J7 (new).** Rows show no clause number or heading from the contract, only a position number that can drift from the real clause number (see G1).
- **J8 (new).** The Executive Overview is four one-line sentences. It has no parties, dates, term, key-figures table, ranked risk list, risk counts or gaps section.
- **J9 (new).** There is no severity summary table or colour-coded badge, and no separation between the original text, the plain-language summary, the key details and the consequences.

### K. Project and CI issues (from the repo PRs)
- **K1.** Fact retention is reported at only 56.7%, which matches the dropped-facts errors in section C.
- **K2.** The eval harness doesn't catch these error types (invented text, wrong categories, wrong numbers, failure text shown as content). It reports 100% "no-invention" while reports contain invented content.
- **K3.** Several PRs were merged with CI checks failing (6 of 8, 7 of 9 and 6 of 8 passed).
- **K4.** The release report certifies "zero known limitations" and "100% production-ready", which the reports contradict.
- **K5 (new).** Fixes between runs are symptom patches: blank gaps, "Employer and Employee" and one nonsense sentence were removed, but invented content, wrong facts and filler remain, so the cause is untouched.

### Root-cause summary
1. Template-driven generation: the model fills a fixed template instead of reading the clause.
2. No verification step that checks output against the source text.
3. Classification and extraction failures aren't surfaced; filler is shown instead.
4. Category comes from template position, not the clause heading.
5. Clause segmentation doesn't follow the contract's own numbered headings.
6. The Overview is generated separately and not checked against the clause data.
7. Locale and currency defaults are hardcoded (rs.).
8. The eval harness has no ground truth for these cases.

---

## PART 5: REQUIRED REPORT STRUCTURE (layout spec)

Fix S17 and J5-J9 by making the renderer produce this exact structure from structured data (JSON), not from one free-text paragraph.

### 5.1 Report header
- Contract title and type (for example "Cloud Infrastructure Consulting Agreement")
- Parties with roles (for example "Cascade Robotics Inc. (Client), Vantage Point Cloud Solutions LLC (Consultant)")
- Effective date and term (or "Not stated")
- "Reviewing as": Client / Consultant / Landlord / Tenant / Neutral
- Report ID, document hash, source filename, generation date, language

### 5.2 Executive Overview (separate labelled sections, each on its own line)
1. **Purpose:** one sentence naming the agreement type, parties and subject.
2. **Key figures table:** Item | Value | Clause. Example rows: Payment term | 45 days from invoice date | 2. Late interest | 2.0% per month | 2. Term | 2 years, no auto-renewal | 7. Liability cap | fees paid in prior 12 months | 6. Termination notice | 30 days for convenience | 8. Governing law / forum | New York law, New York County courts | 9, 11.
3. **Top risks:** ranked list, highest first. Each item gives severity, clause number, one sentence, and why it matters for the reviewing party.
4. **Gaps and drafting issues:** missing clauses, double negatives, dangling references, blank signatures.
5. **Risk count:** for example "HIGH 3 / MEDIUM 4 / LOW 4 / Needs review 1".

Every value in the Overview must come from the clause results (Part 3, gate 7).

### 5.3 Clause summary table (one line per clause, at the top)
Columns: No. (from the contract) | Heading | Category | Severity (colour badge plus text) | One-line takeaway.
Keep contract order. Offer a "sort by severity" option.

### 5.4 Clause card (one per clause, same layout every time)
Each section below is its own line or block. Omit a section if there is nothing grounded to put in it. Never fill it with filler.

1. **Header:** clause number, heading from the contract, category, severity badge, confidence.
2. **Original text:** the verbatim clause text (collapsible if long).
3. **In plain language:** 1 to 2 sentences, grounded in the clause only.
4. **Who is bound:** real party names or roles ("Consultant only", "Both parties").
5. **Key details:** a labelled list of extracted values, each with its unit and label, for example: Payment window: 45 days from invoice date. Late interest: 2.0% per month. Do not print empty fields.
6. **Why this severity:** the rule or reason, and which party it affects.
7. **If the condition is not met:** only if the clause states a consequence.
8. **Not stated in this clause:** optional list of notable gaps (for example "No cure period").

If analysis fails for a clause, show: header, original text, and "Analysis incomplete: <reason>". Do not show a raw enum or generic filler.

### 5.5 Rendering rules
- Real line breaks and real bullet lists. No inline "•" and no run-on label text.
- Same section order in every clause card.
- Do not split a clause card across a page break, or if unavoidable, repeat the clause number on the new page. Never glue the next clause number or severity to the previous text.
- Severity shown as colour plus text (accessible), with a legend.
- Fixed fonts and spacing, readable cell width. Do not put a whole clause analysis in one narrow table cell.
- Hindi output uses the same structure and the same order.
- Footer disclaimer stays.

### 5.6 Data contract for the renderer (suggested)
```json
{
  "header": {"title": "", "type": "", "parties": [{"name": "", "role": ""}], "effective_date": "", "term": "", "reviewing_as": "", "report_id": "", "doc_hash": ""},
  "overview": {"purpose": "", "key_figures": [{"item": "", "value": "", "clause": 0}], "top_risks": [{"severity": "", "clause": 0, "text": "", "why": ""}], "gaps": [""], "risk_counts": {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "REVIEW": 0}},
  "clauses": [{
    "number": 0, "heading": "", "category": "", "severity": "", "confidence": 0.0,
    "original_text": "",
    "plain_language": "",
    "who_is_bound": "",
    "key_details": [{"label": "", "value": "", "source_quote": ""}],
    "severity_reason": "",
    "if_not_met": "",
    "not_stated": [""],
    "status": "ok | analysis_incomplete"
  }]
}
```
The renderer only prints fields that exist and pass the verification step. Every `key_details` value must have a `source_quote` that appears in `original_text`.
