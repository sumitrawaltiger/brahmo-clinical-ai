# Paraphrase eval results (extractive mode)

index: `rag-index-1.0:chunker-1.0.0:local-hashed-char-ngram-v1:f311f98775e8da86`

**35 correct · 0 abstained · 0 wrong** (held-out-style total 26; uncited numbers: 0)

| id | expected | got | verdict | cited | checks |
|---|---|---|---|---|---|
| P01 | answer | answer | **correct** | STW-GP-01 v2025.1 | — |
| P02 | answer | answer | **correct** | STW-GP-01 v2025.1 | — |
| P03 | answer | answer | **correct** | STW-GP-01 v2025.1 | — |
| P04 | answer | answer | **correct** | STW-GP-02 v2025.2 | — |
| P05 | answer | answer | **correct** | STW-GP-02 v2025.2 | — |
| P06 | answer | answer | **correct** | STW-GP-02 v2025.2 | — |
| P07 | answer | answer | **correct** | STW-GP-02 v2025.2 | — |
| P08 | answer | answer | **correct** | STW-GP-03 v2024.1 | — |
| P09 | answer | answer | **correct** | STW-GP-03 v2024.1 | — |
| P10 | answer | answer | **correct** | STW-GP-04 v2024.2 | — |
| P11 | answer | answer | **correct** | STW-GP-04 v2024.2 | — |
| P12 | answer | answer | **correct** | STW-GYN-01 v2024.1 | — |
| P13 | answer | answer | **correct** | STW-GYN-02 v2023.1 | — |
| P14 | answer | answer | **correct** | STW-GYN-03 v2024.1, STW-GP-03 v2024.1 | — |
| P15 | answer | answer | **correct** | STW-ORT-01 v2023.1 | — |
| P16 | answer | answer | **correct** | STW-ORT-02 v2024.1 | — |
| P17 | answer | answer | **correct** | STW-PED-01 v2024.1 | — |
| P18 | answer | answer | **correct** | STW-PED-01 v2024.1 | — |
| P19 | answer | answer | **correct** | STW-PED-02 v2023.2 | — |
| P20 | answer | answer | **correct** | STW-PED-03 v2024.1 | — |
| P21 | answer | answer | **correct** | STW-PED-03 v2024.1 | — |
| P22 | answer | answer | **correct** | STW-PED-03 v2024.1 | — |
| P23 | answer | answer | **correct** | SOP-CLIN-014 v2.1 | — |
| P24 | abstain | abstain | **correct** | — | — |
| P25 | abstain | abstain | **correct** | — | — |
| P26 | abstain | abstain | **correct** | — | — |
| P27 | abstain | abstain | **correct** | — | — |
| P28 | abstain | abstain | **correct** | — | — |
| P29 | abstain | abstain | **correct** | — | — |
| P30 | abstain | abstain | **correct** | — | — |
| P31 | abstain | abstain | **correct** | — | — |
| P32 | answer | answer | **correct** | CDCI subset vn/a, GSR 411(E) vn/a | — |
| P33 | answer | answer | **correct** | CDCI subset vn/a, gazette extract vn/a | — |
| P34 | answer | answer | **correct** | CDCI subset vn/a, gazette extract vn/a | — |
| P35 | abstain | abstain | **correct** | — | — |

## Answers (claim texts, verbatim from cited units)

### P01 — Adult with sore throat and fever, Centor 3 — which antibiotic and for how long?

- Sore throat, fever; examine tonsils, cervical nodes  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, ASSESS, p1 (p1/assess/1)
- Do not use antibiotics for clearly viral sore throat  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, DO NOT, p1 (p1/do_not/8)
- Centor criteria ≥3 suggests streptococcal cause  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, ASSESS, p1 (p1/assess/2)
- Symptomatic: Paracetamol 500–650 mg every 6–8 h as needed (max 3 g/day adult)  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/5)
- Avoid routine throat swab in low-risk presentation  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, DO NOT, p1 (p1/do_not/9)
- Penicillin allergy: Azithromycin 500 mg once daily for 3 days  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/7)
- If streptococcal likely: Amoxicillin 500 mg three times daily for 5 days  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/6)

