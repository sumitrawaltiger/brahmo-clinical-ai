"""Review-queue reason codes. Every uncertain resolution carries exactly one of these."""

UNKNOWN_BRAND = "UNKNOWN_BRAND"                       # no drug-master brand matches the normalized text
AMBIGUOUS_BRAND_MULTI_COMPOSITION = "AMBIGUOUS_BRAND_MULTI_COMPOSITION"  # brand text matches >1 product with different compositions
AMBIGUOUS_STRENGTH_MISSING = "AMBIGUOUS_STRENGTH_MISSING"  # brand family found, strength needed to pick one SKU, none given
AMBIGUOUS_FORM_MISSING = "AMBIGUOUS_FORM_MISSING"      # brand+strength found in several dose forms, none given
FORM_MISMATCH = "FORM_MISMATCH"                        # billed form token contradicts every master row for that brand
STRENGTH_MISMATCH = "STRENGTH_MISMATCH"                # written strength matches no master row for that brand
STRENGTH_UNPARSEABLE = "STRENGTH_UNPARSEABLE"          # a strength was written but could not be read (e.g. '650mg/5ml', '1 tab'); never ignored
FUZZY_ONLY = "FUZZY_ONLY"                              # only near-miss candidates exist (possible typo); never auto-accepted
LLM_SUGGESTION_UNVERIFIED = "LLM_SUGGESTION_UNVERIFIED" # an LLM proposed a mapping that deterministic checks could not confirm
TARGET_PARSE_UNCERTAIN = "TARGET_PARSE_UNCERTAIN"      # regulatory target text has an unresolvable qualifier or unknown ingredient
SOURCE_ROW_INCONSISTENT = "SOURCE_ROW_INCONSISTENT"    # a source row contradicts itself (e.g. strength_text vs structured columns)
IMPLAUSIBLE_VALUE = "IMPLAUSIBLE_VALUE"                # value outside a plausibility window (e.g. 500 mg losartan syrup)
INTERACTION_TERM_UNMAPPED = "INTERACTION_TERM_UNMAPPED" # an interaction-seed ingredient/class has no drug-master ingredient
DUPLICATE_SOURCE_ROW = "DUPLICATE_SOURCE_ROW"          # same identity appears twice in a source with different values
EXPIRED_STOCK = "EXPIRED_STOCK"                        # stock row past expiry relative to reference date

ALL = [v for k, v in dict(globals()).items() if k.isupper() and isinstance(v, str)]
