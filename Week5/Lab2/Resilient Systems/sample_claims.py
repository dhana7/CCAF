"""
sample_claims.py - Three mock insurance claims for the pipeline.

Notice that CLM-002 has `member_active: False`. The validation subagent
must catch this and return a `StageResult(ok=False, ...)` so the
coordinator can record the failure without crashing.
"""

CLAIMS = [
    {
        "claim_id": "CLM-001",
        "member_id": "M-501",
        "member_active": True,
        "procedure_code": "99213",   # office visit - covered
        "amount": 120.00,
        "narrative": "Routine office visit, member presented with mild fever.",
    },
    {
        "claim_id": "CLM-002",
        "member_id": "M-777",
        "member_active": False,      # <-- This should fail validation.
        "procedure_code": "70551",
        "amount": 850.00,
        "narrative": "MRI scan of the brain following persistent headaches.",
    },
    {
        "claim_id": "CLM-003",
        "member_id": "M-501",
        "member_active": True,
        "procedure_code": "93000",   # EKG - covered
        "amount": 95.00,
        "narrative": "Electrocardiogram performed during cardiology consult.",
    },
]


# Tiny policy table the validation subagent consults.
COVERED_PROCEDURES = {"99213", "70551", "93000", "99214"}