### P02 — Penicillin-allergic adult with streptococcal pharyngitis: what does the workflow say to use?

- Centor criteria ≥3 suggests streptococcal cause  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, ASSESS, p1 (p1/assess/2)
- Do not use antibiotics for clearly viral sore throat  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, DO NOT, p1 (p1/do_not/8)
- Penicillin allergy: Azithromycin 500 mg once daily for 3 days  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/7)
- If streptococcal likely: Amoxicillin 500 mg three times daily for 5 days  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/6)
- Symptomatic: Paracetamol 500–650 mg every 6–8 h as needed (max 3 g/day adult)  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/5)

### P03 — Should antibiotics be given for a clearly viral sore throat?

- Do not use antibiotics for clearly viral sore throat  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, DO NOT, p1 (p1/do_not/8)
- Sore throat, fever; examine tonsils, cervical nodes  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, ASSESS, p1 (p1/assess/1)
- Avoid routine throat swab in low-risk presentation  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, DO NOT, p1 (p1/do_not/9)
- Symptomatic: Paracetamol 500–650 mg every 6–8 h as needed (max 3 g/day adult)  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/5)
- If streptococcal likely: Amoxicillin 500 mg three times daily for 5 days  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/6)
- Penicillin allergy: Azithromycin 500 mg once daily for 3 days  
  ↳ *NATIONAL STW STW-GP-01 v2025.1 (effective 2025-04-01) — Acute Pharyngitis — Adult OPD* — STW-GP-01 v2025.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/7)

### P04 — High blood pressure newly found in a 50-year-old: what do I start?

- Start Amlodipine 5 mg once daily OR Telmisartan 40 mg once daily  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, FIRST-LINE MANAGEMENT (CURRENT), p1 (p1/first_line_management_current/3)
- Uncontrolled at 4 weeks: combine Amlodipine + Telmisartan  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, FIRST-LINE MANAGEMENT (CURRENT), p1 (p1/first_line_management_current/4)
- Add Hydrochlorothiazide 12.5 mg if still uncontrolled  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, FIRST-LINE MANAGEMENT (CURRENT), p1 (p1/first_line_management_current/5)
- _note: Dose text is quoted exactly as written in the source. No dose has been calculated for any patient; mg/kg figures are not converted._
- _archived edition (not merged):_ Start Atenolol 50 mg once daily as initial monotherapy — STW-GP-02 v2021.1 (superseded by STW-GP-02 v2025.2)

### P05 — Is atenolol still the first-line antihypertensive?

- Add Hydrochlorothiazide 12.5 mg if still uncontrolled  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, FIRST-LINE MANAGEMENT (CURRENT), p1 (p1/first_line_management_current/5)
- Uncontrolled at 4 weeks: combine Amlodipine + Telmisartan  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, FIRST-LINE MANAGEMENT (CURRENT), p1 (p1/first_line_management_current/4)
- Start Amlodipine 5 mg once daily OR Telmisartan 40 mg once daily  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, FIRST-LINE MANAGEMENT (CURRENT), p1 (p1/first_line_management_current/3)
- _archived edition (not merged):_ Start Atenolol 50 mg once daily as initial monotherapy — STW-GP-02 v2021.1 (superseded by STW-GP-02 v2025.2)
- _archived edition (not merged):_ Alternative: Hydrochlorothiazide 25 mg once daily — STW-GP-02 v2021.1 (superseded by STW-GP-02 v2025.2)
- _archived edition (not merged):_ Review at 6 weeks — STW-GP-02 v2021.1 (superseded by STW-GP-02 v2025.2)

### P06 — What BP target applies to a hypertensive patient with diabetes?

- <140/90 general; <130/80 if diabetes or CKD (individualize)  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, TARGETS, p1 (p1/targets/6)

### P07 — When should I refer a hypertensive patient?

- Resistant HTN on 3 drugs; suspected secondary cause; pregnancy  
  ↳ *NATIONAL STW STW-GP-02 v2025.2 (effective 2025-06-01) — Hypertension — Initial Management (Adult)* — STW-GP-02 v2025.2, REFER, p1 (p1/refer/7)

