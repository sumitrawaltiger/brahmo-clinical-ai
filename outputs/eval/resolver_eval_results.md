# Resolver eval — messy prescription spellings

**45 correct · 0 unknown (queued) · 0 wrong** of 45 (held-out-style total 45)

| id | written | strength | expected | got | method | conf | verdict | note |
|---|---|---|---|---|---|---|---|---|
| M01 | `Dolo 650` | 650 mg | RESOLVED CD1000 | RESOLVED CD1000 | exact_brand_strength | 0.97 | **correct** | canonical |
| M02 | `DOLO-650` | — | RESOLVED CD1000 | RESOLVED CD1000 | exact_brand_unique | 0.95 | **correct** | upper-case, hyphen |
| M03 | `Dolo 650mg` | — | RESOLVED CD1000 | RESOLVED CD1000 | exact_brand_strength | 0.97 | **correct** | glued strength |
| M04 | `Tab. Dolo 650` | — | RESOLVED CD1000 | RESOLVED CD1000 | exact_brand_form | 0.95 | **correct** | Tab. prefix |
| M05 | `T. Dolo 650` | — | RESOLVED CD1000 | RESOLVED CD1000 | exact_brand_form | 0.95 | **correct** | T. prefix |
| M06 | `Dolo` | — | RESOLVED CD1000 | RESOLVED CD1000 | brand_family_unique | 0.92 | **correct** | single-variant family in this master -> brand_family_unique (0.92) |
| M07 | `dolo 650 tab` | — | RESOLVED CD1000 | RESOLVED CD1000 | exact_brand_form | 0.95 | **correct** | trailing form |
| M08 | `Sinarest` | — | RESOLVED CD1021 | RESOLVED CD1021 | brand_family_unique | 0.92 | **correct** | master brand is 'Sinarest Tablet' |
| M09 | `Tab Sinarest` | — | RESOLVED CD1021 | RESOLVED CD1021 | brand_family_unique | 0.92 | **correct** |  |
| M10 | `SINAREST TABLET` | — | RESOLVED CD1021 | RESOLVED CD1021 | exact_brand_unique | 0.95 | **correct** |  |
| M11 | `Combiflam tab` | — | RESOLVED CD1026 | RESOLVED CD1026 | exact_brand_form | 0.95 | **correct** |  |
| M12 | `Augmentin 625` | — | RESOLVED CD1022 | RESOLVED CD1022 | brand_family_unique | 0.92 | **correct** | 'Augmentin 625 Duo' is the only Augmentin 625 |
| M13 | `Augmentin 625 Duo` | 625 mg | UNRESOLVED STRENGTH_MISMATCH | UNRESOLVED STRENGTH_MISMATCH | exact_brand | 0.00 | **correct** | 625 is the brand number, not a salt strength (500 + 125); never guessed |
| M14 | `Pan-D cap` | — | RESOLVED CD1023 | RESOLVED CD1023 | exact_brand_form | 0.95 | **correct** |  |
| M15 | `PAN D` | — | RESOLVED CD1023 | RESOLVED CD1023 | exact_brand_unique | 0.95 | **correct** |  |
| M16 | `Pan 40` | 40 mg | RESOLVED CD1014 | RESOLVED CD1014 | exact_brand_strength | 0.97 | **correct** |  |
| M17 | `Pan` | — | AMBIGUOUS AMBIGUOUS_STRENGTH_MISSING | AMBIGUOUS AMBIGUOUS_STRENGTH_MISSING | brand_family | 0.00 | **correct** | Pan 40 vs Pan-D |
| M18 | `Telma` | — | AMBIGUOUS AMBIGUOUS_STRENGTH_MISSING | AMBIGUOUS AMBIGUOUS_STRENGTH_MISSING | brand_family | 0.00 | **correct** | 20/40/80/-H 40 |
| M19 | `Telma` | 40 mg | AMBIGUOUS AMBIGUOUS_STRENGTH_MISSING | AMBIGUOUS AMBIGUOUS_STRENGTH_MISSING | brand_family | 0.00 | **correct** | Telma 40 and Telma-H 40 both carry telmisartan 40 mg |
| M20 | `Telma 40` | — | RESOLVED CD1010 | RESOLVED CD1010 | exact_brand_unique | 0.95 | **correct** |  |
| M21 | `Tab. Telma 40` | — | RESOLVED CD1010 | RESOLVED CD1010 | exact_brand_form | 0.95 | **correct** |  |
| M22 | `telma h 40` | — | RESOLVED CD1024 | RESOLVED CD1024 | exact_brand_unique | 0.95 | **correct** |  |
| M23 | `TELMA-H-40` | — | RESOLVED CD1024 | RESOLVED CD1024 | exact_brand_unique | 0.95 | **correct** |  |
| M24 | `Telma H` | — | RESOLVED CD1024 | RESOLVED CD1024 | brand_family_unique | 0.92 | **correct** | single-variant family |
| M25 | `Azee 500` | 500 mg | RESOLVED CD1007 | RESOLVED CD1007 | exact_brand_strength | 0.97 | **correct** |  |
| M26 | `T. Azee 500` | — | RESOLVED CD1007 | RESOLVED CD1007 | exact_brand_form | 0.95 | **correct** |  |
| M27 | `Inj Azee` | — | UNRESOLVED FORM_MISMATCH | UNRESOLVED FORM_MISMATCH | brand_family_unique | 0.00 | **correct** | master knows Azee only as a tablet; an injection is not silently a tablet |
| M28 | `Syp Calpol 250` | — | UNRESOLVED FORM_MISMATCH | UNRESOLVED FORM_MISMATCH | brand_family_unique | 0.00 | **correct** | master row is a Suspension; syrup != suspension (raised in Day-2 Q&A Q6) |
| M29 | `Calpol 250 Suspension` | — | RESOLVED CD1004 | RESOLVED CD1004 | exact_brand_unique | 0.95 | **correct** |  |
| M30 | `Calpol` | — | AMBIGUOUS AMBIGUOUS_STRENGTH_MISSING | AMBIGUOUS AMBIGUOUS_STRENGTH_MISSING | brand_family | 0.00 | **correct** | Calpol 650 vs Calpol 250 Suspension |
| M31 | `Crocin advance` | — | RESOLVED CD1020 | RESOLVED CD1020 | brand_family_unique | 0.92 | **correct** |  |
| M32 | `Crocin` | — | AMBIGUOUS AMBIGUOUS_STRENGTH_MISSING | AMBIGUOUS AMBIGUOUS_STRENGTH_MISSING | brand_family | 0.00 | **correct** | Crocin 650 vs Crocin Advance 500 |
| M33 | `Thyronorm 50mcg` | — | UNRESOLVED STRENGTH_MISMATCH | UNRESOLVED STRENGTH_MISMATCH | exact_brand | 0.00 | **correct** | mcg vs master mg (data anomaly B3) |
| M34 | `Thyronorm 50` | — | RESOLVED CD1019 | RESOLVED CD1019 | exact_brand_unique | 0.95 | **correct** | no unit written -> brand match only |
| M35 | `Glycomet 500` | 500mg | RESOLVED CD1013 | RESOLVED CD1013 | exact_brand_strength | 0.97 | **correct** | strength with no space |
| M36 | `Glycomet` | 1 tab | UNRESOLVED STRENGTH_UNPARSEABLE | UNRESOLVED STRENGTH_UNPARSEABLE | brand_family_unique | 0.00 | **correct** |  |
| M37 | `Zqtrixon Forte` | — | UNRESOLVED FUZZY_ONLY | UNRESOLVED FUZZY_ONLY | fuzzy_suggestion | 0.50 | **correct** |  |
| M38 | `Nimupar P` | — | RESOLVED CD1027 | RESOLVED CD1027 | exact_brand_unique | 0.95 | **correct** | hyphen dropped |
| M39 | `NIMUPAR-P TAB` | — | RESOLVED CD1027 | RESOLVED CD1027 | exact_brand_form | 0.95 | **correct** |  |
| M40 | `Zypan Forte` | — | AMBIGUOUS AMBIGUOUS_STRENGTH_MISSING | AMBIGUOUS AMBIGUOUS_STRENGTH_MISSING | exact_brand | 0.00 | **correct** | two unrelated compositions share the name (anomaly B1) |
| M41 | `Zypan Forte tab` | — | RESOLVED CD1034 | RESOLVED CD1034 | exact_brand_form | 0.95 | **correct** | form token disambiguates |
| M42 | `Ecosprin 75` | 75 mg | RESOLVED CD1016 | RESOLVED CD1016 | exact_brand_strength | 0.97 | **correct** |  |
| M43 | `Ecosprin` | — | RESOLVED CD1016 | RESOLVED CD1016 | brand_family_unique | 0.92 | **correct** | single-variant family |
| M44 | `` | — | UNRESOLVED UNKNOWN_BRAND | UNRESOLVED UNKNOWN_BRAND |  | 0.00 | **correct** | empty line |
| M45 | `Tab` | — | UNRESOLVED UNKNOWN_BRAND | UNRESOLVED UNKNOWN_BRAND | none | 0.00 | **correct** | form token only, no brand |
