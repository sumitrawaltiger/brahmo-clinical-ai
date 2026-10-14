# Mini-eval results (extractive mode)

index: `rag-index-1.0:chunker-1.0.0:local-hashed-char-ngram-v1:f311f98775e8da86`

**11 correct · 0 abstained · 0 wrong** (held-out-style total 9; uncited numbers: 0)

| id | expected | got | verdict | cited | checks |
|---|---|---|---|---|---|
| Q1 | answer | answer | **correct** | STW-PED-01 v2024.1 | — |
| Q2 | answer | answer | **correct** | STW-PED-02 v2023.2 | — |
| Q3 | answer | answer | **correct** | STW-GP-02 v2025.2 | — |
| Q4 | answer | answer | **correct** | STW-GP-04 v2024.2 | — |
| Q5 | answer | answer | **correct** | STW-PED-03 v2024.1 | — |
| Q6 | answer | answer | **correct** | STW-ORT-01 v2023.1 | — |
| Q7 | answer | answer | **correct** | STW-GYN-02 v2023.1 | — |
| Q8 | answer | answer | **correct** | STW-GP-03 v2024.1 | — |
| Q9 | abstain | abstain | **correct** | — | — |
| Q10 | abstain | abstain | **correct** | — | — |
| Q11 | answer | answer | **correct** | SOP-CLIN-014 v2.1 | — |

## Answers (claim texts, verbatim from cited units)

### Q1 — What is the first-line antibiotic, dose basis, and duration for acute otitis media in a child?

- Pain: Paracetamol 15 mg/kg per dose every 6 h as needed  
  ↳ *NATIONAL STW STW-PED-01 v2024.1 (effective 2024-05-01) — Acute Otitis Media — Child OPD* — STW-PED-01 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)
- Amoxicillin 40 mg/kg/day in three divided doses for 5 days  
  ↳ *NATIONAL STW STW-PED-01 v2024.1 (effective 2024-05-01) — Acute Otitis Media — Child OPD* — STW-PED-01 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- Severe or <6 months: Amoxicillin–Clavulanate 40 mg/kg/day (amoxicillin component)  
  ↳ *NATIONAL STW STW-PED-01 v2024.1 (effective 2024-05-01) — Acute Otitis Media — Child OPD* — STW-PED-01 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- _note: Dose text is quoted exactly as written in the source. No dose has been calculated for any patient; mg/kg figures are not converted._

### Q2 — A 6-year-old with non-severe community pneumonia: what is the amoxicillin dose exactly as the workflow states it? (Dose question — retrieve and cite the text as written; do not compute for any specific child.)

- Fever: Paracetamol 15 mg/kg per dose every 6 h as needed  
  ↳ *NATIONAL STW STW-PED-02 v2023.2 (effective 2023-11-01) — Community Pneumonia — Child OPD (Non-severe)* — STW-PED-02 v2023.2, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)
- Amoxicillin 40 mg/kg/day in three divided doses for 5 days  
  ↳ *NATIONAL STW STW-PED-02 v2023.2 (effective 2023-11-01) — Community Pneumonia — Child OPD (Non-severe)* — STW-PED-02 v2023.2, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- _note: Dose text is quoted exactly as written in the source. No dose has been calculated for any patient; mg/kg figures are not converted._

### Q3 — What is the first-line initial drug therapy for newly diagnosed adult hypertension? (Note: the pack may contain more than one edition of this workflow.)

- Uncontrolled at 4 weeks: combine Amlodipine + Telmisartan  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, FIRST-LINE MANAGEMENT (CURRENT), p1 (p1/first_line_management_current/4)
- Add Hydrochlorothiazide 12.5 mg if still uncontrolled  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, FIRST-LINE MANAGEMENT (CURRENT), p1 (p1/first_line_management_current/5)
- Start Amlodipine 5 mg once daily OR Telmisartan 40 mg once daily  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, FIRST-LINE MANAGEMENT (CURRENT), p1 (p1/first_line_management_current/3)
- Resistant HTN on 3 drugs; suspected secondary cause; pregnancy  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, REFER, p1 (p1/refer/7)
- Baseline: creatinine, potassium, lipids, ECG, urine albumin  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, CONFIRM, p1 (p1/confirm/2)
- _archived edition (not merged):_ Start Atenolol 50 mg once daily as initial monotherapy — STW-GP-02 v2021.1 (superseded by STW-GP-02 v2025.2)
- _archived edition (not merged):_ Alternative: Hydrochlorothiazide 25 mg once daily — STW-GP-02 v2021.1 (superseded by STW-GP-02 v2025.2)
- _archived edition (not merged):_ Review at 6 weeks — STW-GP-02 v2021.1 (superseded by STW-GP-02 v2025.2)

### Q4 — Which analgesic class must be avoided in suspected dengue, and why?

- AVOID Ibuprofen, Diclofenac, Aspirin and all NSAIDs — bleeding risk  
  ↳ *NATIONAL STW STW-GP-04 v2024.2 (effective 2024-07-01) — Dengue Fever — OPD Management* — STW-GP-04 v2024.2, OPD MANAGEMENT, p1 (p1/opd_management/5)
- Fever + two of: headache, retro-orbital pain, myalgia, rash, leukopenia  
  ↳ *NATIONAL STW STW-GP-04 v2024.2 (effective 2024-07-01) — Dengue Fever — OPD Management* — STW-GP-04 v2024.2, SUSPECT, p1 (p1/suspect/1)

### Q5 — What are the ORS volumes after each loose stool for a child aged 2–10 years, and what zinc course accompanies it?

- ORS after every loose stool: 50–100 ml (<2 y), 100–200 ml (2–10 y)  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- Zinc 20 mg once daily for 14 days (10 mg if <6 months)  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)