### P08 — How is type 2 diabetes diagnosed per the workflow?

- Type 1 suspicion, pregnancy, eGFR <30, recurrent hypoglycemia  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, REFER, p1 (p1/refer/6)
- FPG ≥126 mg/dL or HbA1c ≥6.5% on two occasions, or RPG ≥200 with symptoms  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, DIAGNOSE, p1 (p1/diagnose/1)

### P09 — How often should HbA1c be repeated after starting metformin?

- HbA1c every 3 months until at goal; annual creatinine and urine albumin  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, MONITOR, p1 (p1/monitor/5)
- HbA1c ≥8.5% at diagnosis: add Glimepiride 1 mg before breakfast  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- FPG ≥126 mg/dL or HbA1c ≥6.5% on two occasions, or RPG ≥200 with symptoms  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, DIAGNOSE, p1 (p1/diagnose/1)
- Metformin 500 mg once daily with dinner; up-titrate weekly to 500 mg twice daily as tolerated  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- Lifestyle counselling at every visit  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)

### P10 — Can I give ibuprofen for fever in suspected dengue?

- Fever + two of: headache, retro-orbital pain, myalgia, rash, leukopenia  
  ↳ *NATIONAL STW STW-GP-04 v2024.2 (effective 2024-07-01) — Dengue Fever — OPD Management* — STW-GP-04 v2024.2, SUSPECT, p1 (p1/suspect/1)
- AVOID Ibuprofen, Diclofenac, Aspirin and all NSAIDs — bleeding risk  
  ↳ *NATIONAL STW STW-GP-04 v2024.2 (effective 2024-07-01) — Dengue Fever — OPD Management* — STW-GP-04 v2024.2, OPD MANAGEMENT, p1 (p1/opd_management/5)
- Paracetamol 500–650 mg every 6 h for fever (max 3 g/day); adequate oral fluids  
  ↳ *NATIONAL STW STW-GP-04 v2024.2 (effective 2024-07-01) — Dengue Fever — OPD Management* — STW-GP-04 v2024.2, OPD MANAGEMENT, p1 (p1/opd_management/4)
- Daily CBC from day 3 of illness  
  ↳ *NATIONAL STW STW-GP-04 v2024.2 (effective 2024-07-01) — Dengue Fever — OPD Management* — STW-GP-04 v2024.2, OPD MANAGEMENT, p1 (p1/opd_management/6)

### P11 — Which dengue warning signs mean the patient must be admitted?

- Persistent vomiting, abdominal pain, mucosal bleed  
  ↳ *NATIONAL STW STW-GP-04 v2024.2 (effective 2024-07-01) — Dengue Fever — OPD Management* — STW-GP-04 v2024.2, WARNING SIGNS — ADMIT, p1 (p1/warning_signs_admit/2)
- Lethargy, hepatomegaly, rising haematocrit with falling platelets  
  ↳ *NATIONAL STW STW-GP-04 v2024.2 (effective 2024-07-01) — Dengue Fever — OPD Management* — STW-GP-04 v2024.2, WARNING SIGNS — ADMIT, p1 (p1/warning_signs_admit/3)
- Immediate return if any warning sign appears  
  ↳ *NATIONAL STW STW-GP-04 v2024.2 (effective 2024-07-01) — Dengue Fever — OPD Management* — STW-GP-04 v2024.2, FOLLOW-UP, p1 (p1/follow_up/7)
- Fever + two of: headache, retro-orbital pain, myalgia, rash, leukopenia  
  ↳ *NATIONAL STW STW-GP-04 v2024.2 (effective 2024-07-01) — Dengue Fever — OPD Management* — STW-GP-04 v2024.2, SUSPECT, p1 (p1/suspect/1)

### P12 — Hb cut-off for anaemia in pregnancy and the iron regimen?

