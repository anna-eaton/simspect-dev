#!/usr/bin/env python3
# committed_rf_scan.py: XML-level count of committed loads and of rf edges into committed instructions. Read-only.
"""xml-level: committed loads whose inaddr is rf-fed (address from a producer). usage: xmlpeek.py <xmldir> <n> <seed>"""
import sys,os,random,collections
import xml.etree.ElementTree as ET
xmld, n, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
fs=sorted(os.listdir(xmld)); random.Random(seed).shuffle(fs); fs=fs[:n]
C=collections.Counter()
for f in fs:
    try: r=ET.parse(f"{xmld}/{f}").getroot().find("instance")
    except Exception: C["bad_xml"]+=1; continue
    F={fl.get("label"):[tuple(a.get("label") for a in t.findall("atom")) for t in fl.findall("tuple")] for fl in r.findall("field")}
    C["tests"]+=1
    com={t[0] for t in F.get("iscommitted",[])}
    kind={i:k.split("$")[0] for i,k in F.get("kind",[])}
    lds=[i for i,k in kind.items() if k=="TLoad"]
    inaddr={i:o for i,o in F.get("inaddr",[])}
    rfdst={b for a,b in F.get("rf",[])}
    C[f"n_committed_{min(len(com),3)}"]+=1
    cl=[i for i in lds if i in com]
    if cl: C["committed_load"]+=1
    if any(inaddr.get(i) in rfdst for i in cl): C["committed_load_addr_rf_fed"]+=1
    # any rf edge whose destination operand belongs to a committed instruction
    owner={}
    for fld in ("inaddr","inreg","inmem"):
        for i,o in F.get(fld,[]): owner[o]=i
    if any(owner.get(b) in com for a,b in F.get("rf",[])): C["any_rf_into_committed_instr"]+=1
print(dict(sorted(C.items())))
