from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Tuple, Optional
import json
import xml.etree.ElementTree as ET
import re
import random
from pathlib import Path

@dataclass
class AlloyInstance:
    sig_atoms: Dict[str, Set[str]]
    fields: Dict[str, List[Tuple[str, ...]]]


def parse_alloy_xml(xml_text: str) -> AlloyInstance:
    root = ET.fromstring(xml_text)

    sig_atoms: Dict[str, Set[str]] = {}
    fields: Dict[str, List[Tuple[str, ...]]] = {}

    for sig in root.iter("sig"):
        label = sig.attrib.get("label", "")
        atoms = set()
        for atom in sig.findall("atom"):
            atoms.add(atom.attrib["label"])
        sig_atoms[label] = atoms

    for field in root.iter("field"):
        flabel = field.attrib.get("label", "")
        tups: List[Tuple[str, ...]] = []
        for tup in field.findall("tuple"):
            atoms = [a.attrib["label"] for a in tup.findall("atom")]
            tups.append(tuple(atoms))
        fields[flabel] = tups

    return AlloyInstance(sig_atoms=sig_atoms, fields=fields)

def topo_sort(nodes: List[str], edges: List[Tuple[str, str]]) -> List[str]:
    adj: Dict[str, List[str]] = {n: [] for n in nodes}
    indeg: Dict[str, int] = {n: 0 for n in nodes}
    for a, b in edges:
        if a not in adj:
            adj[a] = []
            indeg[a] = 0
        if b not in adj:
            adj[b] = []
            indeg[b] = 0
        adj[a].append(b)
        indeg[b] += 1

    q = [n for n in nodes if indeg.get(n, 0) == 0]
    out: List[str] = []
    while q:
        n = q.pop()
        out.append(n)
        for m in adj.get(n, []):
            indeg[m] -= 1
            if indeg[m] == 0:
                q.append(m)

    if len(out) != len(set(nodes)):
        raise ValueError("spo graph is not a DAG or nodes list is incomplete.")

    return out

def llvm_escape(name: str) -> str:
    return name.replace("$", "_")


def _atom_sort_key(atom: str) -> Tuple[str, int, str]:
    m = re.match(r"^(.*)\$(\d+)$", atom)
    if not m:
        return (atom, -1, atom)
    prefix, num = m.group(1), int(m.group(2))
    return (prefix, num, atom)