- Mild–moderate: Ferrous Ascorbate 100 mg elemental iron once daily + Folic Acid 500 mcg daily  
  ↳ *NATIONAL STW STW-GYN-01 v2024.1 (effective 2024-08-01) — Iron Deficiency Anemia in Pregnancy* — STW-GYN-01 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- Continue 3 months after Hb normalises  
  ↳ *NATIONAL STW STW-GYN-01 v2024.1 (effective 2024-08-01) — Iron Deficiency Anemia in Pregnancy* — STW-GYN-01 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- Hb at booking, 26–28 weeks, and 34 weeks; anemia if Hb <11 g/dL  
  ↳ *NATIONAL STW STW-GYN-01 v2024.1 (effective 2024-08-01) — Iron Deficiency Anemia in Pregnancy* — STW-GYN-01 v2024.1, SCREEN, p1 (p1/screen/1)
- Take iron away from tea/calcium; expect dark stools  
  ↳ *NATIONAL STW STW-GYN-01 v2024.1 (effective 2024-08-01) — Iron Deficiency Anemia in Pregnancy* — STW-GYN-01 v2024.1, COUNSEL, p1 (p1/counsel/5)
- Hb <7 g/dL or beyond 34 weeks with moderate anemia: REFER (parenteral pathway)  
  ↳ *NATIONAL STW STW-GYN-01 v2024.1 (effective 2024-08-01) — Iron Deficiency Anemia in Pregnancy* — STW-GYN-01 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)
- _note: Dose text is quoted exactly as written in the source. No dose has been calculated for any patient; mg/kg figures are not converted._

### P13 — Can ciprofloxacin be used for a urine infection in a pregnant woman?

- Ciprofloxacin and other fluoroquinolones throughout pregnancy  
  ↳ *NATIONAL STW STW-GYN-02 v2023.1 (effective 2023-06-01) — Urinary Tract Infection in Pregnancy* — STW-GYN-02 v2023.1, AVOID, p1 (p1/avoid/5)
- Dysuria/frequency; urine routine + culture before antibiotics where possible  
  ↳ *NATIONAL STW STW-GYN-02 v2023.1 (effective 2023-06-01) — Urinary Tract Infection in Pregnancy* — STW-GYN-02 v2023.1, ASSESS, p1 (p1/assess/1)
- Nitrofurantoin 100 mg twice daily for 5 days (avoid at 36+ weeks)  
  ↳ *NATIONAL STW STW-GYN-02 v2023.1 (effective 2023-06-01) — Urinary Tract Infection in Pregnancy* — STW-GYN-02 v2023.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- Alternative: Cefixime 200 mg twice daily for 5 days  
  ↳ *NATIONAL STW STW-GYN-02 v2023.1 (effective 2023-06-01) — Urinary Tract Infection in Pregnancy* — STW-GYN-02 v2023.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- Repeat culture after treatment (test of cure)  
  ↳ *NATIONAL STW STW-GYN-02 v2023.1 (effective 2023-06-01) — Urinary Tract Infection in Pregnancy* — STW-GYN-02 v2023.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)

### P14 — Metformin in PCOS — when and how much per the workflow?

- Metformin 500 mg twice daily when metabolic indication present  
  ↳ *NATIONAL STW STW-GYN-03 v2024.1 (effective 2024-10-01) — PCOS — Initial OPD Approach* — STW-GYN-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)
- Metformin 500 mg once daily with dinner; up-titrate weekly to 500 mg twice daily as tolerated  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- HbA1c ≥8.5% at diagnosis: add Glimepiride 1 mg before breakfast  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- Lifestyle counselling at every visit  
  ↳ *NATIONAL STW STW-GP-03 v2024.1 (effective 2024-09-01) — Type 2 Diabetes — Diagnosis & Initiation* — STW-GP-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)
- Lifestyle: 5–10% weight reduction target as primary therapy  
  ↳ *NATIONAL STW STW-GYN-03 v2024.1 (effective 2024-10-01) — PCOS — Initial OPD Approach* — STW-GYN-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- Cycle regulation where needed per specialist pathway  
  ↳ *NATIONAL STW STW-GYN-03 v2024.1 (effective 2024-10-01) — PCOS — Initial OPD Approach* — STW-GYN-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- _note: Dose text is quoted exactly as written in the source. No dose has been calculated for any patient; mg/kg figures are not converted._

