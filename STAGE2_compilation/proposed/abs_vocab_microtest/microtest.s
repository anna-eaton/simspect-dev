# abs-vocab (2026-11-12) hand micro-test: every new fv4 asm encoding (fv4_vocab.jsonc) decodes and
# computes the right value. Static, no libc. Prints "ABSVOCAB OK" and exits 0, or prints
# "ABSVOCAB FAIL" and exits with the failing check number.
        .text
        .globl _start
_start:
        leaq buf(%rip), %r10          # probe / mem base
        # ---------------- ld: load_swapidx ----------------
        movabsq $0x1122334455667788, %rax
        movq %rax, 16(%r10)
        movq $16, %r12
        movq (%r12,%r10,1), %rbx      # probe path, base/index swapped
        movl $1, %r15d
        cmpq %rax, %rbx
        jne fail
        movq 16(,%r10,1), %rbx        # mem path, index-only SIB
        movl $2, %r15d
        cmpq %rax, %rbx
        jne fail
        # ---------------- ld: RMW (X1 form, for comparison) ----------------
        orq $0, 16(%r10)
        orq $0, (%r10,%r12,1)
        movl $3, %r15d
        cmpq %rax, 16(%r10)
        jne fail
        # ---------------- str: store_swapidx / store_imm ----------------
        movq $0xdead, %rbx
        movq $24, %r12
        movq %rbx, (%r12,%r10,1)      # probe path swapped
        movl $4, %r15d
        cmpq %rbx, 24(%r10)
        jne fail
        movq %rbx, 32(,%r10,1)        # mem path index-only
        movl $5, %r15d
        cmpq %rbx, 32(%r10)
        jne fail
        movq $0, (%r10,%r12,1)        # store_imm probe path
        movl $6, %r15d
        cmpq $0, 24(%r10)
        jne fail
        movq $0, 32(%r10)             # store_imm mem path
        movl $7, %r15d
        cmpq $0, 32(%r10)
        jne fail
        movq $0, (%r12,%r10,1)        # store_imm probe path swapped
        movl $8, %r15d
        cmpq $0, 24(%r10)
        jne fail
        # ---------------- other_n ALU family ----------------
        movq $0x0f0f, %rdi
        movq $0x00ff, %rsi
        movq %rdi, %rax               # mov_rr
        movl $9, %r15d
        cmpq $0x0f0f, %rax
        jne fail
        movq %rdi, %rax ; negq %rax   # neg
        movl $10, %r15d
        cmpq $-0x0f0f, %rax
        jne fail
        movq %rdi, %rax ; shlq $3, %rax   # shl3
        movl $11, %r15d
        cmpq $0x7878, %rax
        jne fail
        movq %rdi, %rax ; addq %rsi, %rax # addq_rr
        movl $12, %r15d
        cmpq $0x100e, %rax
        jne fail
        movq %rdi, %rax ; subq %rsi, %rax # sub_rr
        movl $13, %r15d
        cmpq $0x0e10, %rax
        jne fail
        movq %rdi, %rax ; xorq %rsi, %rax # xor_rr
        movl $14, %r15d
        cmpq $0x0ff0, %rax
        jne fail
        movq %rdi, %rax ; andq %rsi, %rax # and_rr
        movl $15, %r15d
        cmpq $0x000f, %rax
        jne fail
        movq %rdi, %rax ; orq %rsi, %rax  # or_rr
        movl $16, %r15d
        cmpq $0x0fff, %rax
        jne fail
        leaq (%rdi,%rsi,8), %rax      # lea_s8
        movl $17, %r15d
        cmpq $0x1707, %rax
        jne fail
        # in-place (out == in0) and out == in1 shapes the emitter uses
        movq %rdi, %rcx ; subq %rsi, %rcx            # out==in0
        movl $18, %r15d
        cmpq $0x0e10, %rcx
        jne fail
        movq %rsi, %rcx ; negq %rcx ; addq %rdi, %rcx    # sub with out==in1: -in1 + in0
        movl $19, %r15d
        cmpq $0x0e10, %rcx
        jne fail
        movq %rdi, %rcx ; negq %rcx                   # neg in place
        movl $20, %r15d
        cmpq $-0x0f0f, %rcx
        jne fail
        movq %rdi, %rcx ; shlq $3, %rcx               # shl3 in place
        movl $21, %r15d
        cmpq $0x7878, %rcx
        jne fail
        leaq (%rdi,%rdi,8), %rcx                      # lea_s8 with in0==in1
        movl $22, %r15d
        cmpq $0x8787, %rcx
        jne fail
        # ---------------- br forms ----------------
        xorq %rcx, %rcx
        cmpq $1, %rcx                 # cmp form, taken iff c==0
        jb 1f
        movl $23, %r15d
        jmp fail
1:      movq $5, %rcx
        cmpq $1, %rcx                 # cmp form, jae taken iff c!=0
        jae 2f
        movl $24, %r15d
        jmp fail
2:      testq %rcx, %rcx              # test form
        jne 3f
        movl $25, %r15d
        jmp fail
3:      jmp 4f                        # jmp form (direct jmp to fall-through)
4:      nop
        # all passed
        movl $1, %eax
        movl $1, %edi
        leaq okmsg(%rip), %rsi
        movl $12, %edx
        syscall
        movl $60, %eax
        xorl %edi, %edi
        syscall
fail:
        movl $1, %eax
        movl $1, %edi
        leaq failmsg(%rip), %rsi
        movl $14, %edx
        syscall
        movl $60, %eax
        movl %r15d, %edi
        syscall
        .data
okmsg:   .ascii "ABSVOCAB OK\n"
failmsg: .ascii "ABSVOCAB FAIL\n"
        .bss
        .align 64
buf:    .zero 256
