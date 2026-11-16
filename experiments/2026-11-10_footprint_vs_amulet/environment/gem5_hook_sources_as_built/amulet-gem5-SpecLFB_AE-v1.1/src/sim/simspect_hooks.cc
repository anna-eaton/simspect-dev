/*
 * SimSpect hook: print-only cache/defense event trace (core emitter, v2).
 * See simspect_hooks.hh. Print-side bookkeeping only; no simulated state.
 */

#include "sim/simspect_hooks.hh"

#include <map>
#include <set>
#include <tuple>
#include <utility>
#include <vector>

#include "base/cprintf.hh"
#include "base/trace.hh"
#include "debug/O3PipeView.hh"
#include "sim/cur_tick.hh"

// SimSpect hook: which AMuLeT build this file is compiled into (META line).
#ifndef SIMSPECT_BUILD_NAME
#define SIMSPECT_BUILD_NAME "SpecLFB"
#endif

namespace gem5 {
namespace SimSpect {

namespace {

uint64_t g_nextId = 1;
uint64_t g_nextSq = 1;
bool g_headerDone = false;
// (squashing seqNum, squash id), in time order
std::vector<std::pair<uint64_t, uint64_t> > g_squashes;
std::map<Addr, std::pair<uint64_t, Addr> > g_lineAttr;
// (struct, line) -> (reserved fill id, seq of the causing access)
std::map<std::pair<std::string, Addr>, std::pair<uint64_t, uint64_t> >
    g_pendingFill;
uint64_t g_tlbSeq = NONE;
Addr g_tlbPc = NONE;
std::map<const void *, std::string> g_pktLvl;
std::set<std::tuple<std::string, uint64_t, uint64_t> > g_tags;

std::string
hexOrDash(uint64_t v)
{
    if (v == NONE)
        return "-";
    return csprintf("0x%x", v);
}

std::string
decOrDash(uint64_t v)
{
    if (v == NONE)
        return "-";
    return csprintf("%d", v);
}

std::string
sanitize(const std::string &v)
{
    if (v.empty())
        return "-";
    std::string o = v;
    for (auto &c : o)
        if (c == ':' || c == '=' || c == ' ' || c == '\t' || c == '\n')
            c = '_';
    return o;
}

void
header()
{
    if (g_headerDone)
        return;
    g_headerDone = true;
    DPRINTFR(O3PipeView,
             "O3PipeView:simspect:0:META:hooks:line=-:seq=-:pc=-:victim=-:"
             "cause=-:sq=-:id=0:ver=2:build=%s\n", SIMSPECT_BUILD_NAME);
}

} // anonymous namespace

Kv &
Kv::str(const char *k, const std::string &v)
{
    s += csprintf(":%s=%s", k, sanitize(v));
    return *this;
}

Kv &
Kv::hex(const char *k, uint64_t v)
{
    s += csprintf(":%s=%s", k, hexOrDash(v));
    return *this;
}

Kv &
Kv::dec(const char *k, uint64_t v)
{
    s += csprintf(":%s=%s", k, decOrDash(v));
    return *this;
}

Kv &
Kv::sdec(const char *k, int64_t v)
{
    s += csprintf(":%s=%d", k, v);
    return *this;
}

bool
enabled()
{
    return TRACING_ON && ::gem5::debug::O3PipeView;
}

uint64_t
newId()
{
    return g_nextId++;
}

std::string
format(const char *st, const char *kind, Addr line, uint64_t seq, Addr pc,
       Addr victim, uint64_t cause, uint64_t sq, uint64_t &id, const Kv &kv)
{
    if (id == NONE)
        id = newId();
    return csprintf("O3PipeView:simspect:%llu:%s:%s:line=%s:seq=%s:pc=%s:"
                    "victim=%s:cause=%s:sq=%s:id=%llu%s",
                    (unsigned long long)curTick(), st, kind,
                    hexOrDash(line), decOrDash(seq), hexOrDash(pc),
                    hexOrDash(victim), decOrDash(cause), decOrDash(sq),
                    (unsigned long long)id, kv.s);
}

void
printLine(const std::string &l)
{
    header();
    DPRINTFR(O3PipeView, "%s\n", l);
}

uint64_t
emit(const char *st, const char *kind, Addr line, uint64_t seq, Addr pc,
     Addr victim, uint64_t cause, uint64_t sq, uint64_t id, const Kv &kv)
{
    std::string l = format(st, kind, line, seq, pc, victim, cause, sq, id, kv);
    printLine(l);
    return id;
}

uint64_t
noteSquash(uint64_t squashSeq, Addr pc)
{
    uint64_t sq = g_nextSq++;
    g_squashes.push_back(std::make_pair(squashSeq, sq));
    emit("ROB", "squash", NONE, squashSeq, pc, NONE, NONE, sq);
    return sq;
}

uint64_t
sqForInst(uint64_t seq)
{
    if (seq == NONE)
        return NONE;
    for (auto it = g_squashes.rbegin(); it != g_squashes.rend(); ++it)
        if (it->first < seq)
            return it->second;
    return NONE;
}

uint64_t
sqForSquashSeq(uint64_t squashSeq)
{
    for (auto it = g_squashes.rbegin(); it != g_squashes.rend(); ++it)
        if (it->first == squashSeq)
            return it->second;
    return g_squashes.empty() ? NONE : g_squashes.back().second;
}

uint64_t
sqExact(uint64_t squashSeq)
{
    for (auto it = g_squashes.rbegin(); it != g_squashes.rend(); ++it)
        if (it->first == squashSeq)
            return it->second;
    return NONE;
}

void
setLineAttr(Addr line, uint64_t seq, Addr pc)
{
    g_lineAttr[lineOf(line)] = std::make_pair(seq, pc);
}

bool
getLineAttr(Addr line, uint64_t &seq, Addr &pc)
{
    auto it = g_lineAttr.find(lineOf(line));
    if (it == g_lineAttr.end()) {
        seq = NONE;
        pc = NONE;
        return false;
    }
    seq = it->second.first;
    pc = it->second.second;
    return true;
}

uint64_t
reserveFill(const std::string &st, Addr line, uint64_t seq)
{
    auto key = std::make_pair(st, lineOf(line));
    auto it = g_pendingFill.find(key);
    if (it != g_pendingFill.end() && it->second.second == seq)
        return it->second.first;
    uint64_t id = newId();
    g_pendingFill[key] = std::make_pair(id, seq);
    return id;
}

uint64_t
takeFill(const std::string &st, Addr line, uint64_t seq)
{
    auto key = std::make_pair(st, lineOf(line));
    auto it = g_pendingFill.find(key);
    if (it == g_pendingFill.end())
        return newId();
    uint64_t id = it->second.first;
    bool match = (it->second.second == seq);
    g_pendingFill.erase(it);
    return match ? id : newId();
}

bool
dropFill(const std::string &st, Addr line)
{
    return g_pendingFill.erase(std::make_pair(st, lineOf(line))) > 0;
}

void
setTlbCtx(uint64_t seq, Addr pc)
{
    g_tlbSeq = seq;
    g_tlbPc = pc;
}

void
getTlbCtx(uint64_t &seq, Addr &pc)
{
    seq = g_tlbSeq;
    pc = g_tlbPc;
}

void
notePktLvl(const void *pkt, const char *lvl)
{
    g_pktLvl[pkt] = lvl;
}

std::string
takePktLvl(const void *pkt)
{
    auto it = g_pktLvl.find(pkt);
    if (it == g_pktLvl.end())
        return "-";
    std::string l = it->second;
    g_pktLvl.erase(it);
    return l;
}

void
tagSet(const char *tag, uint64_t a, uint64_t b)
{
    g_tags.insert(std::make_tuple(std::string(tag), a, b));
}

bool
tagHas(const char *tag, uint64_t a, uint64_t b)
{
    return g_tags.count(std::make_tuple(std::string(tag), a, b)) > 0;
}

bool
tagErase(const char *tag, uint64_t a, uint64_t b)
{
    return g_tags.erase(std::make_tuple(std::string(tag), a, b)) > 0;
}

} // namespace SimSpect
} // namespace gem5
