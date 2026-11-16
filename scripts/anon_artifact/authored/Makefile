WORK ?= $(CURDIR)/work
WORK_FRESH ?= $(CURDIR)/work_fresh
DATA ?= $(CURDIR)/data
GEM5_ROOT ?= $(CURDIR)/gem5
AMULET_REPO ?= $(WORK)/amulet-repo
AMULET_PY ?= python3
PYTHON ?= python3
JAVAC ?= javac
PARALLEL ?= 12
GEN_CPU_S ?= 0.93
JAVA ?= java
CPUS ?= 0-31
JOBS ?= 16
SCONS3 ?= $(SCONS)
SCONS ?= $(shell command -v scons)
SCONS2 ?= python2 $(SCONS)

ALLOY_VERSION := 6.2.0
ALLOY_URL := https://github.com/AlloyTools/org.alloytools.alloy/releases/download/v$(ALLOY_VERSION)/org.alloytools.alloy.dist.jar
ALLOY_SHA256 := 6b8c1cb5bc93bedfc7c61435c4e1ab6e688a242dc702a394628d9a9801edb78d
AMULET_URL := https://github.com/sith-lab/amulet.git
AMULET_COMMIT := c871bdf

TMPDIR := /tmp
PYTHONDONTWRITEBYTECODE := 1
SIMSPECT_JAVA := $(JAVA)
SIMSPECT_JAVAC := $(JAVAC)
export WORK GEM5_ROOT AMULET_REPO AMULET_PY TMPDIR PYTHONDONTWRITEBYTECODE SIMSPECT_JAVA SIMSPECT_JAVAC
SIM := $(PYTHON) simspect.py

.PHONY: numbers corpus-unpack timing-sample eval-recon scons-check gem5 gem5-hits gem5-eval all setup alloy amulet-fetch corpus corpus-extra corpus-stt corpus-recon hits classify rounds pool timing amulet-hits amulet-timing compare eval experiments

all: setup corpus-unpack hits

experiments: setup gem5 corpus-unpack hits rounds pool timing amulet-fetch amulet-hits amulet-timing compare numbers

setup: alloy

gem5: gem5-hits gem5-eval

scons-check:
	@test -n "$(SCONS)" || { echo "scons not found: install SCons or set SCONS=/path/to/scons"; exit 1; }

gem5-hits: scons-check
	cd $(GEM5_ROOT)/amulet-gem5-InvisiSpec_AE-v1.1 && $(SCONS2) -j$(JOBS) build/X86_MESI_Two_Level/gem5.opt
	cd $(GEM5_ROOT)/amulet-gem5-CleanupSpec_AE-v1.1 && $(SCONS2) -j$(JOBS) build/X86_MESI_Two_Level/gem5.opt
	cd $(GEM5_ROOT)/amulet-gem5-SpecLFB_AE-v1.1 && $(SCONS3) -j$(JOBS) build/X86/gem5.opt --ignore-style

gem5-eval: scons-check
	cd $(GEM5_ROOT)/gem5-recon-modded && $(SCONS3) -j$(JOBS) build/X86/gem5.opt --ignore-style
	cd $(GEM5_ROOT)/gem5-recon-ruby3 && $(SCONS3) -j$(JOBS) build/X86/gem5.opt PROTOCOL=MESI_Three_Level
	cd $(GEM5_ROOT)/stt-master && $(SCONS2) -j$(JOBS) build/X86/gem5.opt
	cd $(GEM5_ROOT)/amulet-gem5-STT_AE-v1.1 && $(SCONS2) -j$(JOBS) build/X86/gem5.opt

alloy: STAGE1_alloy/alloy6.jar STAGE1_alloy/a6CountModels.class STAGE1_alloy/a6RandomModels.class

STAGE1_alloy/alloy6.jar:
	curl -fL -o $@.tmp $(ALLOY_URL)
	echo "$(ALLOY_SHA256)  $@.tmp" | shasum -a 256 -c -
	mv $@.tmp $@

STAGE1_alloy/%.class: STAGE1_alloy/%.java STAGE1_alloy/alloy6.jar
	cd STAGE1_alloy && $(JAVAC) -cp alloy6.jar:. $*.java

amulet-fetch:
	test -d $(AMULET_REPO)/.git || git clone $(AMULET_URL) $(AMULET_REPO)
	cd $(AMULET_REPO) && git checkout -q $(AMULET_COMMIT)

numbers:
	$(PYTHON) STAGE3_gem5/timing/numbers.py --data $(DATA)

corpus-unpack:
	mkdir -p $(WORK)/testsets
	for f in $(DATA)/corpus/*.tar.xz; do n=$$(basename $$f .tar.xz); test -f $(WORK)/testsets/$$n/READY || tar -xJf $$f -C $(WORK)/testsets; done

corpus: alloy
	WORK=$(WORK_FRESH) $(SIM) corpus --gen-config runconfigs/generate/Footprint_6_u_main.json

corpus-extra: alloy
	WORK=$(WORK_FRESH) $(SIM) corpus --gen-config runconfigs/generate/Footprint_6_u_extra.json

corpus-stt: alloy
	WORK=$(WORK_FRESH) $(SIM) corpus --gen-config runconfigs/generate/STT_6_u.json

corpus-recon: alloy
	WORK=$(WORK_FRESH) $(SIM) corpus --gen-config runconfigs/generate/Recon_6_u.json

hits: corpus-unpack
	$(SIM) hits --parallel $(PARALLEL)

classify:
	$(SIM) classify

rounds: corpus-unpack
	$(SIM) rounds --parallel $(PARALLEL)

pool: corpus-unpack
	$(SIM) pool --parallel $(PARALLEL)

timing-sample:
	mkdir -p $(WORK)/timing/sample
	test -f $(WORK)/timing/sample/sample.tsv || cp $(DATA)/timing/sample/sample.tsv $(DATA)/timing/sample/sample_meta.json $(WORK)/timing/sample/

timing: corpus-unpack timing-sample
	$(SIM) timing --parallel 16 --cpus $(CPUS)

amulet-hits: amulet-fetch
	$(SIM) amulet-hits

amulet-timing: amulet-fetch
	$(SIM) amulet-timing --cpus $(CPUS)

compare:
	$(SIM) compare --gen $(GEN_CPU_S)

eval: corpus-unpack
	$(SIM) eval --rows E2 E2w E3 E4 --model STT_6_u_A

eval-recon: corpus-recon
	WORK=$(WORK_FRESH) $(SIM) eval --rows E6 --model Recon_6_u_A