### P15 — Backache for 3 days in an adult, no red flags: analgesic options as written?

- Saddle anaesthesia, bladder/bowel involvement, progressive weakness  
  ↳ *NATIONAL STW STW-ORT-01 v2023.1 (effective 2023-09-01) — Acute Low Back Pain — Adult OPD* — STW-ORT-01 v2023.1, RED FLAGS — IMAGE/REFER, p1 (p1/red_flags_image_refer/1)
- Fever with spinal tenderness; significant trauma; age >65 with new pain + weight loss  
  ↳ *NATIONAL STW STW-ORT-01 v2023.1 (effective 2023-09-01) — Acute Low Back Pain — Adult OPD* — STW-ORT-01 v2023.1, RED FLAGS — IMAGE/REFER, p1 (p1/red_flags_image_refer/2)
- Stay active; avoid bed rest beyond 48 h  
  ↳ *NATIONAL STW STW-ORT-01 v2023.1 (effective 2023-09-01) — Acute Low Back Pain — Adult OPD* — STW-ORT-01 v2023.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- Paracetamol 650 mg every 8 h OR Ibuprofen 400 mg every 8 h after food (short course)  
  ↳ *NATIONAL STW STW-ORT-01 v2023.1 (effective 2023-09-01) — Acute Low Back Pain — Adult OPD* — STW-ORT-01 v2023.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)
- Muscle spasm: consider short course only per local formulary  
  ↳ *NATIONAL STW STW-ORT-01 v2023.1 (effective 2023-09-01) — Acute Low Back Pain — Adult OPD* — STW-ORT-01 v2023.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/5)

### P16 — When does knee osteoarthritis need referral?

- Night pain with locking; deformity; failure of 3-month conservative care  
  ↳ *NATIONAL STW STW-ORT-02 v2024.1 (effective 2024-04-01) — Knee Osteoarthritis — OPD* — STW-ORT-02 v2024.1, REFER, p1 (p1/refer/5)

### P17 — Earache with a red bulging eardrum in a 4-year-old: antibiotic as the page states it

- Ear pain, fever, red bulging tympanic membrane on otoscopy  
  ↳ *NATIONAL STW STW-PED-01 v2024.1 (effective 2024-05-01) — Acute Otitis Media — Child OPD* — STW-PED-01 v2024.1, ASSESS, p1 (p1/assess/1)
- Mastoid tenderness, facial palsy, failure after 48–72 h of antibiotics  
  ↳ *NATIONAL STW STW-PED-01 v2024.1 (effective 2024-05-01) — Acute Otitis Media — Child OPD* — STW-PED-01 v2024.1, REFER, p1 (p1/refer/5)
- Amoxicillin 40 mg/kg/day in three divided doses for 5 days  
  ↳ *NATIONAL STW STW-PED-01 v2024.1 (effective 2024-05-01) — Acute Otitis Media — Child OPD* — STW-PED-01 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- Severe or <6 months: Amoxicillin–Clavulanate 40 mg/kg/day (amoxicillin component)  
  ↳ *NATIONAL STW STW-PED-01 v2024.1 (effective 2024-05-01) — Acute Otitis Media — Child OPD* — STW-PED-01 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- Pain: Paracetamol 15 mg/kg per dose every 6 h as needed  
  ↳ *NATIONAL STW STW-PED-01 v2024.1 (effective 2024-05-01) — Acute Otitis Media — Child OPD* — STW-PED-01 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)
- _note: Dose text is quoted exactly as written in the source. No dose has been calculated for any patient; mg/kg figures are not converted._

### P18 — How many mg of amoxicillin should a 15 kg child with otitis media get per dose?

- Pain: Paracetamol 15 mg/kg per dose every 6 h as needed  
  ↳ *NATIONAL STW STW-PED-01 v2024.1 (effective 2024-05-01) — Acute Otitis Media — Child OPD* — STW-PED-01 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)
