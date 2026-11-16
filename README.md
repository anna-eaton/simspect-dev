# SimSpect

SimSpect generates litmus tests for speculative-execution defenses from an Alloy model of the defense, then runs each test on the defense's gem5 implementation to check whether it actually leaks. A test that the model says the defense must block but gem5 lets through is the research signal (a model gap, a harness artifact, or a real defense bug).

## Stages and the files that implement them

| Stage | What it does | Files |
|---|---|---|
| 1a. Minimal violating graphs | Alloy enumerates minimal instruction graphs (skeletons / "cores") in which a transmitter operand is in the defense's protection set while speculative. | `STAGE1_alloy/models/*.als` (core models `*_core_ri.als`), `STAGE1_alloy/a6CountModels.java`, `STAGE1_alloy/a6RandomModels.java` + `alloy_solver_order.py` (seeded order, cross-seed dedup), `STAGE1_alloy/models/proposed_twophase/{partition_stage1,launch_stage1,run_stage1}.py` |
| 1b. Loosened graphs | Each core is pinned loosely into the full model (`*_lpP.als`) and re-enumerated, so the final graphs carry extra instructions around the minimal skeleton. | `STAGE1_alloy/models/proposed/ultimate/loosepin/{stage15lp,make_loosepin,merge_lp,stream_fp}.py`, `STAGE1_alloy/stage_seed.py` |
| 2. Concretization | Each Alloy XML instance becomes LLVM IR, then x86 assembly plus an annotation (`.ann.json`) naming the transmitter, branches and commit boundary; optional post-passes add RMW and `jmp` variants. | `STAGE2_compilation/parsexml.py`, `batch_generate.py`, `compile_annotate.py`, `instruction_tables/`, `make_rmw_corpus.py`, `make_jmp_corpus.py` |
| 3. gem5 run and check | Each test is built and run on a gem5 build with O3PipeView tracing; a per-transmitter checker decides whether the transmitter acted inside the speculative window and obtained its data. | `STAGE3_gem5/gem5_common.py`, `check_ld.py`, `check_br.py`, `check_other.py`, `check_footprint.py` (+ `specs/leakage/*.json`), `cache_setup.py`, `timing/` |

Orchestration: `pipeline.py` (phases `xml`, `llvm`, `asm`, `gem5`, `all`, `clean`), `testsetgen.py` (Stages 1–2 streamed, no gem5), `testrun.py` (Stage 3 consumer, results split by transmitter kind), `twostage_lp.py` (Stage 1a → 1b → 2 for a core-pinned family). The `Makefile` wraps them (`make help`). Full command reference: `wiki/state/COMMANDS.md`; design notes: `wiki/README.md`.

## Prerequisites

- Python 3 (standard library only for the pipeline itself).
- Java 17. On the Mac: `/opt/homebrew/opt/openjdk@17/bin/java` (put `/opt/homebrew/opt/openjdk@17/bin` on `PATH`); in the cafe `gem5_dev` container: `/usr/bin/java`.
- Alloy 6: `STAGE1_alloy/alloy6.jar` (in the repo). `a6CountModels.class` is git-ignored, so compile it once in a fresh clone: `cd STAGE1_alloy && javac -cp alloy6.jar a6CountModels.java`. `a6RandomModels.class` is compiled on demand by `alloy_solver_order.py`.
- `clang-15` on `PATH` for the `asm` phase (`STAGE2_compilation/compile_annotate.py` calls it to target x86-64 Linux); it is installed in the `gem5_dev` container.
- gem5 builds for Stage 3. They live on the cafe nodes inside the `gem5_dev` container (`/work/...`); the list of builds, schemes and flags is `specs/gem5_builds.json` and `wiki/design/MODELS_AND_BUILDS.md`. Connect with `make hold` then `make cafe` (`wiki/state/INFRA.md`).

## Run the pipeline on any `.als` file

Every phase reads one JSONC run config. The keys that decide where things go are under `paths`:

- `paths.models_dir`: directory holding `<model>.als`; `--model <stem>` is resolved as `<models_dir>/<stem>.als` (`pipeline.py` `phase_xml`, `testsetgen.py`).
- `paths.testset_dir`: testsets are written to `<testset_dir>/<stem>/` (`xml/`, then `<mode>/{llvm,asm,ann}/` when `speculation.branch_modes` is set).
- `paths.results_dir` + `paths.results_name`: `pipeline.py gem5`/`all` write to `<results_dir>/<results_name>/<mode>/`. `testrun.py` always writes to `results/<results_name>__<timestamp>/` (it ignores `results_dir`).

Relative paths resolve against the repo root (`simspect_paths.resolve`), not against the config file.

### One command, output in `build/`

`build/` is git-ignored and meant for ad-hoc testsets and results. `scripts/run_als.sh` writes `build/configs/<stem>.jsonc` (the base config with `models_dir` set to the `.als` file's directory and `testset_dir`/`results_dir` set to `build/testsets`/`build/results`) and calls the existing entry point:

```bash
scripts/run_als.sh path/to/MyDefense.als                         # Stages 1-2 via testsetgen.py -> build/testsets/MyDefense/
scripts/run_als.sh path/to/MyDefense.als runconfigs/<cfg>.jsonc   # same, from another base config
scripts/run_als.sh path/to/MyDefense.als runconfigs/<cfg>.jsonc all   # pipeline.py all (needs gem5) -> build/results/MyDefense/
```

The default base config is `runconfigs/regen_lp_20261110/stage2_fv3.jsonc` (Stage-2 recipe v3). Pick a base config whose `gem5` block names the build you want before running `gem5`/`all`, and whose `alloy.max_instances` is the cap you want.

### By hand

Copy a config, set `paths.models_dir` to the `.als` file's directory and `paths.testset_dir`/`paths.results_dir` to where output should go (for example `build/testsets`, `build/results`), then:

```bash
python3 testsetgen.py --model MyDefense --config build/configs/MyDefense.jsonc      # Stages 1-2, streamed (= make gen)
python3 testrun.py    --model MyDefense --config build/configs/MyDefense.jsonc      # Stage 3 on one gem5 build (= make run)
python3 pipeline.py all  --model MyDefense --config build/configs/MyDefense.jsonc   # all phases, sequential
python3 pipeline.py xml  --model MyDefense --config build/configs/MyDefense.jsonc   # one phase only
```

Phases skip work whose output already exists; pass `--force` (or `FORCE=1` to `make`) to redo a phase, and delete stale stage output after changing `parsexml.py` or the model. For the two-stage core-pinned flow (Stage 1a → 1b → 2) use `make twostage-lp CONFIG=runconfigs/twostage_lp/<Family>.jsonc WS=<workspace>` (see `twostage_lp.py`).

To check a single test directory by hand with full per-record output, run a checker directly with the same gem5 settings as the config (`pipeline.py` `_build_gem5_env` maps `gem5.*` keys to `SIMSPECT_*` environment variables): `python3 STAGE3_gem5/check_ld.py <dir-with-.s-and-.ann.json> --jobs 16 --scheme 2 --out full.json`.
