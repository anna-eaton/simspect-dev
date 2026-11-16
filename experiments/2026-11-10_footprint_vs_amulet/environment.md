# Environment of the 2026-11-10 footprint-vs-AMuLeT experiment

Recorded 2026-11-10 by the snapshot agent, read-only, from the cafe1 and cafe3 `gem5_dev` containers while firstdet-final was still running. Raw command output: `environment/raw_env_cafe1.txt`, `environment/raw_env_cafe3.txt` (the script that produced them is at the end of this file). Everything below was identical on cafe1 and cafe3 unless noted.

## Hosts and container

| host | role in this experiment | CPUs seen by the container | memory | container image |
|---|---|---|---|---|
| cafe1.stanford.edu | corpus generation (Stage 1, 1.5, 2, RMW, jmp; regen-lp), second consumer for the CleanupSpec rows (T2rt/T2g/T2u5 `_cafe1` dirs), AMuLeT T5 campaigns and per-bug replays | 64 (Intel Xeon Gold 6226R @ 2.90 GHz) | 503 GB | `simspect_gem5_dev:20261109`, image id `sha256:ef9c710614d20674dbb078a3f5b2aa5a6aac5caead2db2319d73c6fecc1f7fbc` |
| cafe3.stanford.edu | first-detection runs T1rt/T2rt/T3rt, T1g/T2g/T3g, T2u5, classification loop and reports | 64 (same CPU model) | 503 GB | same image id |

The bare ssh login shell on both hosts reports `nproc` = 2 (the cgroup of the login session); all work ran inside `gem5_dev`, which sees 64 CPUs.

## gem5 binaries (AMuLeT artifact builds with SimSpect print-only hooks v2)

The trees under `/work/amulet/` are AMuLeT's AE tarball extracts, not git checkouts, so each source tree is identified by a content hash: the sha256 of the sorted `sha256sum` list of every file under `src/` and `configs/` (`.pyc` excluded). Binary and tree hashes are identical on cafe1 and cafe3.

| defense | binary | md5 | sha256 | built (mtime, UTC) | src+configs tree hash | SimSpect hooks |
|---|---|---|---|---|---|---|
| InvisiSpec (Futuristic) | `/work/amulet/amulet-gem5-InvisiSpec_AE-v1.1/build/X86_MESI_Two_Level/gem5.opt` | `f45251db6d580f12e549751b9331a3ca` | `54a5f7031d6fc2b7bda2e33c7a47632a528df1bdc4f69214911830dc3a16ef29` | 2026-11-08 00:56:16 | `c23aa786ca7e6a14c8668e6933a446c87f3585a4f0a7b3b309b9c8adf2c36237` | ver=2 (`simspect_hooks.cc` md5 `ba5d8404be86a29835ae35e7fc434a5e`) |
| CleanupSpec | `/work/amulet/amulet-gem5-CleanupSpec_AE-v1.1/build/X86_MESI_Two_Level/gem5.opt` | `ec5710cad23e43b265f08657710fcb21` | `ea5d42af07f4e4cfa14eeba7d089032f6efb194ba73e39925a4a8cfe837ddb18` | 2026-10-30 21:27:08 | `7c142cb6ca8562afba8b0097c47992d6868ff7190843b2997ea362be2df05a61` | ver=2 (md5 `f6ae54552e946ced34e1b13f83cf05b0`) |
| SpecLFB | `/work/amulet/amulet-gem5-SpecLFB_AE-v1.1/build/X86/gem5.opt` | `a84176e23121db26d8f2f9019d586566` | `757646a09bb5898b509079995e0d80f142fb6f2ad30a44a983864ebd5ad279f5` | 2026-11-08 01:03:32 | `744d37e302da5b2e19a61195d74ec16425b2d058b1a0a42113005a20ef0e1e3e` | ver=2 (md5 `e80773054bac94e259b565c122ebac5e`) |
| STT (AMuLeT T5 only, not in the comparison) | `/work/amulet/amulet-gem5-STT_AE-v1.1/build/X86/gem5.opt` | `1ff765a880ff895ecfe55b80bf80c990` | `553b1a95243baa8999965abeab13c4cb59766c94bc86a3c87e565334c2c47073` | 2026-10-30 21:27:08 | `5a5961c7efff3e24a8b800a587f522894c41a3f8c9272b33b8695ab86a39b71d` | resolve hooks only |