def _build_rel_map(pairs: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for left, right in pairs:
        out.setdefault(left, []).append(right)
    for k in out:
        out[k] = sorted(out[k], key=_atom_sort_key)
    return out


_TYPE_TAG_TO_KIND: Dict[str, str] = {
    "TLoad":    "ld",
    "TStore":   "str",
    "TBranchn": "br_n",
    "TBranchx": "br_x",
    "TOthern":  "other_n",
    "TOtherx":  "other_x",
}

def _kind_token(ins: str, kind_of: Dict[str, str]) -> str:
    tag = kind_of.get(ins, "")
    base = tag.split("$")[0] if "$" in tag else tag
    return _TYPE_TAG_TO_KIND.get(base, "unknown")


def _format_slots(
    role: str,
    operands: List[str],
    opstate_of: Dict[str, str],
    slot_count: int,
) -> List[str]:
    fields: List[str] = []
    for idx in range(slot_count):
        slot_name = f"{role}{idx}" if slot_count > 1 else role
        if idx < len(operands):
            op = operands[idx]
            physical = opstate_of.get(op, op)
            fields.append(f"{slot_name}=specified:{physical}")
        else:
            fields.append(f"{slot_name}=nonspecified")
    return fields


def _build_slot_records(
    role: str,
    operands: List[str],
    opstate_of: Dict[str, str],
    slot_count: int,
) -> List[Dict[str, Any]]:
    slots: List[Dict[str, Any]] = []
    for idx in range(slot_count):
        slot_name = f"{role}{idx}" if slot_count > 1 else role
        if idx < len(operands):
            op_atom = operands[idx]
            physical = opstate_of.get(op_atom, op_atom)
            slots.append(
                {
                    "slot": slot_name,
                    "specified": True,
                    "operand_atom": op_atom,
                    "physical": physical,
                }
            )
        else:
            slots.append(
                {
                    "slot": slot_name,
                    "specified": False,
                    "operand_atom": None,
                    "physical": None,
                }
            )
    return slots


_STEP_KINDS_DEFAULT = ["other_n", "ld", "str"]


def _unspecified_slot(slot_name: str) -> Dict[str, Any]:
    return {"slot": slot_name, "specified": False, "operand_atom": None, "physical": None}


def _fr_slot(slot_name: str, atom: str) -> Dict[str, Any]:
    return {"slot": slot_name, "specified": True, "operand_atom": None, "physical": atom}


def _make_chain_step(
    chain_id: int,
    step_idx: int,
    kind: str,
    concrete: str,
    llvm_op: str,
    slots: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    return {
        "pc": -1,
        "instruction": f"_chain{chain_id}_step{step_idx}",
        "kind": kind,
        "concrete_instruction": concrete,
        "llvm_op": llvm_op,
        "candidates": [concrete],
        "resolved": False,
        "committed": False,
        "xm": False,
        "slots": slots,
        "synthetic": True,
    }


def _build_chain(
    chain_id: int,
    length: int,
    fr_reg_atoms: List[str],
    fr_mem_atoms: List[str],
    step_kinds: List[str],
    rng: random.Random,
    ilv_chain: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    if length <= 0 or not fr_reg_atoms:
        return []

    have_mem = bool(fr_mem_atoms)
    allowed = [k for k in step_kinds if k != "str" or have_mem]
    if not allowed:
        allowed = ["other_n"]

    steps: List[Dict[str, Any]] = []
    reg_ctr = 0
    mem_ctr = 0

    def alloc_outreg() -> str:
        nonlocal reg_ctr
        atom = fr_reg_atoms[reg_ctr % len(fr_reg_atoms)]
        reg_ctr += 1
        return atom

    def alloc_outmem() -> Optional[str]:
        nonlocal mem_ctr
        if not fr_mem_atoms:
            return None
        atom = fr_mem_atoms[mem_ctr % len(fr_mem_atoms)]
        mem_ctr += 1
        return atom

    last_kind: Optional[str] = None
    last_atom: Optional[str] = None

    for s in range(length):
        if last_kind == "mem":
            kind = "ld"
        else:
            kind = rng.choice(allowed)

        slots = {
            "inreg":  [_unspecified_slot("inreg0"), _unspecified_slot("inreg1")],
            "inaddr": [_unspecified_slot("inaddr")],
            "inmem":  [_unspecified_slot("inmem")],
            "outreg": [_unspecified_slot("outreg")],
            "outmem": [_unspecified_slot("outmem")],
        }

        if s > 0 and last_atom is not None:
            if last_kind == "reg":
                if kind == "ld":
                    slots["inaddr"][0] = _fr_slot("inaddr", last_atom)
                elif kind == "str":
                    if rng.random() < 0.5:
                        slots["inaddr"][0] = _fr_slot("inaddr", last_atom)
                    else:
                        slots["inreg"][0] = _fr_slot("inreg0", last_atom)
                else:
                    idx = rng.randint(0, 1)
                    slots["inreg"][idx] = _fr_slot(f"inreg{idx}", last_atom)
            else:
                slots["inmem"][0] = _fr_slot("inmem", last_atom)

        if kind == "other_n":
            ent = rng.choice(ilv_chain) if ilv_chain else None
            two_inputs = _ilv_refs(ent["asm"], 2) if ent is not None else rng.random() < 0.7
            if not two_inputs:
                if slots["inreg"][1]["specified"]:
                    slots["inreg"][0], slots["inreg"][1] = slots["inreg"][1], _unspecified_slot("inreg1")
                    slots["inreg"][0]["slot"] = "inreg0"
                concrete, llvm_op = "bitnot", "notq"
            else:
                concrete, llvm_op = "add", "leaq"
            if ent is not None:
                concrete, llvm_op = ILV_PREFIX + ent["name"], "inline asm (interleave_only)"
            out = alloc_outreg()
            slots["outreg"][0] = _fr_slot("outreg", out)
            last_kind, last_atom = "reg", out

        elif kind == "ld":
            out = alloc_outreg()
            slots["outreg"][0] = _fr_slot("outreg", out)
            concrete, llvm_op = "load", "movq"
            last_kind, last_atom = "reg", out

        else:
            out = alloc_outmem()
            if out is None:
                reg_out = alloc_outreg()
                slots["outreg"][0] = _fr_slot("outreg", reg_out)
                slots["inreg"][1]  = _unspecified_slot("inreg1")
                kind, concrete, llvm_op = "other_n", "bitnot", "notq"
                last_kind, last_atom = "reg", reg_out
            else:
                slots["outmem"][0] = _fr_slot("outmem", out)
                concrete, llvm_op = "store", "movq"
                last_kind, last_atom = "mem", out

        steps.append(_make_chain_step(chain_id, s, kind, concrete, llvm_op, slots))

    return steps


def pass1_specify_state_a(
    inst: AlloyInstance,
    out_path: Optional[str] = "alloy-out/spo_program.ir",
    write_out: bool = True,
) -> Dict[str, Any]:
    instr_atoms: Set[str] = set(inst.sig_atoms.get("this/Instruction", set()))

    kind_of: Dict[str, str] = {ins: tag for ins, tag in inst.fields.get("kind", [])}

    nodes = sorted(instr_atoms, key=_atom_sort_key)
    spo_edges = [
        (a, b)
        for (a, b) in inst.fields.get("spo", [])
        if a in instr_atoms and b in instr_atoms
    ]
    order = topo_sort(nodes, spo_edges)

    inregs_of = _build_rel_map(inst.fields.get("inreg", []))
    inaddrs_of = _build_rel_map(inst.fields.get("inaddr", []))
    inmems_of = _build_rel_map(inst.fields.get("inmem", []))
    outregs_of = _build_rel_map(inst.fields.get("outreg", []))
    outmems_of = _build_rel_map(inst.fields.get("outmem", []))

    opstate_of: Dict[str, str] = {}
    for op, st in inst.fields.get("opstate", []):
        opstate_of[op] = st

    resolved_instrs = {ins for (ins, _) in inst.fields.get("isresolved", [])}
    committed_instrs = {ins for (ins, _) in inst.fields.get("iscommitted", [])}
    has_commit_split = "isuncommitted" in inst.fields
    must_uncommitted_instrs = {ins for (ins, _) in inst.fields.get("isuncommitted", [])}
    xm_instrs        = {ins for (ins, _) in inst.fields.get("isxm",        [])}

    reg_states = inst.sig_atoms.get("this/Reg_s", set())
    mem_states = inst.sig_atoms.get("this/Mem_s", set())
    used_regs: Set[str] = set()
    used_mems: Set[str] = set()

    lines: List[str] = []
    lines.append("# SPO Abstract Program (phase 1)")
    lines.append("# state elements are physical locations from opstate")
    lines.append("")

    instruction_records: List[Dict[str, Any]] = []

    slot_shape = {
        "inreg": 2,
        "inaddr": 1,
        "inmem": 1,
        "outreg": 1,
        "outmem": 1,
    }

    _rf_src = {t[0] for t in inst.fields.get("rf", []) if t}

    for pc, ins in enumerate(order):
        kind = _kind_token(ins, kind_of)
        resolved_bool  = ins in resolved_instrs
        committed_bool = ins in committed_instrs
        xm_bool        = ins in xm_instrs
        resolved  = "true" if resolved_bool  else "false"
        committed = "true" if committed_bool else "false"

        inregs = inregs_of.get(ins, [])
        inaddrs = inaddrs_of.get(ins, [])
        inmems = inmems_of.get(ins, [])
        outregs = outregs_of.get(ins, [])
        outmems = outmems_of.get(ins, [])

        for op in inregs + inaddrs + outregs:
            st = opstate_of.get(op)
            if st in reg_states:
                used_regs.add(st)
        for op in inmems + outmems:
            st = opstate_of.get(op)
            if st in mem_states:
                used_mems.add(st)

        fields: List[str] = []
        fields.extend(_format_slots("inreg", inregs, opstate_of, slot_shape["inreg"]))
        fields.extend(_format_slots("inaddr", inaddrs, opstate_of, slot_shape["inaddr"]))
        fields.extend(_format_slots("inmem", inmems, opstate_of, slot_shape["inmem"]))
        fields.extend(_format_slots("outreg", outregs, opstate_of, slot_shape["outreg"]))
        fields.extend(_format_slots("outmem", outmems, opstate_of, slot_shape["outmem"]))

        slots: Dict[str, List[Dict[str, Any]]] = {
            "inreg": _build_slot_records("inreg", inregs, opstate_of, slot_shape["inreg"]),
            "inaddr": _build_slot_records("inaddr", inaddrs, opstate_of, slot_shape["inaddr"]),
            "inmem": _build_slot_records("inmem", inmems, opstate_of, slot_shape["inmem"]),
            "outreg": _build_slot_records("outreg", outregs, opstate_of, slot_shape["outreg"]),
            "outmem": _build_slot_records("outmem", outmems, opstate_of, slot_shape["outmem"]),
        }

        instruction_records.append(
            {
                "pc": pc,
                "instruction": ins,
                "kind": kind,
                "resolved":  resolved_bool,
                "committed": committed_bool,
                "outreg_consumed": any(o in _rf_src for o in outregs),
                "must_uncommitted": (ins in must_uncommitted_instrs) if has_commit_split
                                    else not committed_bool,
                "xm":        xm_bool,
                "slots": slots,
            }
        )

        line = f"{pc:04d} {ins} {kind} resolved={resolved} committed={committed} " + " ".join(fields)
        lines.append(line)

    lines.append("")
    lines.append("# resource usage")
    lines.append(f"register_count={len(used_regs)}")
    lines.append(f"memory_count={len(used_mems)}")
    lines.append("registers=" + ",".join(sorted(used_regs, key=_atom_sort_key)))
    lines.append("memory=" + ",".join(sorted(used_mems, key=_atom_sort_key)))

    result: Dict[str, Any] = {
        "instructions": instruction_records,
        "resource_usage": {
            "register_count": len(used_regs),
            "memory_count": len(used_mems),
            "registers": sorted(used_regs, key=_atom_sort_key),
            "memory": sorted(used_mems, key=_atom_sort_key),
        },
    }

    if write_out:
        if out_path is None:
            raise ValueError("out_path must not be None when write_out=True")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    return result


def _load_instruction_tables(
    path: Optional[Path] = None,
) -> tuple[Dict[str, str], Dict[str, List[Dict[str, Any]]]]:
    if path is None:
        path = Path(__file__).parent / "instruction_tables" / "instructions.jsonc"
    text = Path(path).read_text(encoding="utf-8")
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'//[^\n]*', '', text)
    data = json.loads(text)
    kind_categories: Dict[str, str] = data["kind_categories"]
    instructions: Dict[str, List[Dict[str, Any]]] = {
        category: [
            {**entry, "uses": set(entry["uses"])}
            for entry in entries
        ]
        for category, entries in data["instructions"].items()
    }
    return kind_categories, instructions


def reload_tables(path: Optional[str] = None) -> None:
    global _KIND_TO_CATEGORY, INSTRUCTION_TABLE, BRANCH_FORMS
    _KIND_TO_CATEGORY, INSTRUCTION_TABLE = _load_instruction_tables(
        Path(path) if path else None
    )
    BRANCH_FORMS = _load_branch_forms(Path(path) if path else None)


def _load_branch_forms(path: Optional[Path] = None) -> Dict[str, Any]:
    if path is None:
        path = Path(__file__).parent / "instruction_tables" / "instructions.jsonc"
    text = Path(path).read_text(encoding="utf-8")
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'//[^\n]*', '', text)
    return dict(json.loads(text).get("branch_forms", {}))


_KIND_TO_CATEGORY, INSTRUCTION_TABLE = _load_instruction_tables()
BRANCH_FORMS: Dict[str, Any] = {}


def pass2_specify_instructions(
    pass1_result: Dict[str, Any],
    instruction_table: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    out_path: Optional[str] = None,
    write_out: bool = False,
    vocab_rj: Optional[Dict[str, Any]] = None,
    exclude_tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if instruction_table is None:
        instruction_table = INSTRUCTION_TABLE
    _rmw_on = bool(vocab_rj and vocab_rj.get("rmw"))
    _excl = set(exclude_tags or [])
    if _excl:
        instruction_table = {k: [c for c in v if not _excl & set(c.get("tags", []))]
                             for k, v in instruction_table.items()}

    output_instructions: List[Dict[str, Any]] = []

    for rec in pass1_result["instructions"]:
        kind = rec["kind"]
        category = _KIND_TO_CATEGORY.get(kind, "other")
        candidates = instruction_table.get(category, [])

        specified_slots: Set[str] = set()
        for slot_list in rec["slots"].values():
            for sr in slot_list:
                if sr["specified"]:
                    specified_slots.add(sr["slot"])

        valid = [c for c in candidates if specified_slots <= c["uses"]]
        if (_rmw_on and category == "ld" and not rec.get("outreg_consumed", True)
                and specified_slots - {"outreg"} <= VOCAB_RJ_RMW["uses"]):
            valid = valid + [VOCAB_RJ_RMW]

        if not valid:
            valid = [c for c in candidates if not c.get("base")] or candidates

        chosen = random.choice(valid) if valid else None

        out_rec = dict(rec)
        if chosen and chosen.get("base"):
            out_rec["vocab_form"] = chosen["name"]
            chosen = dict(chosen, name=chosen["base"])
        out_rec["concrete_instruction"] = chosen["name"] if chosen else None
        out_rec["llvm_op"] = chosen["llvm_op"] if chosen else None
        out_rec["candidates"] = [c["name"] for c in valid]
        output_instructions.append(out_rec)

    result: Dict[str, Any] = {
        "instructions": output_instructions,
        "resource_usage": pass1_result["resource_usage"],
    }

    if write_out:
        if out_path is None:
            raise ValueError("out_path must not be None when write_out=True")
        lines = ["# SPO Abstract Program (phase 2 - instruction assignment)"]
        lines.append("# concrete_instruction and llvm_op added; operands still mostly unspecified")
        lines.append("")
        for rec in output_instructions:
            concrete = rec.get("concrete_instruction") or "?"
            llvm_op  = rec.get("llvm_op") or "?"
            cands    = rec.get("candidates") or []
            slot_parts: List[str] = []
            for slot_list in rec["slots"].values():
                for sr in slot_list:
                    if sr["specified"]:
                        slot_parts.append(f"{sr['slot']}=specified:{sr['physical']}")
                    else:
                        slot_parts.append(f"{sr['slot']}=nonspecified")
            lines.append(
                f"{rec['pc']:04d} {rec['instruction']} "
                f"{rec['kind']}->{concrete} (llvm: {llvm_op}) "
                f"resolved={str(rec['resolved']).lower()} "
                f"committed={str(rec['committed']).lower()} "
                f"candidates=[{','.join(cands)}] "
                + " ".join(slot_parts)
            )
        lines.append("")
        ru = result["resource_usage"]
        lines.append(f"register_count={ru['register_count']}")
        lines.append(f"memory_count={ru['memory_count']}")
        lines.append("registers=" + ",".join(ru["registers"]))
        lines.append("memory=" + ",".join(ru["memory"]))
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    return result


_BRANCH_KINDS = {"br_n", "br_x"}


def pass2_5_specify_branches(
    pass2_result: Dict[str, Any],
    branch_mode: str = "mispredict_not_taken",
    out_path: Optional[str] = None,
    write_out: bool = False,
) -> Dict[str, Any]:
    if branch_mode not in ("mispredict_not_taken", "mispredict_taken", "stl_bypass"):
        raise ValueError(f"Unknown branch_mode: {branch_mode!r}")
    if branch_mode == "stl_bypass":
        unresolved_brs = [
            rec["pc"] for rec in pass2_result["instructions"]
            if rec.get("kind") in _BRANCH_KINDS
            and not rec.get("resolved", False) and not rec.get("xm", False)
        ]
        if unresolved_brs:
            raise ValueError(
                f"stl_bypass mode needs every branch resolved (no control-flow "
                f"speculation); unresolved branch pc(s) {unresolved_brs}. "
                f"Use an *_stl model.")

    n = len(pass2_result["instructions"])
    instructions: List[Dict[str, Any]] = [dict(rec) for rec in pass2_result["instructions"]]
    needs_end_block = False

    xm_nop_inserts: List[Tuple[int, int]] = []

    for idx, rec in enumerate(instructions):
        if rec.get("kind") not in _BRANCH_KINDS:
            continue

        pc = rec["pc"]
        next_pc = pc + 1
        is_xm = rec.get("xm", False)

        if is_xm:
            rec["concrete_instruction"] = "br_bez"
            rec["llvm_op"]              = "testq+jz"
            cands = rec.get("candidates", [])
            if "br_bez" not in cands:
                rec["candidates"] = cands + ["br_bez"]
            needs_end_block = True
            if idx == len(instructions) - 1:
                xm_nop_inserts.append((idx, pc))
            fallthrough = "end_block" if next_pc >= n else f"bb_{next_pc}"
            rec["branch_annotations"] = {
                "mode":               "mispredict_not_taken",
                "condition_value":    True,
                "taken_target":       "end_block",
                "fallthrough_target": fallthrough,
                "btb_prediction":     "fall_through",
                "btb_predicted_pc":   next_pc,
            }
            continue

        if rec.get("concrete_instruction") in ("br_uncond", "br_bez"):
            rec["concrete_instruction"] = "br_cond"
            rec["llvm_op"]              = "br i1"
            cands = rec.get("candidates", [])
            if "br_cond" not in cands:
                rec["candidates"] = cands + ["br_cond"]

        if rec.get("resolved", False):
            if rec.get("concrete_instruction") == "br_uncond":
                rec["concrete_instruction"] = "br_cond"
                rec["llvm_op"] = "br i1"
                cands = rec.get("candidates", [])
                if "br_cond" not in cands:
                    rec["candidates"] = cands + ["br_cond"]
            needs_end_block = True
            rec["branch_annotations"] = {
                "mode":               "correctly_not_taken",
                "condition_value":    False,
                "taken_target":       "end_block",
                "fallthrough_target": f"bb_{next_pc}" if next_pc < n else "end_block",
                "btb_prediction":     "fall_through",
                "btb_predicted_pc":   next_pc,
            }
            continue

        if rec.get("concrete_instruction") == "br_uncond":
            rec["concrete_instruction"] = "br_cond"
            rec["llvm_op"] = "br i1"
            cands = rec.get("candidates", [])
            if "br_cond" not in cands:
                rec["candidates"] = cands + ["br_cond"]

        if is_xm:
            rec["concrete_instruction"] = "br_bez"
            rec["llvm_op"] = "testq+jz"

        if branch_mode == "mispredict_not_taken":
            needs_end_block = True

            if is_xm and (idx == len(instructions) - 1
                          or instructions[idx + 1].get("kind") in _BRANCH_KINDS):
                xm_nop_inserts.append((idx, pc))

            fallthrough = "end_block" if next_pc >= n else f"bb_{next_pc}"
            rec["branch_annotations"] = {
                "mode":               "mispredict_not_taken",
                "condition_value":    True,
                "taken_target":       "end_block",
                "fallthrough_target": fallthrough,
                "btb_prediction":     "fall_through",
                "btb_predicted_pc":   next_pc,
            }

        elif branch_mode == "mispredict_taken":
            needs_end_block = True

            if is_xm and (idx == len(instructions) - 1
                          or instructions[idx + 1].get("kind") in _BRANCH_KINDS):
                xm_nop_inserts.append((idx, pc))

            taken = f"bb_{next_pc}" if next_pc < n else "end_block"
            rec["branch_annotations"] = {
                "mode":               "mispredict_taken",
                "condition_value":    False,
                "taken_target":       taken,
                "fallthrough_target": "end_block",
                "btb_prediction":     "taken",
                "btb_predicted_pc":   next_pc,
            }

    for insert_idx, br_pc in reversed(xm_nop_inserts):
        nop_pc = br_pc + 1
        nop_rec: Dict[str, Any] = {
            "pc":                     nop_pc,
            "instruction":            "_xm_fallthrough_nop",
            "kind":                   "other_n",
            "concrete_instruction":   "nop",
            "llvm_op":               "nop",
            "candidates":            ["nop"],
            "resolved":              False,
            "committed":             False,
            "xm":                    False,
            "slots":                 {},
            "synthetic":             True,
        }
        instructions.insert(insert_idx + 1, nop_rec)
        ba = instructions[insert_idx].get("branch_annotations")
        if ba:
            if ba.get("mode") == "mispredict_not_taken" and ba["fallthrough_target"] == "end_block":
                ba["fallthrough_target"] = f"bb_{nop_pc}"
            elif ba.get("mode") == "mispredict_taken" and ba["taken_target"] == "end_block":
                ba["taken_target"] = f"bb_{nop_pc}"


    result: Dict[str, Any] = {
        "instructions": instructions,
        "resource_usage": pass2_result["resource_usage"],
        "branch_mode": branch_mode,
        "needs_end_block": needs_end_block,
    }

    if write_out:
        if out_path is None:
            raise ValueError("out_path must not be None when write_out=True")
        lines = ["# SPO Abstract Program (phase 2.5 - branch annotation)"]
        lines.append(f"# branch_mode: {branch_mode}")
        lines.append("")
        for rec in result["instructions"]:
            ba = rec.get("branch_annotations")
            slot_parts: List[str] = []
            for slot_list in rec["slots"].values():
                for sr in slot_list:
                    tag = f"specified:{sr['physical']}" if sr["specified"] else "nonspecified"
                    slot_parts.append(f"{sr['slot']}={tag}")
            line = (
                f"{rec['pc']:04d} {rec['instruction']} "
                f"{rec['kind']}->{rec.get('concrete_instruction', '?')} "
                f"resolved={str(rec['resolved']).lower()} "
                f"committed={str(rec['committed']).lower()} "
                + " ".join(slot_parts)
            )
            if ba:
                line += (
                    f" [BRANCH mode={ba['mode']}"
                    f" cond={ba['condition_value']}"
                    f" taken={ba['taken_target']}"
                    f" fallthrough={ba['fallthrough_target']}"
                    f" btb={ba['btb_prediction']}"
                    f" btb_pc={ba['btb_predicted_pc']}]"
                )
            lines.append(line)
        lines.append("")
        ru = result["resource_usage"]
        lines.append(f"register_count={ru['register_count']}")
        lines.append(f"memory_count={ru['memory_count']}")
        lines.append("registers=" + ",".join(ru["registers"]))
        lines.append("memory=" + ",".join(ru["memory"]))
        lines.append(f"needs_end_block={needs_end_block}")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    return result


def _specified_physical(rec: Dict[str, Any], role: str) -> Optional[str]:
    for sr in rec.get("slots", {}).get(role, []):
        if sr.get("specified"):
            return sr.get("physical")
    return None


def pass2_6_specify_stl(pass25_result: Dict[str, Any]) -> Dict[str, Any]:
    instructions: List[Dict[str, Any]] = [dict(rec) for rec in pass25_result["instructions"]]
    n_pairs = 0

    for i, s in enumerate(instructions):
        if s.get("kind") != "str" or s.get("resolved", False) or s.get("synthetic"):
            continue
        m = _specified_physical(s, "outmem")
        if m is None:
            raise ValueError(f"stl_bypass: unresolved store pc={s['pc']} has no specified outmem")
        loads = []
        for t in instructions[i + 1:]:
            if t.get("kind") == "str" and _specified_physical(t, "outmem") == m:
                break
            if (t.get("kind") == "ld" and not t.get("committed", False)
                    and _specified_physical(t, "inmem") == m):
                loads.append(t)
        if not loads:
            raise ValueError(f"stl_bypass: unresolved store pc={s['pc']} ({m}) has no aliasing load")
        s["stl_annotation"] = {"role": "store", "pair": n_pairs, "mem_atom": m}
        loads[0]["stl_annotation"] = {"role": "bypass_load", "pair": n_pairs, "mem_atom": m}
        for t in loads[1:]:
            t["stl_annotation"] = {"role": "alias_load", "pair": n_pairs, "mem_atom": m}
        n_pairs += 1

    if n_pairs == 0:
        raise ValueError("stl_bypass: instance has no unresolved store")

    out = dict(pass25_result)
    out["instructions"] = instructions
    return out


def _stl_pairs(instructions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_pair: Dict[int, Dict[str, Any]] = {}
    for rec in instructions:
        tag = rec.get("stl_annotation")
        if not tag:
            continue
        e = by_pair.setdefault(tag["pair"], {"pair": tag["pair"], "mem_atom": tag["mem_atom"],
                                             "alias_load_pcs": []})
        if tag["role"] == "alias_load":
            e["alias_load_pcs"].append(rec["pc"])
        else:
            e["store_pc" if tag["role"] == "store" else "load_pc"] = rec["pc"]
    return [by_pair[k] for k in sorted(by_pair)]


_MASK64 = (1 << 64) - 1
_PROBE_MEM_BYTES = 256 * 8


def _to_signed64(v: int) -> int:
    v &= _MASK64
    return v - (1 << 64) if v >> 63 else v


def _mem_addr_of(rec: Dict[str, Any], mem_role: str,
                 vals: Dict[str, int]) -> Tuple[str, int, Optional[str]]:
    ia = None
    for sr in rec["slots"].get("inaddr", []):
        if sr.get("specified") and sr.get("ssa_name") and sr.get("assigned"):
            ia = sr
    if ia is not None:
        return "probe", _to_signed64(vals.get(ia["ssa_name"], 0)), ia["ssa_name"]
    for sr in rec["slots"].get(mem_role, []):
        if sr.get("assigned_offset") is not None:
            return "mem", sr["assigned_offset"], None
    raise ValueError(f"pc={rec['pc']}: no address for {mem_role}")


def _stl_arch_values(instructions: List[Dict[str, Any]], until_pc: int,
                     alloca_n: int,
                     store_override: Optional[Dict[int, Optional[Tuple[str, int]]]] = None,
                     ) -> Dict[str, int]:
    store_override = store_override or {}
    vals: Dict[str, int] = {}
    mem: Dict[Tuple[str, int], int] = {}
    bounds = {"mem": alloca_n * 8, "probe": _PROBE_MEM_BYTES}

    def val(rec: Dict[str, Any], slot_name: str) -> int:
        for sl in rec["slots"].values():
            for sr in sl:
                if sr["slot"] == slot_name and sr.get("ssa_name"):
                    return vals.setdefault(sr["ssa_name"], 0)
        return 0

    def out(rec: Dict[str, Any], v: int) -> None:
        for sr in rec["slots"].get("outreg", []):
            if sr.get("ssa_name"):
                vals[sr["ssa_name"]] = v & _MASK64

    def check(space: str, off: int) -> None:
        if off < 0 or off + 8 > bounds[space]:
            raise ValueError(f"stl_bypass: access {space}+{off} out of bounds")

    for rec in instructions:
        if rec["pc"] >= until_pc:
            break
        c = rec.get("concrete_instruction")
        if c == "load":
            space, off, _ = _mem_addr_of(rec, "inmem", vals)
            check(space, off)
            out(rec, sum(mem.get((space, off + b), 0) << (8 * b) for b in range(8)))
        elif c == VOCAB_RJ_RMW["name"]:
            space, off, _ = _mem_addr_of(rec, "inmem", vals)
            check(space, off)
        elif c == "store":
            if rec["pc"] in store_override:
                if store_override[rec["pc"]] is None:
                    continue
                space, off = store_override[rec["pc"]]
            else:
                space, off, _ = _mem_addr_of(rec, "outmem", vals)
            check(space, off)
            v = 0 if _fv4_store_imm(rec) else val(rec, "inreg0") & _MASK64
            for b in range(8):
                mem[(space, off + b)] = (v >> (8 * b)) & 0xFF
        elif c == "bitnot":
            out(rec, ~val(rec, "inreg0"))
        elif c == "add":
            out(rec, val(rec, "inreg0") + val(rec, "inreg1"))
        elif c == "zsm":
            out(rec, val(rec, "inreg0") * val(rec, "inreg1"))
        elif c in FV4_ALU_UNARY or c in FV4_ALU_BINARY:
            out(rec, _fv4_alu_eval(_fv4_alu_effective(rec), val(rec, "inreg0"), val(rec, "inreg1")))
        elif c == "div":
            a, d = _to_signed64(val(rec, "inreg0")), _to_signed64(val(rec, "inreg1"))
            if not rec.get("xm", False):
                d = _to_signed64(d | 1)
            if d == 0 or (a == -(1 << 63) and d == -1):
                raise ValueError(f"stl_bypass: div at pc={rec['pc']} faults")
            q = abs(a) // abs(d)
            out(rec, q if (a < 0) == (d < 0) else -q)
        elif c in ("br_cond", "br_uncond", "br_bez"):
            ba = rec.get("branch_annotations") or {}
            if ba.get("condition_value") or c == "br_bez":
                raise ValueError(f"stl_bypass: architecturally taken branch at pc={rec['pc']} before the bypass load")
        elif c == "nop":
            pass
        else:
            raise ValueError(f"stl_bypass: can't evaluate {c!r} at pc={rec['pc']}")
    return vals


def _stl_store_retargets(pass4_result: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    instructions = pass4_result["instructions"]
    alloca_n = pass4_result["alloca_total_slots"]
    by_pc = {rec["pc"]: rec for rec in instructions}
    out: Dict[int, Dict[str, Any]] = {}
    override: Dict[int, Optional[Tuple[str, int]]] = {}
    for p in _stl_pairs(instructions):
        s, l = by_pc[p["store_pc"]], by_pc[p["load_pc"]]
        s_ia = any(sr.get("specified") and sr.get("ssa_name") for sr in s["slots"].get("inaddr", []))
        l_ia = any(sr.get("specified") and sr.get("ssa_name") for sr in l["slots"].get("inaddr", []))
        if not s_ia and not l_ia:
            s_off = _mem_addr_of(s, "outmem", {})[1]
            l_off = _mem_addr_of(l, "inmem", {})[1]
            if s_off != l_off:
                raise ValueError(f"stl_bypass: store pc={s['pc']} and load pc={l['pc']} "
                                 f"share {p['mem_atom']} but got slots {s_off} != {l_off}")
            continue
        vals = _stl_arch_values(instructions, l["pc"], alloca_n, {**override, s["pc"]: None})
        l_space, l_addr, _ = _mem_addr_of(l, "inmem", vals)
        if l_addr < 0 or l_addr + 8 > (_PROBE_MEM_BYTES if l_space == "probe" else alloca_n * 8):
            raise ValueError(f"stl_bypass: bypass load pc={l['pc']} address {l_space}+{l_addr} out of bounds")
        vals2 = _stl_arch_values(instructions, l["pc"], alloca_n, {**override, s["pc"]: (l_space, l_addr)})
        if _mem_addr_of(l, "inmem", vals2)[:2] != (l_space, l_addr):
            raise ValueError(f"stl_bypass: bypass load pc={l['pc']} address depends on the re-targeted store")
        if s_ia:
            _, s_idx_val, s_idx_ssa = _mem_addr_of(s, "outmem", vals2)
            disp = l_addr - s_idx_val
        else:
            s_idx_ssa, disp = None, l_addr
        if not -(1 << 31) <= disp < (1 << 31):
            raise ValueError(f"stl_bypass: store pc={s['pc']} displacement {disp} out of range")
        override[s["pc"]] = (l_space, l_addr)
        out[s["pc"]] = {"space": l_space, "disp": disp, "index_ssa": s_idx_ssa,
                        "addr": l_addr}
    return out


def _stl_alias_load_matches(pass4_result: Dict[str, Any]) -> Dict[int, List[int]]:
    instructions = pass4_result["instructions"]
    alloca_n = pass4_result["alloca_total_slots"]
    by_pc = {rec["pc"]: rec for rec in instructions}
    retargets = _stl_store_retargets(pass4_result)
    override = {pc: (r["space"], r["addr"]) for pc, r in retargets.items()}
    out: Dict[int, List[int]] = {}
    for p in _stl_pairs(instructions):
        s = by_pc[p["store_pc"]]
        target = override.get(s["pc"]) or _mem_addr_of(s, "outmem", {})[:2]
        keep = []
        for a_pc in p["alias_load_pcs"]:
            try:
                vals = _stl_arch_values(instructions, a_pc, alloca_n, override)
            except ValueError:
                continue
            if _mem_addr_of(by_pc[a_pc], "inmem", vals)[:2] == target:
                keep.append(a_pc)
        out[p["pair"]] = keep
    return out


def pass_interleave(
    pass25_result: Dict[str, Any],
    interleave_cfg: Optional[Dict[str, Any]] = None,
    rng: Optional[random.Random] = None,
) -> Dict[str, Any]:
    cfg = interleave_cfg or {}
    if not cfg.get("enabled", False):
        result = dict(pass25_result)
        result["fr_reg_pool"] = []
        result["fr_mem_pool"] = []
        return result

    if rng is None:
        rng = random.Random()

    fp_cfg     = cfg.get("free_pool", {})
    n_fr_reg   = int(fp_cfg.get("reg", 5))
    n_fr_mem   = int(fp_cfg.get("mem", 3))
    chain_cfg  = cfg.get("chain", {})
    min_length = int(chain_cfg.get("min_length", 2))
    max_length = int(chain_cfg.get("max_length", 4))
    step_kinds: List[str] = list(chain_cfg.get("step_kinds", _STEP_KINDS_DEFAULT))
    num_chains = min(max(int(cfg.get("num_chains", 1)), 0), 2)
    _ilv_icfg = cfg.get("interleave_only") or {}
    ilv_chain = _ilv_chain_entries(_ilv_select(_ilv_icfg)) if _ilv_icfg.get("enabled") else None
    if _ilv_icfg.get("enabled") and not ilv_chain:
        raise ValueError("interleave.interleave_only: no usable chain entries after exclude_tags")
    if num_chains == 0:
        result = dict(pass25_result)
        result["fr_reg_pool"] = []
        result["fr_mem_pool"] = []
        return result

    fr_reg_atoms = [f"Reg_s$fr{k}" for k in range(max(n_fr_reg, 1))]
    fr_mem_atoms = [f"Mem_s$fr{k}" for k in range(n_fr_mem)] if n_fr_mem > 0 else []

    if not fr_mem_atoms and "str" in step_kinds:
        step_kinds = [k for k in step_kinds if k != "str"]
    if not step_kinds:
        step_kinds = ["other_n"]

    instructions = [dict(rec) for rec in pass25_result["instructions"]]
    N = len(instructions)

    first_uncommitted_idx = N
    for i, rec in enumerate(instructions):
        if not rec.get("committed", False):
            first_uncommitted_idx = i
            break

    all_steps: List[Dict[str, Any]] = []
    for cid in range(num_chains):
        lo = max(min_length, 1)
        hi = max(max_length, lo)
        length = rng.randint(lo, hi)
        all_steps.extend(_build_chain(cid, length, fr_reg_atoms, fr_mem_atoms, step_kinds, rng,
                                      ilv_chain=ilv_chain))

    L = len(all_steps)
    uncommitted_count = N - first_uncommitted_idx

    pool_size = uncommitted_count + L
    rel_positions: Set[int] = set(
        rng.sample(range(pool_size), min(L, pool_size))
    ) if pool_size > 0 else set()

    new_instructions: List[Dict[str, Any]] = list(instructions[:first_uncommitted_idx])
    chain_iter  = iter(all_steps)
    orig_iter   = iter(instructions[first_uncommitted_idx:])
    for pos in range(pool_size):
        if pos in rel_positions:
            step = next(chain_iter, None)
            if step is not None:
                new_instructions.append(step)
        else:
            orig = next(orig_iter, None)
            if orig is not None:
                new_instructions.append(orig)
    new_instructions.extend(s for s in orig_iter)
    new_instructions.extend(s for s in chain_iter)

    for new_pc, rec in enumerate(new_instructions):
        rec["pc"] = new_pc

    for i, rec in enumerate(new_instructions):
        ba = rec.get("branch_annotations")
        if not ba:
            continue
        ba["btb_predicted_pc"] = rec["pc"] + 1
        has_next = (i + 1 < len(new_instructions))
        mode = ba.get("mode", "")
        spec_key = ("taken_target"
                    if mode in ("mispredict_taken", "correctly_taken")
                    else "fallthrough_target")
        for key in ("fallthrough_target", "taken_target"):
            t = ba.get(key, "")
            if t.startswith("bb_"):
                ba[key] = (f"bb_{rec['pc'] + 1}" if has_next else "end_block")
            elif t == "end_block" and key == spec_key and has_next:
                ba[key] = f"bb_{rec['pc'] + 1}"

    return {
        "instructions":   new_instructions,
        "resource_usage": pass25_result["resource_usage"],
        "branch_mode":    pass25_result.get("branch_mode"),
        "needs_end_block": pass25_result.get("needs_end_block", False),
        "fr_reg_pool":    fr_reg_atoms,
        "fr_mem_pool":    fr_mem_atoms,
    }


X86_64_CALLER_SAVED: List[str] = [
    "rax", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11",
    "r12", "r13", "r14", "r15",
]

_VPOOL_IDX_SCRATCH    = 0
_VPOOL_IDX_COND_REG   = 1
_VPOOL_IDX_PROBE_BASE = 2
_VPOOL_FREE_START     = 3

FV2_SPLICE_OPS: Dict[str, str] = {
    "add0":   "addq $$0, $0",
    "or0":    "orq $$0, $0",
    "xor0":   "xorq $$0, $0",
    "and_m1": "andq $$-1, $0",
    "imul1":  "imulq $$1, $0, $0",
    "lea0":   "leaq 0($0), $0",
    "not2":   "notq $0\\0Anotq $0",
    "neg2":   "negq $0\\0Anegq $0",
    "rol_ror":"rolq $$13, $0\\0Arorq $$13, $0",
    "add_sub":"addq $$4097, $0\\0Asubq $$4097, $0",
    "xor2":   "xorq $$85, $0\\0Axorq $$85, $0",
    "bswap2": "bswapq $0\\0Abswapq $0",
}
FV2_FILLER_OPS: Dict[str, str] = {
    "add":  "movq $1, $0\\0Aaddq $2, $0",
    "xor":  "movq $1, $0\\0Axorq $2, $0",
    "and":  "movq $1, $0\\0Aandq $2, $0",
    "imul": "movq $1, $0\\0Aimulq $2, $0",
    "lea":  "leaq ($1,$2), $0",
    "shl":  "movq $1, $0\\0Ashlq $$3, $0",
}

VOCAB_RJ_RMW: Dict[str, Any] = {
    "name": "load_rmw_or0",
    "llvm_op": "orq $0, mem (inline asm)",
    "uses": {"inaddr", "inmem"},
    "requires": "outreg_unconsumed",
}
FV2_FILLER_JMP = "jmp"
LOAD_LIKE = ("load", VOCAB_RJ_RMW["name"])

ILV_TABLE_DEFAULT = "STAGE2_compilation/instruction_tables/proposed/interleave_only.jsonc"
ILV_PREFIX = "ilv:"
_ILV_CACHE: Dict[str, Dict[str, Dict[str, Any]]] = {}
_ILV_USES: Dict[str, Set[str]] = {}


def _ilv_refs(asm: str, n: int) -> bool:
    t = asm.replace("$$", "")
    return f"${n}" in t or ("${%d:" % n) in t


def load_interleave_only(path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    p = Path(path or ILV_TABLE_DEFAULT)
    if not p.is_absolute() and not p.exists():
        p = Path(__file__).resolve().parent.parent / p
    key = str(p.resolve())
    if key not in _ILV_CACHE:
        text = p.read_text(encoding="utf-8")
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        text = re.sub(r'//[^\n]*', '', text)
        ents: Dict[str, Dict[str, Any]] = {}
        for e in json.loads(text)["entries"]:
            if e.get("status", "ok") != "ok" or int(e.get("weight", 1)) != 1:
                continue
            if e.get("form", "rr") not in ("rr", "none"):
                raise ValueError(f"interleave_only entry {e['name']!r}: unknown form {e.get('form')!r}")
            ents[e["name"]] = e
            _ILV_USES[ILV_PREFIX + e["name"]] = (
                {"inreg0", "outreg"} | ({"inreg1"} if _ilv_refs(e["asm"], 2) else set()))
        _ILV_CACHE[key] = ents
    return _ILV_CACHE[key]


def _ilv_entry(name: str) -> Dict[str, Any]:
    for ents in _ILV_CACHE.values():
        if name in ents:
            return ents[name]
    raise ValueError(f"interleave_only entry {name!r} not loaded")


def _ilv_select(icfg: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    ents = load_interleave_only(icfg.get("table"))
    tags = list(icfg.get("exclude_tags") or [])
    return {n: e for n, e in ents.items() if not any(e.get(t) for t in tags)}


def _ilv_chain_entries(ents: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [e for e in ents.values() if e.get("form", "rr") == "rr" and _ilv_refs(e["asm"], 1)]

FV4_ALU_UNARY: Dict[str, Optional[str]] = {"mov_rr": None, "neg": "negq", "shl3": "shlq $$3,"}
FV4_ALU_BINARY: Dict[str, str] = {"addq_rr": "addq", "sub_rr": "subq", "xor_rr": "xorq",
                                  "and_rr": "andq", "or_rr": "orq", "lea_s8": "lea"}
_FV4_COMMUTATIVE = {"addq_rr", "xor_rr", "and_rr", "or_rr"}


def _fv4_store_imm(rec: Dict[str, Any]) -> bool:
    if rec.get("vocab_form") != "store_imm":
        return False
    return not any(sr.get("specified") for sr in rec["slots"].get("inreg", [])
                   if sr["slot"] == "inreg0")


def _fv4_alu_effective(rec: Dict[str, Any]) -> str:
    c = rec.get("concrete_instruction")
    if c in ("sub_rr", "xor_rr"):
        ph = [sr.get("assigned") for sr in rec["slots"].get("inreg", [])
              if sr["slot"] in ("inreg0", "inreg1")]
        if len(ph) == 2 and ph[0] is not None and ph[0] == ph[1]:
            return "or_rr"
    return c


def _fv4_alu_eval(c: str, a: int, b: int) -> int:
    return {"mov_rr": a, "neg": -a, "shl3": a << 3, "addq_rr": a + b, "sub_rr": a - b,
            "xor_rr": a ^ b, "and_rr": a & b, "or_rr": a | b, "lea_s8": a + 8 * b}[c]

_REG_SLOT_ROLES = {"inreg", "outreg", "inaddr"}
_MEM_SLOT_ROLES = {"inmem", "outmem"}


def _uses_for(concrete_instruction: Optional[str]) -> Set[str]:
    if concrete_instruction is None:
        return set()
    if concrete_instruction == VOCAB_RJ_RMW["name"]:
        return VOCAB_RJ_RMW["uses"]
    if concrete_instruction.startswith(ILV_PREFIX):
        return _ILV_USES[concrete_instruction]
    for candidates in INSTRUCTION_TABLE.values():
        for c in candidates:
            if c["name"] == concrete_instruction:
                return c["uses"]
    return set()


def pass3_assign_operands(
    pass25_result: Dict[str, Any],
    out_path: Optional[str] = None,
    write_out: bool = False,
    reg_naming: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    locked_reg_atoms: List[str] = pass25_result["resource_usage"]["registers"]
    locked_mem_atoms: List[str] = pass25_result["resource_usage"]["memory"]
    n_locked_regs = len(locked_reg_atoms)
    n_locked_mems = len(locked_mem_atoms)

    if n_locked_regs > len(X86_64_CALLER_SAVED):
        raise ValueError(
            f"Model uses {n_locked_regs} locked registers but only "
            f"{len(X86_64_CALLER_SAVED)} caller-saved registers are available"
        )

    _rn_mode = (reg_naming or {}).get("mode", "sorted")
    if _rn_mode == "sorted":
        reg_order: List[str] = list(X86_64_CALLER_SAVED)
    elif _rn_mode == "random":
        if "seed" not in reg_naming:
            raise ValueError("reg_naming mode 'random' needs a 'seed'")
        reg_order = random.Random(reg_naming["seed"]).sample(
            X86_64_CALLER_SAVED, len(X86_64_CALLER_SAVED))
    else:
        raise ValueError(f"reg_naming.mode must be 'sorted' or 'random': {_rn_mode!r}")

    locked_reg_map: Dict[str, str] = {
        atom: reg_order[i] for i, atom in enumerate(locked_reg_atoms)
    }

    n_free_regs = len(X86_64_CALLER_SAVED) - n_locked_regs
    virtual_pool: List[str] = reg_order[n_locked_regs:]
    free_pool: List[str] = virtual_pool[_VPOOL_FREE_START:]

    locked_mem_map: Dict[str, int] = {
        atom: i * 8 for i, atom in enumerate(locked_mem_atoms)
    }

    fr_reg_pool: List[str] = pass25_result.get("fr_reg_pool", [])
    fr_mem_pool: List[str] = pass25_result.get("fr_mem_pool", [])

    fr_reg_map: Dict[str, str] = {}
    if fr_reg_pool and free_pool:
        for i, atom in enumerate(fr_reg_pool):
            fr_reg_map[atom] = free_pool[i % len(free_pool)]
    chain_region: Set[str] = set(fr_reg_map.values())
    alloy_outreg_pool: List[str] = [r for r in free_pool if r not in chain_region]
    if not alloy_outreg_pool:
        alloy_outreg_pool = list(free_pool)

    fr_mem_map: Dict[str, int] = {
        atom: (n_locked_mems + i) * 8 for i, atom in enumerate(fr_mem_pool)
    }

    free_mem_slot: int = n_locked_mems + len(fr_mem_pool)

    instructions: List[Dict[str, Any]] = []

    for rec in pass25_result["instructions"]:
        new_rec = dict(rec)
        concrete = rec.get("concrete_instruction")
        uses = _uses_for(concrete)
        is_synthetic = bool(rec.get("synthetic"))

        new_slots: Dict[str, List[Dict[str, Any]]] = {}
        for role, slot_list in rec["slots"].items():
            new_slot_list: List[Dict[str, Any]] = []
            for sr in slot_list:
                new_sr = dict(sr)
                slot_name = sr["slot"]

                if role in _REG_SLOT_ROLES:
                    if sr["specified"]:
                        phys = sr["physical"]
                        if phys in locked_reg_map:
                            new_sr["assigned"] = locked_reg_map[phys]
                        elif phys in fr_reg_map:
                            new_sr["assigned"] = fr_reg_map[phys]
                        else:
                            new_sr["assigned"] = random.choice(free_pool) if free_pool else None
                    elif slot_name in uses:
                        if role == "outreg" and not is_synthetic:
                            pool = alloy_outreg_pool
                        else:
                            pool = free_pool
                        new_sr["assigned"] = random.choice(pool) if pool else None
                    else:
                        new_sr["assigned"] = None

                elif role in _MEM_SLOT_ROLES:
                    if sr["specified"]:
                        phys = sr["physical"]
                        if phys in locked_mem_map:
                            new_sr["assigned_offset"] = locked_mem_map[phys]
                        elif phys in fr_mem_map:
                            new_sr["assigned_offset"] = fr_mem_map[phys]
                        else:
                            new_sr["assigned_offset"] = None
                    elif slot_name in uses:
                        new_sr["assigned_offset"] = free_mem_slot * 8
                        free_mem_slot += 1
                    else:
                        new_sr["assigned_offset"] = None

                new_slot_list.append(new_sr)
            new_slots[role] = new_slot_list

        new_rec["slots"] = new_slots

        ba = rec.get("branch_annotations")
        if ba is not None:
            new_rec["condition_assigned"] = ba["condition_value"]

        instructions.append(new_rec)

    alloca_total_slots = free_mem_slot
    alloca_total_bytes = alloca_total_slots * 8

    result: Dict[str, Any] = {
        "instructions": instructions,
        "resource_usage": pass25_result["resource_usage"],
        "branch_mode": pass25_result.get("branch_mode"),
        "needs_end_block": pass25_result.get("needs_end_block", False),
        "locked_registers": locked_reg_map,
        "virtual_reg_pool": virtual_pool,
        "memory_offsets": locked_mem_map,
        "alloca_total_bytes": alloca_total_bytes,
        "alloca_total_slots": alloca_total_slots,
        "fr_reg_pool": fr_reg_pool,
        "fr_mem_pool": fr_mem_pool,
        **({"reg_naming": {"mode": "random", "seed": reg_naming["seed"]}}
           if _rn_mode == "random" else {}),
    }

    if write_out:
        if out_path is None:
            raise ValueError("out_path must not be None when write_out=True")
        pool_range = ", ".join(virtual_pool) if virtual_pool else "(empty)"
        lines = ["# SPO Abstract Program (phase 3 - operand assignment)"]
        lines.append(f"# locked_registers : {locked_reg_map}")
        lines.append(f"# virtual_pool     : {pool_range}")
        lines.append(f"# memory_offsets   : {locked_mem_map}")
        lines.append(f"# alloca           : {alloca_total_slots} x i64 = {alloca_total_bytes} bytes")
        lines.append("")
        for rec in instructions:
            slot_parts: List[str] = []
            for role, slot_list in rec["slots"].items():
                for sr in slot_list:
                    sn = sr["slot"]
                    if role in _REG_SLOT_ROLES:
                        a = sr.get("assigned")
                        if a is None:
                            slot_parts.append(f"{sn}=unused")
                        elif sr["specified"]:
                            slot_parts.append(f"{sn}={a}[locked]")
                        else:
                            slot_parts.append(f"{sn}={a}")
                    elif role in _MEM_SLOT_ROLES:
                        off = sr.get("assigned_offset")
                        if off is None:
                            slot_parts.append(f"{sn}=unused")
                        elif sr["specified"]:
                            slot_parts.append(f"{sn}=mem[{off}][locked]")
                        else:
                            slot_parts.append(f"{sn}=mem[{off}]")

            cond_str = (f" cond={rec['condition_assigned']}"
                        if "condition_assigned" in rec else "")
            ba = rec.get("branch_annotations")
            btb_str = (f" [btb={ba['btb_prediction']} btb_pc={ba['btb_predicted_pc']}]"
                       if ba else "")

            lines.append(
                f"{rec['pc']:04d} {rec['instruction']:12s} "
                f"{rec['kind']}->{rec.get('concrete_instruction', '?'):12s} "
                f"resolved={str(rec['resolved']).lower()} "
                f"committed={str(rec['committed']).lower()}"
                + cond_str + " "
                + " ".join(slot_parts)
                + btb_str
            )

        lines.append("")
        lines.append(f"locked_register_count={n_locked_regs}")
        lines.append(f"locked_memory_count={n_locked_mems}")
        lines.append(f"alloca_total_bytes={alloca_total_bytes}")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    return result


_SSA_WRITE_SLOT_NAMES: Set[str] = {"outreg"}

_SSA_READ_SLOT_NAMES: Set[str] = {"inreg0", "inreg1", "inaddr"}


def pass4_ssa(
    pass3_result: Dict[str, Any],
    out_path: Optional[str] = None,
    write_out: bool = False,
) -> Dict[str, Any]:
    current: Dict[str, str] = {}
    counter: Dict[str, int] = {}
    init_needed: Dict[str, str] = {}

    def fresh(reg: str) -> str:
        n = counter.get(reg, 0) + 1
        counter[reg] = n
        name = f"{reg}_{n}"
        current[reg] = name
        return name

    def lookup(reg: str) -> str:
        if reg not in current:
            name = f"{reg}_0"
            current[reg] = name
            init_needed[reg] = name
        return current[reg]

    instructions: List[Dict[str, Any]] = []

    for rec in pass3_result["instructions"]:
        concrete = rec.get("concrete_instruction")
        uses = _uses_for(concrete)

        new_rec = dict(rec)
        new_slots: Dict[str, List[Dict[str, Any]]] = {}

        pending_writes: List[Tuple[Dict[str, Any], str]] = []

        for role, slot_list in rec["slots"].items():
            new_slot_list: List[Dict[str, Any]] = []
            for sr in slot_list:
                new_sr = dict(sr)
                slot_name = sr["slot"]
                assigned = sr.get("assigned")

                if role in _REG_SLOT_ROLES and slot_name in uses and assigned is not None:
                    if slot_name in _SSA_WRITE_SLOT_NAMES:
                        new_sr["ssa_name"] = None
                        pending_writes.append((new_sr, assigned))
                    else:
                        new_sr["ssa_name"] = lookup(assigned)
                else:
                    new_sr["ssa_name"] = None

                new_slot_list.append(new_sr)
            new_slots[role] = new_slot_list

        for slot_dict, reg_name in pending_writes:
            slot_dict["ssa_name"] = fresh(reg_name)

        new_rec["slots"] = new_slots

        if rec.get("condition_assigned") is not None:
            new_rec["condition_ssa_forced"] = (
                "i1 true" if rec["condition_assigned"] else "i1 false"
            )

        instructions.append(new_rec)

    result: Dict[str, Any] = {
        "instructions": instructions,
        "resource_usage": pass3_result["resource_usage"],
        "branch_mode": pass3_result.get("branch_mode"),
        "needs_end_block": pass3_result.get("needs_end_block", False),
        "locked_registers": pass3_result["locked_registers"],
        "virtual_reg_pool": pass3_result["virtual_reg_pool"],
        "memory_offsets": pass3_result["memory_offsets"],
        "alloca_total_bytes": pass3_result["alloca_total_bytes"],
        "alloca_total_slots": pass3_result["alloca_total_slots"],
        "ssa_init": init_needed,
    }
    if "reg_naming" in pass3_result:
        result["reg_naming"] = pass3_result["reg_naming"]

    if write_out:
        if out_path is None:
            raise ValueError("out_path must not be None when write_out=True")
        phys_regs = set(pass3_result["locked_registers"].values())
        lines = ["# SPO Abstract Program (phase 4 - SSA)"]
        lines.append(f"# locked_registers : {pass3_result['locked_registers']}")
        lines.append(f"# ssa_init         : {init_needed}")
        lines.append(f"# alloca           : {pass3_result['alloca_total_slots']} x i64 "
                     f"({pass3_result['alloca_total_bytes']} bytes)")
        lines.append("")
        for rec in instructions:
            slot_parts: List[str] = []
            for role, slot_list in rec["slots"].items():
                for sr in slot_list:
                    sn = sr["slot"]
                    if role in _REG_SLOT_ROLES:
                        ssa = sr.get("ssa_name")
                        if ssa is None:
                            slot_parts.append(f"{sn}=-")
                        elif sr["specified"]:
                            slot_parts.append(f"{sn}={ssa}[locked]")
                        else:
                            slot_parts.append(f"{sn}={ssa}")
                    elif role in _MEM_SLOT_ROLES:
                        off = sr.get("assigned_offset")
                        if off is None:
                            slot_parts.append(f"{sn}=-")
                        elif sr["specified"]:
                            slot_parts.append(f"{sn}=mem[{off}][locked]")
                        else:
                            slot_parts.append(f"{sn}=mem[{off}]")

            cond_str = (f" cond_forced={rec['condition_ssa_forced']}"
                        if "condition_ssa_forced" in rec else "")
            ba = rec.get("branch_annotations")
            btb_str = (f" [btb={ba['btb_prediction']} btb_pc={ba['btb_predicted_pc']}]"
                       if ba else "")

            lines.append(
                f"{rec['pc']:04d} {rec['instruction']:12s} "
                f"{rec['kind']}->{rec.get('concrete_instruction', '?'):12s} "
                f"resolved={str(rec['resolved']).lower()} "
                f"committed={str(rec['committed']).lower()}"
                + cond_str + "  "
                + "  ".join(slot_parts)
                + btb_str
            )

        lines.append("")
        lines.append(f"ssa_init: {init_needed}")
        lines.append(f"locked_register_count={len(pass3_result['locked_registers'])}")
        lines.append(f"locked_memory_count={len(pass3_result['memory_offsets'])}")
        lines.append(f"alloca_total_bytes={pass3_result['alloca_total_bytes']}")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    return result


def commit_boundary(
    instructions: List[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    alloy = [rec for rec in instructions if not rec.get("synthetic")]
    last_committed = None
    for rec in alloy:
        if rec.get("committed", False):
            last_committed = rec
    first_noncommitted = next(
        (rec for rec in alloy
         if rec.get("must_uncommitted", not rec.get("committed", False))), None)
    return last_committed, first_noncommitted


def pass5_emit_llvm(
    pass4_result: Dict[str, Any],
    func_name: str = "test",
    out_path: Optional[str] = None,
    write_out: bool = False,
    fpr_cfg: Optional[Dict[str, Any]] = None,
    fv2_cfg: Optional[Dict[str, Any]] = None,
    stsep_cfg: Optional[Dict[str, Any]] = None,
    brcond_cfg: Optional[Dict[str, Any]] = None,
) -> str:
    instructions = pass4_result["instructions"]
    locked_registers: Dict[str, str] = pass4_result["locked_registers"]
    ssa_init: Dict[str, str] = pass4_result["ssa_init"]
    alloca_n: int = pass4_result["alloca_total_slots"]
    needs_end_block: bool = pass4_result.get("needs_end_block", False)

    new_block_pcs: Set[int] = set()
    for rec in instructions:
        ba = rec.get("branch_annotations")
        if not ba:
            continue
        for target_key in ("fallthrough_target", "taken_target"):
            t = ba.get(target_key, "")
            if t.startswith("bb_"):
                try:
                    new_block_pcs.add(int(t[3:]))
                except ValueError:
                    pass

    def get_slot(rec: Dict[str, Any], slot_name: str) -> Optional[Dict[str, Any]]:
        for slot_list in rec["slots"].values():
            for sr in slot_list:
                if sr["slot"] == slot_name:
                    return sr
        return None

    def ssa_ref(rec: Dict[str, Any], slot_name: str) -> Optional[str]:
        sr = get_slot(rec, slot_name)
        if sr is None:
            return None
        name = sr.get("ssa_name")
        return f"%{name}" if name else None

    def mem_slot_idx(rec: Dict[str, Any], slot_name: str) -> Optional[int]:
        sr = get_slot(rec, slot_name)
        if sr is None:
            return None
        off = sr.get("assigned_offset")
        return off // 8 if off is not None else None

    _ctr: Dict[str, int] = {}

    def tmp(tag: str = "t") -> str:
        _ctr[tag] = _ctr.get(tag, 0) + 1
        return f"%__{tag}_{_ctr[tag]}"

    lines: List[str] = []
    I = "  "

    def il(s: str) -> None:
        lines.append(I + s)

    def lbl(name: str) -> None:
        lines.append(f"{name}:")

    def cm(s: str) -> None:
        il(f"; {s}")

    def asm_force(ssa_name: str, phys: str, val: str) -> None:
        il(f'%{ssa_name} = call i64 asm sideeffect "movq $1, $0", "={{{phys}}},r"(i64 {val})')

    _vpool = pass4_result.get("virtual_reg_pool", [])
    _probe_base_phys = (
        _vpool[_VPOOL_IDX_PROBE_BASE]
        if len(_vpool) > _VPOOL_IDX_PROBE_BASE
        else "r10"
    )

    lines.append(f"define i64 @{func_name}() {{")
    lbl("entry")

    _has_inaddr_load_or_store = any(
        (get_slot(_r, "inaddr") or {}).get("specified") and
        (get_slot(_r, "inaddr") or {}).get("ssa_name")
        for _r in instructions
        if _r.get("concrete_instruction") in LOAD_LIKE + ("store",)
    )

    _stsep_on = bool(stsep_cfg and stsep_cfg.get("enabled"))
    _stsep_pcs: Set[int] = set()
    _stsep_kept: List[int] = []
    if _stsep_on:
        def _phys_of(r: Dict[str, Any], n: str) -> Optional[str]:
            sr = get_slot(r, n)
            return sr.get("physical") if sr and sr.get("specified") else None
        for i_, r in enumerate(instructions):
            if r.get("concrete_instruction") != "store":
                continue
            ia = get_slot(r, "inaddr")
            if not (ia and ia.get("specified") and ia.get("ssa_name") and ia.get("assigned")):
                continue
            om = _phys_of(r, "outmem")
            alias = om is not None and any(
                l.get("concrete_instruction") in LOAD_LIKE and _phys_of(l, "inmem") == om
                and (get_slot(l, "inaddr") or {}).get("specified")
                for l in instructions[i_ + 1:])
            (_stsep_kept.append if alias else _stsep_pcs.add)(r["pc"])
        pass4_result["store_separation"] = {"separated_store_pcs": sorted(_stsep_pcs),
                                            "kept_alloy_alias_store_pcs": _stsep_kept}

    if alloca_n > 0:
        il(f"%mem_base = alloca [{alloca_n} x i64], align 8")
        for i in range(alloca_n):
            gp = tmp("mg")
            il(f"{gp} = getelementptr [{alloca_n} x i64], ptr %mem_base, i64 0, i64 {i}")
            il(f"store volatile i64 0, ptr {gp}, align 8")

    if _stsep_on and _stsep_pcs:
        il(f"%probe_st = alloca [256 x i64], align 64")
        for _pi in range(256):
            _pgp = tmp("pg")
            il(f"{_pgp} = getelementptr [256 x i64], ptr %probe_st, i64 0, i64 {_pi}")
            il(f"store volatile i64 0, ptr {_pgp}, align 8")
    if _has_inaddr_load_or_store:
        il(f"%probe_mem = alloca [256 x i64], align 64")
        for _pi in range(256):
            _pgp = tmp("pg")
            il(f"{_pgp} = getelementptr [256 x i64], ptr %probe_mem, i64 0, i64 {_pi}")
            il(f"store volatile i64 0, ptr {_pgp}, align 8")

    for reg, ssa_name in sorted(ssa_init.items()):
        asm_force(ssa_name, reg, "0")

    il(f'call void asm sideeffect "mfence", "~{{memory}}"()')

    stl_retarget: Dict[int, Dict[str, Any]] = (
        _stl_store_retargets(pass4_result)
        if any(rec.get("stl_annotation") for rec in instructions) else {}
    )

    lc_rec, fnc_rec = commit_boundary(instructions)
    last_committed_pc: Optional[int] = lc_rec["pc"] if lc_rec else None
    first_noncommitted_pc: Optional[int] = fnc_rec["pc"] if fnc_rec else None

    _fpr_on = bool(fpr_cfg and fpr_cfg.get("enabled"))
    _fpr_routes: List[Dict[str, Any]] = []
    if _fpr_on:
        import zlib as _zlib
        _fpr_regs = [int(x) for x in fpr_cfg.get("xmm_regs", list(range(16)))]
        if not _fpr_regs or any(not 0 <= x <= 15 for x in _fpr_regs):
            raise ValueError(f"fpr_cfg.xmm_regs must be a non-empty subset of 0-15: {_fpr_regs}")
        _fpr_loads = fpr_cfg.get("loads", "consumed")
        if _fpr_loads not in ("consumed", "all"):
            raise ValueError(f"fpr_cfg.loads must be 'consumed' or 'all': {_fpr_loads!r}")
        _fpr_forms = list(fpr_cfg.get("forms", ["route"]))
        if not _fpr_forms or any(f not in ("route", "direct", "route_alu", "direct_alu") for f in _fpr_forms):
            raise ValueError(f"fpr_cfg.forms must be a non-empty subset of route/direct/route_alu/direct_alu: {_fpr_forms}")
        _fpr_rng = random.Random(_zlib.crc32(f"fpr:{func_name}".encode()))
        _fpr_consumed: Set[str] = set()
        for _r in instructions:
            for _sl in _r["slots"].values():
                for _sr in _sl:
                    if _sr["slot"] not in ("outreg", "outmem") and _sr.get("ssa_name"):
                        _fpr_consumed.add(_sr["ssa_name"])

    def fpr_route(rec: Dict[str, Any], out_name: str, phys: Optional[str]) -> Tuple[str, str, str]:
        if not _fpr_on or not phys:
            return "$0", "", ""
        if _fpr_loads == "consumed" and out_name not in _fpr_consumed:
            return "$0", "", ""
        k = _fpr_rng.choice(_fpr_regs)
        form = _fpr_rng.choice(_fpr_forms) if len(_fpr_forms) > 1 else _fpr_forms[0]
        if rec.get("xm") and form.startswith("direct"):
            form = "route" + form[len("direct"):]
        ent: Dict[str, Any] = {"pc": rec["pc"], "atom": rec["instruction"],
                               "xmm": k, "outreg": phys, "ssa": out_name}
        if form != "route" or len(_fpr_forms) > 1:
            ent["form"] = form
        direct = form.startswith("direct")
        dst = f"%xmm{k}" if direct else "$0"
        sfx = "" if direct else f"\\0Amovq $0, %xmm{k}"
        clob = f",~{{xmm{k}}}"
        back = k
        if form.endswith("_alu"):
            others = [x for x in _fpr_regs if x != k]
            j = _fpr_rng.choice(others) if others else (k + 1) % 16
            sfx += f"\\0Apxor %xmm{j}, %xmm{j}\\0Apor %xmm{k}, %xmm{j}"
            clob += f",~{{xmm{j}}}"
            ent["alu_xmm"] = j
            back = j
        sfx += f"\\0Amovq $$0, $0\\0Amovq %xmm{back}, $0"
        _fpr_routes.append(ent)
        return dst, sfx, clob

    _fv2_on = bool(fv2_cfg and fv2_cfg.get("enabled"))
    _fv2_rec: Dict[str, Any] = {"splices": [], "fillers": [], "notes": []}
    _ilv_fents: Optional[Dict[str, Dict[str, Any]]] = None
    _fv2_plan_splice: Dict[int, List[Tuple[str, str, str, Dict[str, Any]]]] = {}
    _fv2_plan_fill: Dict[int, int] = {}
    _fv2_cur: Dict[str, str] = dict((reg, ssa) for reg, ssa in ssa_init.items())
    _fv2_dead: List[str] = []
    _vrj: Dict[str, Any] = dict((fv2_cfg or {}).get("vocab_rj") or {}) if _fv2_on else {}
    _rmw_pcs: List[int] = []
    if _fv2_on:
        import zlib as _zlib
        _fv2_rng = random.Random(_zlib.crc32(f"fv2:{func_name}".encode()))
        _sp_cfg = fv2_cfg.get("splice", {})
        _fl_cfg = fv2_cfg.get("fillers", {})
        _sp_ops = list(_sp_cfg.get("ops", list(FV2_SPLICE_OPS)))
        _fl_ops = list(_fl_cfg.get("ops", list(FV2_FILLER_OPS)))
        _ilv_fcfg = fv2_cfg.get("interleave_only") or {}
        if _ilv_fcfg.get("enabled"):
            _ilv_fents = _ilv_select(_ilv_fcfg)
            if not _ilv_fents:
                raise ValueError("fanout_v2.interleave_only: no usable entries after exclude_tags")
            _fl_ops = list(_ilv_fents)
            _fv2_rec["interleave_only"] = {"table": _ilv_fcfg.get("table") or ILV_TABLE_DEFAULT,
                                           "exclude_tags": list(_ilv_fcfg.get("exclude_tags") or []),
                                           "n_ops": len(_fl_ops)}
        for o in _sp_ops:
            if o not in FV2_SPLICE_OPS: raise ValueError(f"fv2 splice op {o!r} not in FV2_SPLICE_OPS")
        for o in ([] if _ilv_fents else _fl_ops):
            if o not in FV2_FILLER_OPS: raise ValueError(f"fv2 filler op {o!r} not in FV2_FILLER_OPS")
        if _vrj.get("jmp") and FV2_FILLER_JMP not in _fl_ops:
            _fl_ops.append(FV2_FILLER_JMP)
        _pre_ok = bool(fv2_cfg.get("pre_window_reads", False))
        _unres = [r["pc"] for r in instructions
                  if (r.get("branch_annotations") or {}).get("mode", "").startswith("mispredict")]
        _win_pc = min(_unres) if _unres else None
        def _in_window(p: int) -> bool:
            return _pre_ok or (_win_pc is not None and p > _win_pc)
        _prod: Dict[str, Dict[str, Any]] = {}
        for r in instructions:
            if r.get("synthetic"):
                continue
            o = get_slot(r, "outreg")
            if o and o.get("specified") and o.get("ssa_name"):
                _prod[o["ssa_name"]] = r
        _xm = next((r for r in instructions if r.get("xm")), None)
        _xm_slot = None
        if _xm is not None:
            _xm_slot = "inaddr" if _xm.get("concrete_instruction") in LOAD_LIKE + ("store",) else "inreg0"
        _p_x = float(_sp_cfg.get("p_xmit", 0.75)); _p_o = float(_sp_cfg.get("p_other", 0.25))
        if _sp_cfg.get("enabled", True):
            for r in instructions:
                if r.get("synthetic"):
                    continue
                for sn in ("inaddr", "inreg0", "inreg1"):
                    sr = get_slot(r, sn)
                    if not (sr and sr.get("specified") and sr.get("ssa_name") and sr.get("assigned")):
                        continue
                    pr = _prod.get(sr["ssa_name"])
                    if pr is None or pr is r:
                        continue
                    is_x = (r is _xm and sn == _xm_slot)
                    if _fv2_rng.random() >= (_p_x if is_x else _p_o):
                        continue
                    if not _in_window(r["pc"]):
                        _fv2_rec["notes"].append(f"skip pre-window splice pc{r['pc']}.{sn}")
                        continue
                    op = _fv2_rng.choice(_sp_ops)
                    _fv2_plan_splice.setdefault(r["pc"], []).append(
                        (sn, sr["ssa_name"], sr["assigned"],
                         {"consumer_pc": r["pc"], "slot": sn, "reg": sr["assigned"],
                          "producer_pc": pr["pc"], "op": op, "xmit_edge": is_x}))
        _used: Set[str] = set(locked_registers.values()) | set(ssa_init)
        _used |= set((pass4_result.get("virtual_reg_pool") or [])[:_VPOOL_FREE_START])
        for r in instructions:
            for sl in r["slots"].values():
                for sr in sl:
                    if sr.get("assigned"):
                        _used.add(sr["assigned"])
        _fv2_dead = [x for x in X86_64_CALLER_SAVED if x not in _used and x not in ("rax", "rcx", "rdx")]
        _otb_cfg = fv2_cfg.get("otb", {})
        if _otb_cfg.get("enabled") and _xm is not None and _fv2_rng.random() < float(_otb_cfg.get("p", 1.0)):
            xs = get_slot(_xm, _xm_slot) if _xm_slot else None
            pr = _prod.get(xs["ssa_name"]) if xs and xs.get("specified") and xs.get("ssa_name") else None
            why = None
            if pr is None or not xs.get("assigned"):
                why = "transmitter leak operand has no Alloy producer"
            elif _win_pc is None or pr["pc"] <= _win_pc:
                why = "producer is not under the unresolved branch"
            else:
                brr = [r["pc"] for r in instructions if r.get("branch_annotations")
                       and not r["branch_annotations"].get("mode", "").startswith("mispredict")
                       and r["pc"] < _win_pc]
                if not brr:
                    why = "no resolved Alloy branch before the unresolved branch"
                elif not _fv2_dead:
                    why = "no unused register for L2"
            if why:
                _fv2_rec["otb"] = {"applied": False, "why": why}
            else:
                t2 = _fv2_dead.pop(_fv2_rng.randrange(len(_fv2_dead)))
                after_pc = max(brr)
                nxt = next(r["pc"] for r in instructions if r["pc"] > after_pc)
                _fv2_rec["otb"] = {"applied": True, "br_r_pc": after_pc, "br_u_pc": _win_pc,
                                   "l2_before_pc": nxt, "l2_reg": t2, "merge_reg": xs["assigned"],
                                   "producer_pc": pr["pc"], "xmit_pc": _xm["pc"], "slot": _xm_slot}
                pl = _fv2_plan_splice.get(_xm["pc"], [])
                _fv2_plan_splice[_xm["pc"]] = [x for x in pl if x[0] != _xm_slot]
        if _fl_cfg.get("enabled", True):
            lo, hi = (list(_fl_cfg.get("count", [1, 3])) + [3])[:2]
            n_fill = _fv2_rng.randint(int(lo), int(hi))
            cands = [r["pc"] for r in instructions if _in_window(r["pc"])]
            if not _fv2_dead:
                if n_fill: _fv2_rec["notes"].append("no dead register: fillers skipped")
            elif cands:
                for _ in range(n_fill):
                    p_ = _fv2_rng.choice(cands)
                    _fv2_plan_fill[p_] = _fv2_plan_fill.get(p_, 0) + 1

    _otb = _fv2_rec.get("otb") if _fv2_on else None
    if _otb and _otb.get("applied"):
        il(f"%otb_mem = alloca [8 x i64], align 64")
        for _pi in range(8):
            _pgp = tmp("pg")
            il(f"{_pgp} = getelementptr [8 x i64], ptr %otb_mem, i64 0, i64 {_pi}")
            il(f"store volatile i64 0, ptr {_pgp}, align 8")
        il(f'call void asm sideeffect "mfence", "~{{memory}}"()')
    _otb_l2: List[str] = []

    _fv2_n = [0]
    _fv2_ren: Dict[str, str] = {}
    _fv2_ren_ent: Dict[str, Dict[str, Any]] = {}
    def fv2_before(rec: Dict[str, Any]) -> Dict[str, Any]:
        if not _fv2_on:
            return rec
        pc_ = rec["pc"]
        for _ in range(_fv2_plan_fill.get(pc_, 0)):
            live = sorted(_fv2_cur.items())
            if not live:
                break
            op = _fv2_rng.choice(_fl_ops)
            if _ilv_fents is not None:
                ie = _ilv_fents[op]
                if ie.get("form", "rr") == "none":
                    il(f'call void asm sideeffect "{ie["asm"]}", ""()')
                    _fv2_rec["fillers"].append({"before_pc": pc_, "op": op})
                    continue
                srcs = [_fv2_rng.choice(live) for _ in range(2)]
                d = _fv2_rng.choice(_fv2_dead)
                _fv2_n[0] += 1
                xclob = "".join(f",~{{{x}}}" for x in ie.get("clobbers", []))
                il(f'%__fill_{_fv2_n[0]} = call i64 asm sideeffect "{ie["asm"]}", '
                   f'"=&{{{d}}},{{{srcs[0][0]}}},{{{srcs[1][0]}}},~{{flags}}{xclob}"'
                   f'(i64 %{srcs[0][1]}, i64 %{srcs[1][1]})')
                _fv2_rec["fillers"].append({"before_pc": pc_, "op": op, "dst": d,
                                            "srcs": [srcs[0][0], srcs[1][0]]})
                continue
            if op == FV2_FILLER_JMP:
                il(f'call void asm sideeffect "jmp .Lsimspect_jf${{:uid}}\\0A.Lsimspect_jf${{:uid}}:", ""()')
                _fv2_rec["fillers"].append({"before_pc": pc_, "op": op})
                continue
            srcs = [_fv2_rng.choice(live) for _ in range(2)]
            d = _fv2_rng.choice(_fv2_dead)
            _fv2_n[0] += 1
            body = FV2_FILLER_OPS[op]
            il(f'%__fill_{_fv2_n[0]} = call i64 asm sideeffect "{body}", '
               f'"=&{{{d}}},{{{srcs[0][0]}}},{{{srcs[1][0]}}},~{{flags}}"'
               f'(i64 %{srcs[0][1]}, i64 %{srcs[1][1]})')
            _fv2_rec["fillers"].append({"before_pc": pc_, "op": op, "dst": d,
                                        "srcs": [srcs[0][0], srcs[1][0]]})
        if _otb and _otb.get("applied"):
            if pc_ == _otb["l2_before_pc"]:
                il(f'%__otb_l2 = call i64 asm sideeffect "movq 0($1), $0", '
                   f'"=&{{{_otb["l2_reg"]}}},{{{_probe_base_phys}}},~{{memory}}"(ptr %otb_mem)')
                _otb_l2.append("%__otb_l2")
            if pc_ == _otb["xmit_pc"] and _otb_l2:
                xs_ = get_slot(rec, _otb["slot"])
                old_ = _fv2_ren.get(xs_["ssa_name"], xs_["ssa_name"])
                new_ = f"{xs_['ssa_name']}__otb"
                il(f'%{new_} = call i64 asm sideeffect "xorq $2, $0\\0Axorq $2, $0", '
                   f'"={{{_otb["merge_reg"]}}},0,{{{_otb["l2_reg"]}}},~{{flags}}"(i64 %{old_}, i64 {_otb_l2[0]})')
                _fv2_ren[xs_["ssa_name"]] = new_
                _fv2_ren_ent[xs_["ssa_name"]] = _otb
        plan = _fv2_plan_splice.get(pc_)
        later = [(sr["slot"], sr["ssa_name"]) for sl in rec["slots"].values() for sr in sl
                 if sr["slot"] not in ("outreg", "outmem") and sr.get("ssa_name") in _fv2_ren]
        if not plan and not later:
            return rec
        import copy as _copy
        rec = _copy.deepcopy(rec)
        for sl in rec["slots"].values():
            for sr in sl:
                if sr["slot"] not in ("outreg", "outmem") and sr.get("ssa_name") in _fv2_ren:
                    old_ = sr["ssa_name"]
                    sr["ssa_name"] = _fv2_ren[old_]
                    _fv2_ren_ent[old_].setdefault("later_readers", []).append(f"pc{pc_}.{sr['slot']}")
        if not plan:
            return rec
        done: Dict[str, str] = {}
        for sn, ssa, phys, ent in plan:
            if ssa not in done:
                _fv2_n[0] += 1
                new = f"{ssa}__sp{_fv2_n[0]}"
                il(f'%{new} = call i64 asm sideeffect "{FV2_SPLICE_OPS[ent["op"]]}", '
                   f'"={{{phys}}},0,~{{flags}}"(i64 %{ssa})')
                done[ssa] = new
                _fv2_ren[ssa] = new
                _fv2_ren_ent[ssa] = ent
            else:
                ent = dict(ent, shared_with_previous=True)
            for sl in rec["slots"].values():
                for sr in sl:
                    if sr["slot"] == sn and sr.get("ssa_name") == ssa:
                        sr["ssa_name"] = done[ssa]
            _fv2_rec["splices"].append(ent)
        return rec

    def fv2_after(rec: Dict[str, Any]) -> None:
        if not _fv2_on:
            return
        if rec.get("concrete_instruction") == VOCAB_RJ_RMW["name"]:
            return
        o = get_slot(rec, "outreg")
        if o and o.get("ssa_name") and o.get("assigned"):
            _fv2_cur[o["assigned"]] = o["ssa_name"]

    _br_cmp = bool(BRANCH_FORMS.get("br_cmp"))
    _jmp_p = float(BRANCH_FORMS.get("jmp_direct", 0) or 0)
    _bc_alloy = bool(brcond_cfg and brcond_cfg.get("from_alloy"))
    _jmp_pcs: List[int] = []
    _bc_pcs: List[int] = []
    if _jmp_p > 0:
        import zlib as _zlib2
        _jrng = random.Random(_zlib2.crc32(f"jmp:{func_name}".encode()))
        for r in instructions:
            ba_ = r.get("branch_annotations")
            if (ba_ and ba_.get("mode") == "correctly_not_taken" and not r.get("xm")
                    and r.get("concrete_instruction") in ("br_cond", "br_uncond")
                    and _jrng.random() < _jmp_p):
                _jmp_pcs.append(r["pc"])
    _br_uni = list(BRANCH_FORMS.get("uniform") or [])
    _cmp_pcs: Set[int] = set()
    if _br_uni:
        import zlib as _zlib3
        _brng = random.Random(_zlib3.crc32(f"brf:{func_name}".encode()))
        for r in instructions:
            ba_ = r.get("branch_annotations")
            c_ = r.get("concrete_instruction")
            if not ba_ or c_ not in ("br_cond", "br_uncond", "br_bez"):
                continue
            jmp_ok = (ba_.get("mode") == "correctly_not_taken" and not r.get("xm")
                      and c_ in ("br_cond", "br_uncond"))
            elig = [f for f in _br_uni if f in ("test", "cmp") or (f == "jmp" and jmp_ok)]
            if not elig:
                continue
            f_ = _brng.choice(elig)
            if f_ == "jmp":
                _jmp_pcs.append(r["pc"])
            elif f_ == "cmp":
                _cmp_pcs.add(r["pc"])

    _fv4_forms: Dict[str, str] = {}

    def br_on(cond_raw: str, cond_i1: str, taken_lbl: str, ft_lbl: str, taken_if_zero: bool) -> None:
        if not (_br_cmp or pc in _cmp_pcs):
            il(f"br i1 {cond_i1}, label %{taken_lbl}, label %{ft_lbl}")
            return
        jcc = "jb" if taken_if_zero else "jae"
        il(f'callbr void asm sideeffect "cmpq $$1, $0\\0A{jcc} ${{1:l}}", "r,!i,~{{flags}}"'
           f'(i64 {cond_raw}) to label %{ft_lbl} [label %{taken_lbl}]')

    last_was_terminator = False
    safe_name = func_name.replace("-", "_").replace(".", "_")
    _fv2_prev: Optional[Dict[str, Any]] = None

    for rec in instructions:
        pc = rec["pc"]
        concrete = rec.get("concrete_instruction")
        atom = rec["instruction"]

        if pc in new_block_pcs:
            if not last_was_terminator:
                il(f"br label %bb_{pc}")
            lbl(f"bb_{pc}")
            last_was_terminator = False

        if _fv2_on:
            if _fv2_prev is not None:
                fv2_after(_fv2_prev)
            rec = fv2_before(rec)
            _fv2_prev = rec
        cm(f"pc={pc}  {atom}  ({concrete})")
        if rec.get("vocab_form"):
            cm(f"fv4 form: {rec['vocab_form']}")
            _fv4_forms[str(pc)] = rec["vocab_form"]
        marker = f"__litmus_{safe_name}_pc{pc}"
        mkr = f".globl {marker}\\0A{marker}:\\0A"
        if pc == last_committed_pc:
            cb = f"__litmus_{safe_name}_last_committed"
            mkr += f".globl {cb}\\0A{cb}:\\0A"
        if pc == first_noncommitted_pc:
            cb = f"__litmus_{safe_name}_first_noncommitted"
            mkr += f".globl {cb}\\0A{cb}:\\0A"

        last_was_terminator = False

        if concrete == "load":
            _swp = rec.get("vocab_form") == "load_swapidx"
            inaddr_sr = get_slot(rec, "inaddr")
            _ia_specified = inaddr_sr and inaddr_sr.get("specified")
            inaddr_ssa  = inaddr_sr.get("ssa_name") if _ia_specified else None
            inaddr_phys = inaddr_sr.get("assigned") if _ia_specified else None
            outreg_sr = get_slot(rec, "outreg")
            if inaddr_ssa and inaddr_phys:
                if outreg_sr and outreg_sr.get("ssa_name"):
                    out_name = outreg_sr["ssa_name"]
                    phys = outreg_sr.get("assigned")
                    fdst, fsx, fcl = fpr_route(rec, out_name, phys)
                    il(f'%{out_name} = call i64 asm sideeffect '
                       f'"{mkr}movq {"($2, $1, 1)" if _swp else "($1, $2, 1)"}, {fdst}{fsx}", '
                       f'"=&{{{phys}}},{{{_probe_base_phys}}},{{{inaddr_phys}}},~{{memory}}{fcl}"'
                       f'(ptr %probe_mem, i64 %{inaddr_ssa})')
                else:
                    il(f'call void asm sideeffect '
                       f'"{mkr}movq {"($1, $0, 1)" if _swp else "($0, $1, 1)"}, %%rax", '
                       f'"{{{_probe_base_phys}}},{{{inaddr_phys}}},~{{memory}},~{{rax}}"'
                       f'(ptr %probe_mem, i64 %{inaddr_ssa})')
            else:
                idx = mem_slot_idx(rec, "inmem")
                if idx is None or alloca_n == 0:
                    il(f'call void asm sideeffect ".globl {marker}\\0A{marker}:", ""()')
                    cm(f"WARNING: load {atom} missing inmem offset — skipped")
                    continue
                offset = idx * 8
                if outreg_sr and outreg_sr.get("ssa_name"):
                    out_name = outreg_sr["ssa_name"]
                    phys = outreg_sr.get("assigned")
                    fdst, fsx, fcl = fpr_route(rec, out_name, phys)
                    il(f'%{out_name} = call i64 asm sideeffect '
                       f'"{mkr}movq {offset}({",$1,1" if _swp else "$1"}), {fdst}{fsx}", '
                       f'"=&{{{phys}}},{{{_probe_base_phys}}},~{{memory}}{fcl}"(ptr %mem_base)')
                else:
                    il(f'call void asm sideeffect '
                       f'"{mkr}movq {offset}({",$0,1" if _swp else "$0"}), %rax", '
                       f'"{{{_probe_base_phys}}},~{{memory}},~{{rax}}"(ptr %mem_base)')

        elif concrete == VOCAB_RJ_RMW["name"]:
            inaddr_sr = get_slot(rec, "inaddr")
            _ia_specified = inaddr_sr and inaddr_sr.get("specified")
            inaddr_ssa  = inaddr_sr.get("ssa_name") if _ia_specified else None
            inaddr_phys = inaddr_sr.get("assigned") if _ia_specified else None
            if inaddr_ssa and inaddr_phys:
                il(f'call void asm sideeffect '
                   f'"{mkr}orq $$0, ($0, $1, 1)", '
                   f'"{{{_probe_base_phys}}},{{{inaddr_phys}}},~{{memory}},~{{flags}}"'
                   f'(ptr %probe_mem, i64 %{inaddr_ssa})')
            else:
                idx = mem_slot_idx(rec, "inmem")
                if idx is None or alloca_n == 0:
                    il(f'call void asm sideeffect ".globl {marker}\\0A{marker}:", ""()')
                    cm(f"WARNING: load_rmw_or0 {atom} missing inmem offset — skipped")
                    continue
                il(f'call void asm sideeffect '
                   f'"{mkr}orq $$0, {idx * 8}($0)", '
                   f'"{{{_probe_base_phys}}},~{{memory}},~{{flags}}"(ptr %mem_base)')
            _rmw_pcs.append(pc)

        elif concrete == "store" and pc in stl_retarget:
            rt = stl_retarget[pc]
            base_ptr = "%probe_mem" if rt["space"] == "probe" else "%mem_base"
            disp = rt["disp"]
            cm(f"stl_bypass store: re-targeted to {rt['space']}+{disp}"
               + (f" + {rt['index_ssa']}" if rt["index_ssa"] else ""))
            inaddr_sr = get_slot(rec, "inaddr")
            inaddr_phys = inaddr_sr.get("assigned") if inaddr_sr else None
            inreg0_sr = get_slot(rec, "inreg0")
            has_src = bool(inreg0_sr and inreg0_sr.get("ssa_name")) and not _fv4_store_imm(rec)
            _swp = rec.get("vocab_form") == "store_swapidx"
            ops: List[str] = []
            cons: List[str] = []
            if has_src:
                phys_src = inreg0_sr.get("assigned")
                ops.append(f'i64 %{inreg0_sr["ssa_name"]}')
                cons.append(f'{{{phys_src}}}' if phys_src else 'r')
            ops.append(f"ptr {base_ptr}")
            cons.append(f"{{{_probe_base_phys}}}")
            if rt["index_ssa"]:
                ops.append(f'i64 %{rt["index_ssa"]}')
                cons.append(f"{{{inaddr_phys}}}")
            n = len(ops)
            src_txt = "$0" if has_src else "$$0"
            b = n - (2 if rt["index_ssa"] else 1)
            addr_txt = (f"{disp}(${b}, ${b + 1}, 1)" if rt["index_ssa"] else f"{disp}(${b})")
            if _swp:
                addr_txt = (f"{disp}(${b + 1}, ${b}, 1)" if rt["index_ssa"] else f"{disp}(,${b},1)")
            il(f'call void asm sideeffect '
               f'"{mkr}movq {src_txt}, {addr_txt}", '
               f'"{",".join(cons)},~{{memory}}"({", ".join(ops)})')

        elif concrete == "store":
            inaddr_sr = get_slot(rec, "inaddr")
            _ia_specified = inaddr_sr and inaddr_sr.get("specified")
            inaddr_ssa  = inaddr_sr.get("ssa_name") if _ia_specified else None
            inaddr_phys = inaddr_sr.get("assigned") if _ia_specified else None
            inreg0_sr = get_slot(rec, "inreg0")
            if _fv4_store_imm(rec):
                inreg0_sr = None
            _swp = rec.get("vocab_form") == "store_swapidx"
            _st_base = "%probe_st" if pc in _stsep_pcs else "%probe_mem"
            if inaddr_ssa and inaddr_phys:
                if inreg0_sr and inreg0_sr.get("ssa_name"):
                    src_ssa = f'%{inreg0_sr["ssa_name"]}'
                    phys_src = inreg0_sr.get("assigned")
                    in_con = f'{{{phys_src}}}' if phys_src else 'r'
                    il(f'call void asm sideeffect '
                       f'"{mkr}movq $0, {"($2, $1, 1)" if _swp else "($1, $2, 1)"}", '
                       f'"{in_con},{{{_probe_base_phys}}},{{{inaddr_phys}}},~{{memory}}"'
                       f'(i64 {src_ssa}, ptr {_st_base}, i64 %{inaddr_ssa})')
                else:
                    il(f'call void asm sideeffect '
                       f'"{mkr}movq $$0, {"($1, $0, 1)" if _swp else "($0, $1, 1)"}", '
                       f'"{{{_probe_base_phys}}},{{{inaddr_phys}}},~{{memory}}"'
                       f'(ptr {_st_base}, i64 %{inaddr_ssa})')
            else:
                idx = mem_slot_idx(rec, "outmem")
                if idx is None or alloca_n == 0:
                    il(f'call void asm sideeffect ".globl {marker}\\0A{marker}:", ""()')
                    cm(f"WARNING: store {atom} missing outmem offset — skipped")
                    continue
                offset = idx * 8
                if inreg0_sr and inreg0_sr.get("ssa_name"):
                    src_ssa = f'%{inreg0_sr["ssa_name"]}'
                    phys_src = inreg0_sr.get("assigned")
                    in_con = f'{{{phys_src}}}' if phys_src else 'r'
                    il(f'call void asm sideeffect '
                       f'"{mkr}movq $0, {offset}({",$1,1" if _swp else "$1"})", '
                       f'"{in_con},{{{_probe_base_phys}}},~{{memory}}"(i64 {src_ssa}, ptr %mem_base)')
                else:
                    il(f'call void asm sideeffect '
                       f'"{mkr}movq $$0, {offset}({",$0,1" if _swp else "$0"})", '
                       f'"{{{_probe_base_phys}}},~{{memory}}"(ptr %mem_base)')

        elif concrete.startswith(ILV_PREFIX):
            ie = _ilv_entry(concrete[len(ILV_PREFIX):])
            cons, ins, phys = [], [], []
            for sn in (("inreg0", "inreg1") if _ilv_refs(ie["asm"], 2) else ("inreg0",)):
                sr_ = get_slot(rec, sn)
                ph_ = sr_.get("assigned") if sr_ else None
                ins.append(f"i64 {ssa_ref(rec, sn) or '0'}")
                cons.append(f'{{{ph_}}}' if ph_ else 'r')
                phys.append(ph_)
            xclob = "".join(f",~{{{x}}}" for x in ie.get("clobbers", []))
            outreg_sr = get_slot(rec, "outreg")
            phys_out = outreg_sr.get("assigned") if outreg_sr else None
            ec = "=" if (phys_out and phys_out in phys) else "=&"
            out_con = f'{ec}{{{phys_out}}}' if phys_out else f'{ec}r'
            out_name = (outreg_sr.get("ssa_name") if outreg_sr else None) or f"__ilv_dead_{pc}"
            il(f'%{out_name} = call i64 asm sideeffect "{mkr}{ie["asm"]}", '
               f'"{out_con},{",".join(cons)},~{{flags}}{xclob}"({", ".join(ins)})')

        elif concrete == "bitnot":
            inreg0 = ssa_ref(rec, "inreg0") or "0"
            inreg0_sr = get_slot(rec, "inreg0")
            phys_in = inreg0_sr.get("assigned") if inreg0_sr else None
            outreg_sr = get_slot(rec, "outreg")
            if outreg_sr and outreg_sr.get("ssa_name"):
                out_name = outreg_sr["ssa_name"]
                phys_out = outreg_sr.get("assigned")
                if phys_in and phys_in == phys_out:
                    il(f'%{out_name} = call i64 asm sideeffect '
                       f'"{mkr}notq $0", '
                       f'"=&{{{phys_out}}},0,~{{flags}}"(i64 {inreg0})')
                else:
                    in_con = f'{{{phys_in}}}' if phys_in else 'r'
                    il(f'%{out_name} = call i64 asm sideeffect '
                       f'"{mkr}movq $1, $0\\0Anotq $0", '
                       f'"=&{{{phys_out}}},{in_con},~{{flags}}"(i64 {inreg0})')
            else:
                in_con = f'{{{phys_in}}}' if phys_in else 'r'
                il(f'call void asm sideeffect '
                   f'"{mkr}notq $0", '
                   f'"{in_con},~{{flags}}"(i64 {inreg0})')

        elif concrete == "add":
            inreg0 = ssa_ref(rec, "inreg0") or "0"
            inreg1 = ssa_ref(rec, "inreg1") or "0"
            inreg0_sr = get_slot(rec, "inreg0")
            inreg1_sr = get_slot(rec, "inreg1")
            phys_in0 = inreg0_sr.get("assigned") if inreg0_sr else None
            phys_in1 = inreg1_sr.get("assigned") if inreg1_sr else None
            outreg_sr = get_slot(rec, "outreg")
            if outreg_sr and outreg_sr.get("ssa_name"):
                out_name = outreg_sr["ssa_name"]
                phys_out = outreg_sr.get("assigned")
                in0_con = f'{{{phys_in0}}}' if phys_in0 else 'r'
                in1_con = f'{{{phys_in1}}}' if phys_in1 else 'r'
                il(f'%{out_name} = call i64 asm sideeffect '
                   f'"{mkr}leaq ($1, $2), $0", '
                   f'"=&{{{phys_out}}},{in0_con},{in1_con}"(i64 {inreg0}, i64 {inreg1})')
            else:
                in0_con = f'{{{phys_in0}}}' if phys_in0 else 'r'
                in1_con = f'{{{phys_in1}}}' if phys_in1 else 'r'
                il(f'call void asm sideeffect '
                   f'"{mkr}leaq ($0, $1), %rax", '
                   f'"{in0_con},{in1_con},~{{rax}}"(i64 {inreg0}, i64 {inreg1})')

        elif concrete in ("inc", "cmov_rr"):
            inreg0 = ssa_ref(rec, "inreg0") or "0"
            inreg0_sr = get_slot(rec, "inreg0")
            phys_in0 = inreg0_sr.get("assigned") if inreg0_sr else None
            in0_con = f'{{{phys_in0}}}' if phys_in0 else 'r'
            outreg_sr = get_slot(rec, "outreg")
            has_out = bool(outreg_sr and outreg_sr.get("ssa_name"))
            dst = "$0" if has_out else "%rax"
            k = 1 if has_out else 0
            if concrete == "inc":
                body = f"movq ${k}, {dst}\\0Aincq {dst}"
                ins = [f"i64 {inreg0}"]; cons = [in0_con]
            else:
                inreg1 = ssa_ref(rec, "inreg1") or "0"
                inreg1_sr = get_slot(rec, "inreg1")
                phys_in1 = inreg1_sr.get("assigned") if inreg1_sr else None
                body = (f"movq ${k}, {dst}\\0Acmpq ${k}, ${k}\\0Acmovneq ${k + 1}, {dst}")
                ins = [f"i64 {inreg0}", f"i64 {inreg1}"]
                cons = [in0_con, f'{{{phys_in1}}}' if phys_in1 else 'r']
            if has_out:
                out_name = outreg_sr["ssa_name"]; phys_out = outreg_sr.get("assigned")
                il(f'%{out_name} = call i64 asm sideeffect "{mkr}{body}", '
                   f'"=&{{{phys_out}}},{",".join(cons)},~{{flags}}"({", ".join(ins)})')
            else:
                il(f'call void asm sideeffect "{mkr}{body}", '
                   f'"{",".join(cons)},~{{rax}},~{{flags}}"({", ".join(ins)})')

        elif concrete in FV4_ALU_UNARY or concrete in FV4_ALU_BINARY:
            eff = _fv4_alu_effective(rec)
            if eff != concrete:
                cm(f"fv4 {concrete}: same-register inputs, emitted as {eff} (no zero idiom)")
            binary = eff in FV4_ALU_BINARY
            ops_in, phys_in, cons_in = [], [], []
            for sn in (("inreg0", "inreg1") if binary else ("inreg0",)):
                sr_ = get_slot(rec, sn)
                ph_ = sr_.get("assigned") if sr_ else None
                ops_in.append(ssa_ref(rec, sn) or "0")
                phys_in.append(ph_)
                cons_in.append(f'{{{ph_}}}' if ph_ else 'r')
            outreg_sr = get_slot(rec, "outreg")
            has_out = bool(outreg_sr and outreg_sr.get("ssa_name"))
            phys_out = outreg_sr.get("assigned") if has_out else None

            def _alu(dst: str, a: str, b: Optional[str]) -> str:
                if not binary:
                    op = FV4_ALU_UNARY[eff]
                    cp = "" if a == dst else f"movq {a}, {dst}"
                    if op is None:
                        return cp or f"movq {a}, {dst}"
                    return (cp + "\\0A" if cp else "") + f"{op} {dst}"
                if eff == "lea_s8":
                    return f"leaq ({a}, {b}, 8), {dst}"
                cp = "" if a == dst else f"movq {a}, {dst}\\0A"
                return cp + f"{FV4_ALU_BINARY[eff]} {b}, {dst}"

            if has_out:
                out_name = outreg_sr["ssa_name"]
                p0 = phys_in[0]
                p1 = phys_in[1] if binary else None
                if binary and p0 and p0 == p1:
                    if p0 == phys_out:
                        body, cons, ins = _alu("$0", "$0", "$0"), f"={{{phys_out}}},0", [ops_in[0]]
                    else:
                        body, cons, ins = _alu("$0", "$1", "$1"), f"=&{{{phys_out}}},{cons_in[0]}", [ops_in[0]]
                elif p0 and p0 == phys_out:
                    body = _alu("$0", "$0", "$2" if binary else None)
                    cons = f"={{{phys_out}}},0" + (f",{cons_in[1]}" if binary else "")
                    ins = ops_in
                elif binary and p1 and p1 == phys_out:
                    if eff == "lea_s8":
                        body = "leaq ($1, $0, 8), $0"
                    elif eff in _FV4_COMMUTATIVE:
                        body = f"{FV4_ALU_BINARY[eff]} $1, $0"
                    else:
                        body = "negq $0\\0Aaddq $1, $0"
                    cons, ins = f"={{{phys_out}}},{cons_in[0]},0", ops_in
                else:
                    body = _alu("$0", "$1", "$2" if binary else None)
                    cons, ins = f"=&{{{phys_out}}}," + ",".join(cons_in), ops_in
                args = ", ".join(f"i64 {x}" for x in ins)
                il(f'%{out_name} = call i64 asm sideeffect "{mkr}{body}", '
                   f'"{cons},~{{flags}}"({args})')
            else:
                body = _alu("%rax", "$0", "$1" if binary else None)
                args = ", ".join(f"i64 {x}" for x in ops_in)
                il(f'call void asm sideeffect "{mkr}{body}", '
                   f'"{",".join(cons_in)},~{{rax}},~{{flags}}"({args})')

        elif concrete == "zsm":
            inreg0 = ssa_ref(rec, "inreg0") or "0"
            inreg1 = ssa_ref(rec, "inreg1") or "0"
            inreg0_sr = get_slot(rec, "inreg0")
            inreg1_sr = get_slot(rec, "inreg1")
            phys_in0 = inreg0_sr.get("assigned") if inreg0_sr else None
            phys_in1 = inreg1_sr.get("assigned") if inreg1_sr else None
            outreg_sr = get_slot(rec, "outreg")
            if outreg_sr and outreg_sr.get("ssa_name"):
                out_name = outreg_sr["ssa_name"]
                phys_out = outreg_sr.get("assigned")
                in0_con = f'{{{phys_in0}}}' if phys_in0 else 'r'
                in1_con = f'{{{phys_in1}}}' if phys_in1 else 'r'
                il(f'%{out_name} = call i64 asm sideeffect '
                   f'"{mkr}movq $1, $0\\0Aimulq $2, $0", '
                   f'"=&{{{phys_out}}},{in0_con},{in1_con},~{{flags}}"'
                   f'(i64 {inreg0}, i64 {inreg1})')
            else:
                in0_con = f'{{{phys_in0}}}' if phys_in0 else 'r'
                in1_con = f'{{{phys_in1}}}' if phys_in1 else 'r'
                il(f'call void asm sideeffect '
                   f'"{mkr}movq $0, %rax\\0Aimulq $1, %rax", '
                   f'"{in0_con},{in1_con},~{{rax}},~{{flags}}"'
                   f'(i64 {inreg0}, i64 {inreg1})')

        elif concrete == "div":
            is_xm      = rec.get("xm", False)
            inreg0     = ssa_ref(rec, "inreg0") or "0"
            inreg1     = ssa_ref(rec, "inreg1") or "0"
            inreg0_sr  = get_slot(rec, "inreg0")
            inreg1_sr  = get_slot(rec, "inreg1")
            phys_in0   = inreg0_sr.get("assigned") if inreg0_sr else None
            phys_in1   = inreg1_sr.get("assigned") if inreg1_sr else None
            in0_con    = f'{{{phys_in0}}}' if phys_in0 else 'r'
            in1_con    = f'{{{phys_in1}}}' if phys_in1 else 'r'
            outreg_sr  = get_slot(rec, "outreg")
            has_outreg = bool(outreg_sr and outreg_sr.get("ssa_name"))
            divisor_in = "$2" if has_outreg else "$1"

            if is_xm:
                divisor_setup = ""
                divisor_op    = divisor_in
                extra_clobber = ""
            else:
                divisor_setup = f"movq {divisor_in}, %rcx\\0Aorq $$1, %rcx\\0A"
                divisor_op    = "%rcx"
                extra_clobber = "~{rcx},"

            if has_outreg:
                out_name = outreg_sr["ssa_name"]
                phys_out = outreg_sr.get("assigned")
                il(f'%{out_name} = call i64 asm sideeffect '
                   f'"{mkr}movq $1, %rax\\0A{divisor_setup}cqo\\0Aidivq {divisor_op}\\0A'
                   f'movq %rax, $0", '
                   f'"=&{{{phys_out}}},{in0_con},{in1_con},'
                   f'~{{rax}},{extra_clobber}~{{rdx}},~{{flags}}"'
                   f'(i64 {inreg0}, i64 {inreg1})')
            else:
                il(f'call void asm sideeffect '
                   f'"{mkr}movq $0, %rax\\0A{divisor_setup}cqo\\0Aidivq {divisor_op}", '
                   f'"{in0_con},{in1_con},~{{rax}},{extra_clobber}~{{rdx}},~{{flags}}"'
                   f'(i64 {inreg0}, i64 {inreg1})')

        elif concrete == "br_bez":
            ba = rec.get("branch_annotations")
            if ba:
                taken = ba["taken_target"]
                ft    = ba["fallthrough_target"]
                cm(f"BEZ xmit branch: BTB predicts={ba['btb_prediction']}")
                inreg0    = ssa_ref(rec, "inreg0")
                inreg0_sr = get_slot(rec, "inreg0")
                phys_in0  = inreg0_sr.get("assigned") if inreg0_sr else None
                cond_raw  = tmp("bez_raw")
                if inreg0 is not None and phys_in0 is not None:
                    il(f'{cond_raw} = call i64 asm sideeffect '
                       f'"{mkr}movq $1, $0", '
                       f'"=&r,{{{phys_in0}}}"(i64 {inreg0})')
                else:
                    vpool = pass4_result.get("virtual_reg_pool", [])
                    cond_reg = vpool[1] if len(vpool) > 1 else "r11"
                    il(f'{cond_raw} = call i64 asm sideeffect '
                       f'"{mkr}xorq $0, $0", '
                       f'"=&{{{cond_reg}}}"()')
                bez_i1 = tmp("bez_i1")
                il(f"{bez_i1} = icmp eq i64 {cond_raw}, 0")
                br_on(cond_raw, bez_i1, taken, ft, True)
                last_was_terminator = True
            else:
                il(f'call void asm sideeffect "{mkr}", ""()')
                cm(f"resolved branch {atom} — skipped")

        elif concrete == "nop":
            il(f'call void asm sideeffect "{mkr}nop", ""()')

        elif concrete in ("br_cond", "br_uncond") and pc in _jmp_pcs:
            ba = rec["branch_annotations"]
            ft = ba["fallthrough_target"]
            jd = f"jmpdead_{pc}"
            il(f'callbr void asm sideeffect "{mkr}jmp ${{0:l}}", "!i"() to label %{jd} [label %{ft}]')
            lbl(jd)
            il("unreachable")
            last_was_terminator = True

        elif concrete in ("br_cond", "br_uncond"):
            ba = rec.get("branch_annotations")
            if ba:
                taken = ba["taken_target"]
                ft    = ba["fallthrough_target"]
                mode  = ba.get("mode")
                cm(f"BTB predicts={ba['btb_prediction']}  btb_predicted_pc={ba['btb_predicted_pc']}  mode={mode}")
                if mode in ("mispredict_not_taken", "mispredict_taken", "correctly_not_taken"):
                    is_xm = rec.get("xm", False)
                    inreg0    = ssa_ref(rec, "inreg0") if is_xm else None
                    inreg0_sr = get_slot(rec, "inreg0") if is_xm else None
                    phys_in0  = inreg0_sr.get("assigned") if inreg0_sr else None
                    cond_raw = tmp("cond_raw")
                    cond_i1  = tmp("cond_i1")
                    if (is_xm and inreg0 is not None and phys_in0 is not None
                            and not ba["condition_value"]):
                        il(f'{cond_raw} = call i64 asm sideeffect '
                           f'"{mkr}movq $1, $0", '
                           f'"=&r,{{{phys_in0}}}"(i64 {inreg0})')
                    elif (_bc_alloy and not is_xm
                          and get_slot(rec, "inreg0") and get_slot(rec, "inreg0").get("specified")
                          and get_slot(rec, "inreg0").get("ssa_name")
                          and get_slot(rec, "inreg0").get("assigned")):
                        bsr = get_slot(rec, "inreg0")
                        cval = 1 if ba["condition_value"] else 0
                        il(f'{cond_raw} = call i64 asm sideeffect '
                           f'"{mkr}movq $1, $0\\0Aandq $$0, $0\\0Aorq $${cval}, $0", '
                           f'"=&r,{{{bsr["assigned"]}}},~{{flags}}"(i64 %{bsr["ssa_name"]})')
                        _bc_pcs.append(pc)
                    else:
                        vpool = pass4_result.get("virtual_reg_pool", [])
                        cond_reg = vpool[1] if len(vpool) > 1 else "r11"
                        init_op = "movq $$1, $0" if ba["condition_value"] else "xorq $0, $0"
                        il(f'{cond_raw} = call i64 asm sideeffect '
                           f'"{mkr}{init_op}", '
                           f'"=&{{{cond_reg}}}"()')
                    il(f"{cond_i1} = icmp ne i64 {cond_raw}, 0")
                    if mode == "mispredict_taken":
                        ftb = f"ftbypass_{pc}"
                        ftb_lbl = f"__litmus_{safe_name}_ftbypass{pc}"
                        br_on(cond_raw, cond_i1, taken, ftb, False)
                        lbl(ftb)
                        il(f'call void asm sideeffect '
                           f'".globl {ftb_lbl}\\0A{ftb_lbl}:", ""()')
                        il(f"br label %{ft}")
                    elif taken == ft:
                        ftb = f"ftbypass_{pc}"
                        ftb_lbl = f"__litmus_{safe_name}_ftbypass{pc}"
                        br_on(cond_raw, cond_i1, taken, ftb, False)
                        lbl(ftb)
                        il(f'call void asm sideeffect '
                           f'".globl {ftb_lbl}\\0A{ftb_lbl}:", ""()')
                        il(f"br label %{ft}")
                    else:
                        br_on(cond_raw, cond_i1, taken, ft, False)
                else:
                    il(f'call void asm sideeffect "{mkr}", ""()')
                    cond = rec.get("condition_ssa_forced", "i1 true")
                    il(f"br {cond}, label %{taken}, label %{ft}")
                last_was_terminator = True
            else:
                il(f'call void asm sideeffect "{mkr}", ""()')
                cm(f"branch {atom} has no branch_annotations — skipped")

        else:
            il(f'call void asm sideeffect "{mkr}", ""()')
            cm(f"unknown concrete_instruction={concrete!r} — skipped")

    if needs_end_block:
        if not last_was_terminator:
            il("br label %end_block")
        lbl("end_block")
        il("ret i64 0")
    else:
        if not last_was_terminator:
            il("ret i64 0")

    lines.append("}")
    ir = "\n".join(lines)

    if _br_cmp or _jmp_pcs or _br_uni:
        pass4_result["branch_forms"] = {"br_cmp": _br_cmp, "jmp_direct_pcs": _jmp_pcs}
        if _br_uni:
            pass4_result["branch_forms"].update(uniform=_br_uni, br_cmp_pcs=sorted(_cmp_pcs))
    if _bc_alloy:
        pass4_result["branch_cond"] = {"from_alloy": True, "pcs": _bc_pcs}
    if _fv4_forms:
        pass4_result["vocab_forms"] = _fv4_forms
    if _fv2_on:
        _fv2_rec["window_pc"] = _win_pc
        _fv2_rec["pre_window_reads"] = _pre_ok
        _fv2_rec["dead_registers"] = _fv2_dead
        pass4_result["fv2"] = _fv2_rec

    if _vrj:
        pass4_result["vocab_rj"] = {"rmw": bool(_vrj.get("rmw")), "jmp": bool(_vrj.get("jmp")),
                                    "rmw_pcs": _rmw_pcs,
                                    "jmp_filler_before_pcs": [f["before_pc"] for f in _fv2_rec["fillers"]
                                                              if f.get("op") == FV2_FILLER_JMP]}
    if _fpr_on:
        pass4_result["fpr_routes"] = {
            "loads": _fpr_loads, "xmm_regs": _fpr_regs, "routes": _fpr_routes}

    if write_out:
        if out_path is None:
            raise ValueError("out_path must not be None when write_out=True")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(ir + "\n")

    return ir


def emit_branch_annotations(
    result: Dict[str, Any],
    out_path: Optional[str] = None,
    write_out: bool = False,
) -> List[Dict[str, Any]]:
    import json

    annotations: List[Dict[str, Any]] = []

    _jmps = set((result.get("branch_forms") or {}).get("jmp_direct_pcs", []))
    for rec in result["instructions"]:
        ba = rec.get("branch_annotations")
        if ba is None or rec["pc"] in _jmps:
            continue
        annotations.append({
            "branch_pc":            rec["pc"],
            "branch_atom":          rec["instruction"],
            "btb_forced_target_pc": ba["btb_predicted_pc"],
            "mode":                 ba["mode"],
        })

    xmit = None
    for rec in result["instructions"]:
        if rec.get("xm", False):
            xmit = {
                "pc":   rec["pc"],
                "kind": rec["kind"],
                "atom": rec["instruction"],
            }
            break

    lc_rec, fnc_rec = commit_boundary(result["instructions"])
    last_committed: Optional[Dict[str, Any]] = (
        {"pc": lc_rec["pc"], "atom": lc_rec["instruction"]} if lc_rec else None)
    first_noncommitted: Optional[Dict[str, Any]] = (
        {"pc": fnc_rec["pc"], "atom": fnc_rec["instruction"]} if fnc_rec else None)

    if write_out:
        if out_path is None:
            raise ValueError("out_path must not be None when write_out=True")
        payload: Dict[str, Any] = {
            "branch_mode": result.get("branch_mode", "unknown"),
            "annotations": annotations,
        }
        if xmit is not None:
            payload["xmit"] = xmit
        cb_payload: Dict[str, Any] = {}
        if last_committed is not None:
            cb_payload["last_committed"] = last_committed
        if first_noncommitted is not None:
            cb_payload["first_noncommitted"] = first_noncommitted
        if cb_payload:
            payload["commit_boundary"] = cb_payload
        stl = _stl_pairs(result["instructions"])
        if stl:
            alias = _stl_alias_load_matches(result)
            payload["stl_annotations"] = [
                {"store_pc": p["store_pc"], "load_pc": l_pc, "role": role,
                 "mem_atom": p["mem_atom"], "mode": "stl_bypass"}
                for p in stl
                for l_pc, role in ([(p["load_pc"], "bypass")]
                                   + [(a, "alias") for a in alias[p["pair"]]])
            ]
        if result.get("fpr_routes") is not None:
            payload["fpr"] = result["fpr_routes"]
        if result.get("fv2") is not None:
            payload["fanout_v2"] = result["fv2"]
        if result.get("store_separation") is not None:
            payload["store_separation"] = result["store_separation"]
        if result.get("branch_forms") is not None:
            payload["branch_forms"] = result["branch_forms"]
        if result.get("vocab_rj") is not None:
            payload["vocab_rj"] = result["vocab_rj"]
        if result.get("vocab_forms") is not None:
            payload["vocab_forms"] = result["vocab_forms"]
        if result.get("branch_cond") is not None:
            payload["branch_cond"] = result["branch_cond"]
        if result.get("reg_naming") is not None:
            payload["reg_naming"] = dict(result["reg_naming"],
                                         locked_registers=result["locked_registers"],
                                         infra_registers=result["virtual_reg_pool"][:_VPOOL_FREE_START])
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")

    return annotations


if __name__ == "__main__":
    xml_text = open("alloy-out/STT_new/inst-000001.xml", "r", encoding="utf-8").read()
    inst = parse_alloy_xml(xml_text)
    print(pass1_specify_state_a(inst, out_path="alloy-out/spo_program.ir", write_out=True))