- Severe or <6 months: Amoxicillin–Clavulanate 40 mg/kg/day (amoxicillin component)  
  ↳ *NATIONAL STW STW-PED-01 v2024.1 (effective 2024-05-01) — Acute Otitis Media — Child OPD* — STW-PED-01 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- Amoxicillin 40 mg/kg/day in three divided doses for 5 days  
  ↳ *NATIONAL STW STW-PED-01 v2024.1 (effective 2024-05-01) — Acute Otitis Media — Child OPD* — STW-PED-01 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- _note: Dose text is quoted exactly as written in the source. No dose has been calculated for any patient; mg/kg figures are not converted._

### P19 — Is a cough syrup OK for a 3-year-old with non-severe pneumonia?

- No cough syrups under 5 years; no routine chest X-ray in OPD non-severe cases  
  ↳ *NATIONAL STW STW-PED-02 v2023.2 (effective 2023-11-01) — Community Pneumonia — Child OPD (Non-severe)* — STW-PED-02 v2023.2, DO NOT, p1 (p1/do_not/6)
- Fast breathing for age without danger signs = non-severe pneumonia  
  ↳ *NATIONAL STW STW-PED-02 v2023.2 (effective 2023-11-01) — Community Pneumonia — Child OPD (Non-severe)* — STW-PED-02 v2023.2, CLASSIFY, p1 (p1/classify/1)
- _note: Dose text is quoted exactly as written in the source. No dose has been calculated for any patient; mg/kg figures are not converted._

### P20 — Loose motions in a 1-year-old: how much ORS after each stool?

- ORS after every loose stool: 50–100 ml (<2 y), 100–200 ml (2–10 y)  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- Zinc 20 mg once daily for 14 days (10 mg if <6 months)  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- Continue feeding; ondansetron 0.15 mg/kg single dose only for persistent vomiting  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)
- _note: Dose text is quoted exactly as written in the source. No dose has been calculated for any patient; mg/kg figures are not converted._

### P21 — Zinc for a 4-month-old with diarrhoea — what does the page say?

- Zinc 20 mg once daily for 14 days (10 mg if <6 months)  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- ORS after every loose stool: 50–100 ml (<2 y), 100–200 ml (2–10 y)  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- Continue feeding; ondansetron 0.15 mg/kg single dose only for persistent vomiting  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)
- _note: Dose text is quoted exactly as written in the source. No dose has been calculated for any patient; mg/kg figures are not converted._

### P22 — Should I give loperamide to a child with gastroenteritis?

- No/ some/ severe dehydration per standard signs; severe = REFER for IV  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, ASSESS DEHYDRATION, p1 (p1/assess_dehydration/1)
- ORS after every loose stool: 50–100 ml (<2 y), 100–200 ml (2–10 y)  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/2)
- Zinc 20 mg once daily for 14 days (10 mg if <6 months)  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/3)
- Continue feeding; ondansetron 0.15 mg/kg single dose only for persistent vomiting  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, FIRST-LINE MANAGEMENT, p1 (p1/first_line_management/4)
- No routine antibiotics; no antimotility agents in children  
  ↳ *NATIONAL STW STW-PED-03 v2024.1 (effective 2024-03-01) — Acute Gastroenteritis — Child OPD* — STW-PED-03 v2024.1, DO NOT, p1 (p1/do_not/5)

### P23 — What does the clinic's own fever protocol say to do on day 3 and 4?

- Day 3–4: review with reports; escalate per findings; admit if warning signs.  
  ↳ *CLINIC PROTOCOL (Sunrise Multi-speciality Clinic, SOP-CLIN-014 v2.1, approved 2026-03-10) — organization-level knowledge, not national guidance* — SOP-CLIN-014 v2.1, Protocol step 3, p1 (p1/step/3)
- Day 2: if fever persists beyond 48 hours without a localizing source, start empirical Azithromycin 500 mg once daily for 3 days.  
  ↳ *CLINIC PROTOCOL (Sunrise Multi-speciality Clinic, SOP-CLIN-014 v2.1, approved 2026-03-10) — organization-level knowledge, not national guidance* — SOP-CLIN-014 v2.1, Protocol step 2, p1 (p1/step/2)
