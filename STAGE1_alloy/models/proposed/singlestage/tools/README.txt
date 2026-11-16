Shared tools for the single-stage (flat) draft models in ../<family>/ (2026-11-09, singlestage session).
run_flat.py                 enumerate one model under several solver orders, with log + runs.jsonl (see its docstring)
census_flat.py              shape/dedup census of the output (see its docstring)
check_bound_consistency.py  lint: fold depth / IX atoms / Int vs the instruction bound (run_flat refuses if it fails)
a6RandomModels.java         a6CountModels with a seeded randomized SAT4J order
Model generator: ../../../proposed_twophase/stage15_bound/make_s15_model.py (--pin none = flat model at a new bound)
Docs: wiki/design/TWO_PHASE_MODELS.md, sections '2026-11-09'. cafe2 workspace: /tests/singlestage_20261109/