- Hook version: every trace starts with `O3PipeView:simspect:0:META:hooks:...:ver=2:build=<Defense>` (`simspect_hooks.cc:78-79` in each tree). The exact hook sources as built are copied in `environment/gem5_hook_sources_as_built/` (with each tree's `configs/example/se.py`, the config script every run config names). The repo patch files of that era are copied in `environment/gem5_hooks_repo_diffs/` (from `gem5-hooks/amulet-*`). The hooks print only under the O3PipeView debug flag, so they are inactive in AMuLeT's own T5 runs.
- Which run used which binary: `configs/firstdet_final_20261110/*.jsonc` (`gem5.binary`, `gem5.config_script`, `gem5.extra_args`); each run's `config.ini` is in `results/firstdet_final/<host>/<run>/config.ini`.

## Alloy / Java (Stage 1 and 1.5)

- `alloy6.jar` sha256 `6b8c1cb5bc93bedfc7c61435c4e1ab6e688a242dc702a394628d9a9801edb78d` (cafe1 `loosepin_regen/code/STAGE1_alloy/alloy6.jar`; identical to the Mac `STAGE1_alloy/alloy6.jar`). A copy is inside the corpus tarball (`data/`), path `loosepin_regen/code/STAGE1_alloy/alloy6.jar`.
- Java: OpenJDK 17.0.15 (build 17.0.15+6-Ubuntu-0ubuntu120.04), `/usr/bin/java` in `gem5_dev`.
- Enumerators: `STAGE1_alloy/a6RandomModels.java` (seeded random SAT4J order, Stage 1.5) and `a6CountModels.java` (Stage 1); sources in `code/run_hosts/cafe1_loosepin_regen/code/STAGE1_alloy/` (the `.class` files were not copied; recompile with `javac -cp alloy6.jar`).

## SimSpect toolchain (Stage 2 and gem5 harness)

- Python 3.8.10 (`/usr/bin/python3` in `gem5_dev`) runs `pipeline.py`, the Stage-2 tools, the checkers and the timing scripts.
- clang 10.0.0-4ubuntu1, gcc 9.4.0, GNU assembler 2.34 (Binutils 2.34); `make_jmp_corpus.py` also needs `llvm-objdump-15` (as `compile_annotate.py` does).
- `TMPDIR=/tmp` for every gem5 run (H-STK).

## AMuLeT (T5 baseline)

- Repo: cafe1 `/tests/simspect_alloy_20261108/timing/amulet_t5/amulet-repo`, commit `c871bdf6d143cb298c1e548c64b143bac40af09d` (copied from cafe2 `/work/amulet-repo`). Untracked files present (not used by T5): `STT_GADGET_ANALYSIS.md`, `src/analyze_gadgets.py`, `src/gen_stt_tests.py`, `stt_corpus/`, `stt_corpus_gadgets.json`. Changes for T5: only the YAML gem5 paths and output dirs (`results/amulet_t5/runs/<D>_<UTC>/yaml.diff`), the measurement-only `benchmark_t5.py` (generated by `make_benchmark_t5.py` with asserted replacements), and empty `build/X86` dirs created in the two Ruby trees (no source or binary touched).
- Venv: `/opt/amulet-venv`, Python 3.11.8 (from `/opt/python`). `pip freeze` (also in `environment/amulet_venv_pip_freeze.txt`): iced-x86==1.21.0, numpy==2.4.6, protobuf==3.20.0, pydot==4.0.1, pyparsing==3.3.2, PyYAML==6.0.3, toml==0.10.2, types-PyYAML==6.0.12.20260518, unicorn==2.1.4, xxhash==3.7.0.

## Mac (where the snapshot was assembled)

- macOS 26.6; repo working tree base commit `264adea` plus uncommitted changes (see `git status` at snapshot time). The Mac only relayed files (`relay_cafe3.sh`) and held the source of truth for docs; no simulation ran on it.

## How this was collected

```bash
# inside gem5_dev on cafe1 and on cafe3 (read-only):
for D in InvisiSpec:X86_MESI_Two_Level CleanupSpec:X86_MESI_Two_Level SpecLFB:X86 STT:X86; do n=${D%%:*}; b=${D##*:}; t=/work/amulet/amulet-gem5-${n}_AE-v1.1
  md5sum $t/build/$b/gem5.opt; sha256sum $t/build/$b/gem5.opt; stat -c '%y %s bytes' $t/build/$b/gem5.opt
  (cd $t && find src configs -type f ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum | sha256sum)
done
java -version; sha256sum <code>/STAGE1_alloy/alloy6.jar; python3 --version
/opt/amulet-venv/bin/python --version; /opt/amulet-venv/bin/pip freeze
(cd amulet-repo && git rev-parse HEAD && git status --short)
clang --version; gcc --version; as --version
# on the host: docker inspect gem5_dev --format '{{.Image}} {{.Config.Image}}'
```
