/*
 * SimSpect hook: print-only cache/defense event trace (format v2).
 *
 * Every event is printed under the existing O3PipeView debug flag as
 *   O3PipeView:simspect:<tick>:<struct>:<kind>:line=0x<line>:seq=<sn|->:
 *     pc=0x<pc|->:victim=0x<line|->:cause=<id|->:sq=<id|->:id=<id>
 *     [:key=value ...]                                   (v2 optional fields)
 * (one physical line). The first 11 fields are exactly the v1 format; v2
 * only APPENDS key=value fields (values never contain ':' or '='), so v1
 * parsers keep working. The first emitted line of a run is a header:
 *   O3PipeView:simspect:0:META:hooks:line=-:...:id=0:ver=2:build=<name>
 * Nothing here changes simulated behavior or timing: the only state kept is
 * print-side bookkeeping (event ids, squash ids, per-line attribution), all
 * consulted only when O3PipeView is enabled.
 * Documented in the SimSpect repo: wiki/design/SIMSPECT_HOOKS.md.
 */

#ifndef __SIM_SIMSPECT_HOOKS_HH__
#define __SIM_SIMSPECT_HOOKS_HH__

#include <cstdint>
#include <string>

#include "base/types.hh"

namespace SimSpect {

static const uint64_t NONE = ~0ULL;

/** SimSpect hook: true iff O3PipeView tracing is on (all hooks gate on it). */
bool enabled();

/** Physical line address (64B lines in every SimSpect build). */
inline Addr lineOf(Addr a) { return a & ~Addr(63); }

/** Fresh unique event id. */
uint64_t newId();

/** v2: optional key=value fields appended after id=. Values are sanitized
 *  (':', '=' and whitespace become '_'); NONE prints as '-'. */
struct Kv
{
    std::string s;
    Kv &str(const char *k, const std::string &v);
    Kv &hex(const char *k, uint64_t v);
    Kv &dec(const char *k, uint64_t v);
    Kv &sdec(const char *k, int64_t v);
    Kv &flag(const char *k, bool v) { return dec(k, v ? 1 : 0); }
    Kv &raw(const std::string &already_formatted) { s += already_formatted; return *this; }
};

/** Format one event line (no trailing newline); assigns the id if NONE. */
std::string format(const char *st, const char *kind, Addr line, uint64_t seq,
                   Addr pc, Addr victim, uint64_t cause, uint64_t sq,
                   uint64_t &id, const Kv &kv = Kv());
/** Print an already formatted line (adds the newline). */
void printLine(const std::string &l);

/** Print one event line; returns its id. NONE fields print as '-'. */
uint64_t emit(const char *st, const char *kind, Addr line, uint64_t seq,
              Addr pc, Addr victim, uint64_t cause, uint64_t sq,
              uint64_t id = NONE, const Kv &kv = Kv());

/** Core squash: emits ROB:squash and returns the new squash id. */
uint64_t noteSquash(uint64_t squashSeq, Addr pc);
/** Latest squash whose squashing seqNum < seq (the squash covering seq). */
uint64_t sqForInst(uint64_t seq);
/** Latest squash whose squashing seqNum == squashSeq (else latest). */
uint64_t sqForSquashSeq(uint64_t squashSeq);
/** Exact lookup: squash id for squashing seqNum, or NONE if never seen. */
uint64_t sqExact(uint64_t squashSeq);

/** Per-line attribution: most recent instruction that caused activity. */
void setLineAttr(Addr line, uint64_t seq, Addr pc);
bool getLineAttr(Addr line, uint64_t &seq, Addr &pc);

/** Evict->fill link: reserve the id the incoming fill of `line` in `st`
 *  will carry (cause= on the evict), and consume it at the fill.
 *  dropFill discards a reservation that no fill consumed (v2: e.g. an
 *  InvisiSpec SpecLoad replacement, which never allocates the line), so a
 *  later fill of the same line never inherits a stale cause id. */
uint64_t reserveFill(const std::string &st, Addr line, uint64_t seq);
uint64_t takeFill(const std::string &st, Addr line, uint64_t seq);
bool dropFill(const std::string &st, Addr line);

/** TLB attribution context (set by TLB::translate before lookup/insert). */
void setTlbCtx(uint64_t seq, Addr pc);
void getTlbCtx(uint64_t &seq, Addr &pc);

/** v2: hit level of a response packet, noted where the memory system knows
 *  it (Ruby Sequencer::hitCallback) and taken where the LSQ receives it. */
void notePktLvl(const void *pkt, const char *lvl);
std::string takePktLvl(const void *pkt);

/** v2: small print-side tag sets (e.g. "sbsq" = InvisiSpec SB entry
 *  released at squash, "sbfill" = SB entry filled), keyed (a, b). */
void tagSet(const char *tag, uint64_t a, uint64_t b);
bool tagHas(const char *tag, uint64_t a, uint64_t b);
bool tagErase(const char *tag, uint64_t a, uint64_t b);

} // namespace SimSpect

#endif // __SIM_SIMSPECT_HOOKS_HH__