### Q6 — Which red flags in acute low back pain mandate imaging or referral?

- Fever with spinal tenderness; significant trauma; age >65 with new pain + weight loss  
  ↳ *NATIONAL STW STW-ORT-01 v2023.1 (effective 2023-09-01) — Acute Low Back Pain — Adult OPD* — STW-ORT-01 v2023.1, RED FLAGS — IMAGE/REFER, p1 (p1/red_flags_image_refer/2)
- Saddle anaesthesia, bladder/bowel involvement, progressive weakness  
  ↳ *NATIONAL STW STW-ORT-01 v2023.1 (effective 2023-09-01) — Acute Low Back Pain — Adult OPD* — STW-ORT-01 v2023.1, RED FLAGS — IMAGE/REFER, p1 (p1/red_flags_image_refer/1)
- Reassess at 2 weeks; persistent >6 weeks = imaging pathway  
  ↳ *NATIONAL STW STW-ORT-01 v2023.1 (effective 2023-09-01) — Acute Low Back Pain — Adult OPD* — STW-ORT-01 v2023.1, REVIEW, p1 (p1/review/6)

### Q7 — Which urinary antibiotic is avoided at 36+ weeks of pregnancy, and what is the stated alternative?

- Nitrofurantoin near term (36+ weeks)  
  ↳ *NATIONAL STW STW-GYN-02 v2023.1 (effective 2023-06-01) — Urinary Tract Infection in Pregnancy* — STW-GYN-02 v2023.1, AVOID, p1 (p1/avoid/6)
- Nitrofurantoin 100 mg twice daily for 5 days (avoid at 36+ weeks)  
  ↳ *NATIONAL STW STW-GYN-02 v2023.1 (effective 2023-06-01) — Urinary Tract Infection in Pregnancy* — STW-GYN-02 v2023.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- Ciprofloxacin and other fluoroquinolones throughout pregnancy  
  ↳ *NATIONAL STW STW-GYN-02 v2023.1 (effective 2023-06-01) — Urinary Tract Infection in Pregnancy* — STW-GYN-02 v2023.1, AVOID, p1 (p1/avoid/5)
- Alternative: Cefixime 200 mg twice daily for 5 days  
  ↳ *NATIONAL STW STW-GYN-02 v2023.1 (effective 2023-06-01) — Urinary Tract Infection in Pregnancy* — STW-GYN-02 v2023.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- Dysuria/frequency; urine routine + culture before antibiotics where possible  
  ↳ *NATIONAL STW STW-GYN-02 v2023.1 (effective 2023-06-01) — Urinary Tract Infection in Pregnancy* — STW-GYN-02 v2023.1, ASSESS, p1 (p1/assess/1)

### Q8 — At what HbA1c threshold at diagnosis does the workflow add a second agent to metformin, and which agent?

- HbA1c ≥8.5% at diagnosis: add Glimepiride 1 mg before breakfast  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- HbA1c every 3 months until at goal; annual creatinine and urine albumin  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, MONITOR, p1 (p1/monitor/5)
- Metformin 500 mg once daily with dinner; up-titrate weekly to 500 mg twice daily as tolerated  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- FPG ≥126 mg/dL or HbA1c ≥6.5% on two occasions, or RPG ≥200 with symptoms  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, DIAGNOSE, p1 (p1/diagnose/1)

### Q9 — What is the first-line prophylactic drug for migraine in adults?

**ABSTAIN:** the provided corpus has no workflow for migraine. Missing: a national STW page or clinic protocol covering migraine

### Q10 — What is the standard drug regimen for newly diagnosed pulmonary tuberculosis?

**ABSTAIN:** the provided corpus has no workflow for pulmonary_tuberculosis. Missing: a national STW page or clinic protocol covering pulmonary_tuberculosis

### Q11 — Per the clinic's own protocol, when are empirical antibiotics started in adult acute undifferentiated fever — and does the national workflow pack say the same? Label your sources.

- Day 2: if fever persists beyond 48 hours without a localizing source, start empirical Azithromycin 500 mg once daily for 3 days.  
  ↳ *CLINIC PROTOCOL (Sunrise Multi-speciality Clinic, SOP-CLIN-014 v2.1, approved 2026-03-10) — organization-level knowledge, not national guidance* — SOP-CLIN-014 v2.1, Protocol step 2, p1 (p1/step/2)
- Documentation: record fever chart and medication reconciliation at each visit.  
  ↳ *CLINIC PROTOCOL (Sunrise Multi-speciality Clinic, SOP-CLIN-014 v2.1, approved 2026-03-10) — organization-level knowledge, not national guidance* — SOP-CLIN-014 v2.1, Protocol step 4, p1 (p1/step/4)
- Day 0–1: Paracetamol per standard reference dosing; hydration advice; CBC + peripheral smear if fever > 48h; dengue NS1 in season.  
  ↳ *CLINIC PROTOCOL (Sunrise Multi-speciality Clinic, SOP-CLIN-014 v2.1, approved 2026-03-10) — organization-level knowledge, not national guidance* — SOP-CLIN-014 v2.1, Protocol step 1, p1 (p1/step/1)
- Day 3–4: review with reports; escalate per findings; admit if warning signs.  
  ↳ *CLINIC PROTOCOL (Sunrise Multi-speciality Clinic, SOP-CLIN-014 v2.1, approved 2026-03-10) — organization-level knowledge, not national guidance* — SOP-CLIN-014 v2.1, Protocol step 3, p1 (p1/step/3)
- _national comparison:_ The provided national STW pack contains no workflow for acute undifferentiated fever adult. It therefore neither confirms nor contradicts the clinic protocol; the clinic protocol stands as organization-level guidance only.

