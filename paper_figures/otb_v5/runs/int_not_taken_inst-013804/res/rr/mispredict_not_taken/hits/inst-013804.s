	.text
	.file	"inst-013804.ll"
	.globl	"inst-013804"                   # -- Begin function inst-013804
	.p2align	4, 0x90
	.type	"inst-013804",@function
"inst-013804":                          # @inst-013804
	.cfi_startproc
# %bb.0:                                # %entry
	pushq	%r14
	.cfi_def_cfa_offset 16
	pushq	%r13
	.cfi_def_cfa_offset 24
	pushq	%r12
	.cfi_def_cfa_offset 32
	.cfi_offset %r12, -32
	.cfi_offset %r13, -24
	.cfi_offset %r14, -16
	movq	$0, -8(%rsp)
	xorl	%ecx, %ecx
	#APP
	movq	%rcx, %r10
	#NO_APP
	#APP
	movq	%rcx, %r11
	#NO_APP
	#APP
	movq	%rcx, %r12
	#NO_APP
	#APP
	movq	%rcx, %r9
	#NO_APP
	#APP
	movq	%rcx, %rax
	#NO_APP
	#APP
	movq	%rcx, %rdi
	#NO_APP
	#APP
	movq	%rcx, %rsi
	#NO_APP
	#APP
	mfence
	#NO_APP
	leaq	-8(%rsp), %rcx
	#APP
	.globl	__litmus_inst_013804_pc0
__litmus_inst_013804_pc0:
	movq	%rax, (,%rcx)
	#NO_APP
	#APP
	.globl	__litmus_inst_013804_pc1
__litmus_inst_013804_pc1:
	.globl	__litmus_inst_013804_last_committed
__litmus_inst_013804_last_committed:
	movq	(%rcx), %r13
	#NO_APP
	#APP
	.globl	__litmus_inst_013804_pc2
__litmus_inst_013804_pc2:
	.globl	__litmus_inst_013804_first_noncommitted
__litmus_inst_013804_first_noncommitted:
	movq	%r13, %rcx
	andq	$0, %rcx
	orq	$1, %rcx
	#NO_APP
	#APP
	cmpq	$1, %rcx
	jae	.Ltmp0
	#NO_APP
# %bb.1:                                # %bb_3
	leaq	-8(%rsp), %rcx
	#APP
	.globl	__litmus_inst_013804_pc3
__litmus_inst_013804_pc3:
	movq	(%rcx), %r13
	#NO_APP
	#APP
	.globl	__litmus_inst_013804_pc4
__litmus_inst_013804_pc4:
	movq	%rax, (,%rcx)
	#NO_APP
	#APP
	.globl	__litmus_inst_013804_pc5
__litmus_inst_013804_pc5:
	movq	%r13, %rax
	#NO_APP
	testq	%rax, %rax
	je	.LBB0_3
# %bb.2:                                # %bb_6
	leaq	-8(%rsp), %rcx
	#APP
	.globl	__litmus_inst_013804_pc6
__litmus_inst_013804_pc6:
	movq	%r11, (%rcx)
	#NO_APP
	#APP
	movsbq	%sil, %r14
	#NO_APP
	#APP
	.globl	__litmus_inst_013804_pc7
__litmus_inst_013804_pc7:
	movq	%r12, (,%rcx)
	#NO_APP
.Ltmp0:                                 # Block address taken
.LBB0_3:                                # %end_block
	xorl	%eax, %eax
	popq	%r12
	.cfi_def_cfa_offset 24
	popq	%r13
	.cfi_def_cfa_offset 16
	popq	%r14
	.cfi_def_cfa_offset 8
	retq
.Lfunc_end0:
	.size	"inst-013804", .Lfunc_end0-"inst-013804"
	.cfi_endproc
                                        # -- End function
	.section	".note.GNU-stack","",@progbits
	.addrsig