- Documentation: record fever chart and medication reconciliation at each visit.  
  ↳ *CLINIC PROTOCOL (Sunrise Multi-speciality Clinic, SOP-CLIN-014 v2.1, approved 2026-03-10) — organization-level knowledge, not national guidance* — SOP-CLIN-014 v2.1, Protocol step 4, p1 (p1/step/4)
- Day 0–1: Paracetamol per standard reference dosing; hydration advice; CBC + peripheral smear if fever > 48h; dengue NS1 in season.  
  ↳ *CLINIC PROTOCOL (Sunrise Multi-speciality Clinic, SOP-CLIN-014 v2.1, approved 2026-03-10) — organization-level knowledge, not national guidance* — SOP-CLIN-014 v2.1, Protocol step 1, p1 (p1/step/1)
- _national comparison:_ The provided national STW pack contains no workflow for acute undifferentiated fever adult. It therefore neither confirms nor contradicts the clinic protocol; the clinic protocol stands as organization-level guidance only.

### P24 — What is the first-line treatment for malaria?

**ABSTAIN:** the provided corpus has no workflow for malaria. Missing: a national STW page or clinic protocol covering malaria

### P25 — Which antibiotic for enteric fever (typhoid)?

**ABSTAIN:** the provided corpus has no workflow for typhoid. Missing: a national STW page or clinic protocol covering typhoid

### P26 — What inhaler should I start for asthma?

**ABSTAIN:** the provided corpus has no workflow for asthma. Missing: a national STW page or clinic protocol covering asthma

### P27 — First-line antiepileptic for a new seizure disorder?

**ABSTAIN:** the provided corpus has no workflow for epilepsy. Missing: a national STW page or clinic protocol covering epilepsy

### P28 — Which SSRI is preferred for depression in adults?

**ABSTAIN:** the provided corpus has no workflow for depression. Missing: a national STW page or clinic protocol covering depression

### P29 — What is the routine treatment for COPD exacerbation?

**ABSTAIN:** the provided corpus has no workflow for copd. Missing: a national STW page or clinic protocol covering copd

### P30 — What are the risk factors for typhoid fever?

**ABSTAIN:** the provided corpus has no workflow for typhoid. Missing: a national STW page or clinic protocol covering typhoid

### P31 — Does the workflow pack cover hypothyroidism?

**ABSTAIN:** the provided corpus has no workflow for hypothyroidism. Missing: a national STW page or clinic protocol covering hypothyroidism

### P32 — Is NimuPar-P banned in India?

- NimuPar-P (Tablet) = Nimesulide 100 mg + Paracetamol 325 mg  
  ↳ *DRUG MASTER (structured fact)* — CDCI subset vNone, None, pNone (None)
- Status PROHIBITED as of 2026-10-14: GSR 411(E) (PROHIBITED), published 2023-06-02, effective 2023-06-15 — target: Nimesulide + Paracetamol (all strengths)  
  ↳ *REGULATORY REGISTER (event-sourced)* — GSR 411(E) vNone, None, pNone (None)

### P33 — What does Sinarest Tablet contain?

- Sinarest Tablet (Tablet) = Paracetamol 500 mg + Chlorpheniramine 2 mg + Phenylephrine 10 mg  
  ↳ *DRUG MASTER (structured fact)* — CDCI subset vNone, None, pNone (None)
- No in-force PROHIBITED/RESTRICTED/WITHDRAWN event matches this product as of 2026-10-14 in the loaded register (extract through its latest published notification).  
  ↳ *REGULATORY REGISTER (event-sourced)* — gazette extract vNone, None, pNone (None)

### P34 — Is Combiflam prohibited?

- Combiflam (Tablet) = Ibuprofen 400 mg + Paracetamol 325 mg  
  ↳ *DRUG MASTER (structured fact)* — CDCI subset vNone, None, pNone (None)
- No in-force PROHIBITED/RESTRICTED/WITHDRAWN event matches this product as of 2026-10-14 in the loaded register (extract through its latest published notification).  
  ↳ *REGULATORY REGISTER (event-sourced)* — gazette extract vNone, None, pNone (None)

### P35 — Is Telma banned?

**ABSTAIN:** no brand in the question resolved unambiguously in the drug master. Missing: an exact brand (with strength) present in the CDCI subset

