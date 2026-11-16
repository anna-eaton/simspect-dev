/*
 * SimSpect hook: Ruby-side helpers for the print-only cache event trace (v2).
 *
 * Called from (a) SLICC-generated code (PeekStatementAST: a MsgScope on
 * every peeked in_msg, so each message has its own attribution context that
 * ends with the peek; StateMachine doTransition: begin/endTransition around
 * every transition plus a TransGuard), (b) CacheMemory allocate/deallocate/
 * setMRU, (c) TBETable allocate/deallocate. Everything is print-side
 * bookkeeping, gated on O3PipeView. See wiki/design/SIMSPECT_HOOKS.md in the
 * SimSpect repo.
 */

#ifndef __MEM_RUBY_SLICC_INTERFACE_SIMSPECTRUBYHOOKS_HH__
#define __MEM_RUBY_SLICC_INTERFACE_SIMSPECTRUBYHOOKS_HH__

#include <sstream>
#include <string>
#include <utility>

#include "base/types.hh"
#include "sim/simspect_hooks.hh"

class RubyRequest;
class CacheMemory;

namespace SimSpect {

/** The message the current controller is processing (one per peek). */
struct MsgCtx
{
    bool valid;
    Addr line;
    bool isCpu;     // a RubyRequest from the Sequencer (exact seq/pc)
    bool isIfetch;
    uint64_t seq;
    Addr pc;
    Addr addr;      // byte address (CPU requests), else NONE
    uint64_t size;  // bytes (CPU requests), else NONE
    std::string req;    // closed vocabulary: ld st ifetch specld expose ...
    std::string msg;    // native message type (RubyRequestType / Coherence*)
    int ctId;           // CleanupSpec cleanup-table id (-1 if none)
    const void *ptr;    // the message object (dedupe of recycled requests)
    MsgCtx() : valid(false), line(0), isCpu(false), isIfetch(false),
               seq(NONE), pc(NONE), addr(NONE), size(NONE), req("-"),
               msg("-"), ctId(-1), ptr(nullptr) {}
};
extern MsgCtx g_msg;

void noteRubyRequest(const RubyRequest *m);
void noteMsgAddr(Addr a, const std::string &type, const void *ptr);

template <class T>
auto msgTypeStr(const T *m, int) -> decltype(
    std::declval<std::ostream &>() << m->m_Type, std::string())
{
    std::ostringstream os;
    os << m->m_Type;
    return os.str();
}

template <class T>
std::string msgTypeStr(const T *, long)
{
    return "-";
}

template <class T>
auto noteMsgImpl(const T *m, int) -> decltype((void)m->m_addr, void())
{
    noteMsgAddr(m->m_addr, msgTypeStr(m, 0), (const void *)m);
}

template <class T>
void noteMsgImpl(const T *, long)
{
    g_msg = MsgCtx();
}

/** SimSpect hook: generic peeked message (protocol msgs carry m_addr). */
template <class T>
inline void noteMsg(const T *m)
{
    if (enabled())
        noteMsgImpl(m, 0);
}

/** SimSpect hook: a Sequencer RubyRequest (carries the inst seqNum). */
inline void noteMsg(const RubyRequest *m)
{
    if (enabled())
        noteRubyRequest(m);
}

/** SimSpect hook (v2): the attribution context of one peek. Restores the
 *  enclosing context when the peek's scope ends (also on exceptions), so no
 *  event outside a peek inherits a stale message. */
class MsgScope
{
    MsgCtx saved;
    bool on;
  public:
    template <class T>
    explicit MsgScope(const T *m) : on(enabled())
    {
        if (on) {
            saved = g_msg;
            noteMsg(m);
        }
    }
    ~MsgScope() { if (on) g_msg = saved; }
};

/** SimSpect hook: wraps every SLICC transition (doTransition). */
void beginTransition(const char *machine, int version,
                     const std::string &event, const std::string &state,
                     const std::string &statePerm, Addr addr);
void endTransition(bool valid, const std::string &nextState,
                   const std::string &nextPerm);
/** Closes a transition whose endTransition never ran (an action threw). */
void abortTransition();

class TransGuard
{
    bool on;
  public:
    explicit TransGuard(bool o) : on(o) {}
    void done() { on = false; }
    ~TransGuard() { if (on) abortTransition(); }
};

/** SimSpect hook: CacheMemory tag changes / replacement-state updates
 *  (set/way = the slot; -1 if unknown). */
void onCacheAllocate(CacheMemory *cm, Addr a, int64_t set, int way);
void onCacheDeallocate(CacheMemory *cm, Addr a, int64_t set, int way);
void onCacheTouch(CacheMemory *cm, Addr a, int64_t set, int way);

/** SimSpect hook: TBE (Ruby MSHR) alloc/free -> MSHR/L2MSHR/DIRTBE
 *  buf_fill/buf_release; allocation also records per-line attribution. */
void onTBEAllocate(Addr a);
void onTBEDeallocate(Addr a);

/** v2: closed-vocabulary req= for a RubyRequestType name. */
std::string reqOfRubyType(const std::string &t, bool validate);

} // namespace SimSpect

#endif // __MEM_RUBY_SLICC_INTERFACE_SIMSPECTRUBYHOOKS_HH__
