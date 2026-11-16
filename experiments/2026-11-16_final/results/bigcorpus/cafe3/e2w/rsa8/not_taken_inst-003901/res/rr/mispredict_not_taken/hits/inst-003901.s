	.text
	.file	"inst-003901.ll"
	.globl	"inst-003901"                   # -- Begin function inst-003901
	.p2align	4, 0x90
	.type	"inst-003901",@function
"inst-003901":                          # @inst-003901
	.cfi_startproc
# %bb.0:                                # %entry
	pushq	%r15
	.cfi_def_cfa_offset 16
	pushq	%r12
	.cfi_def_cfa_offset 24
	.cfi_offset %r12, -24
	.cfi_offset %r15, -16
	movq	$0, -8(%rsp)
	xorl	%eax, %eax
	#APP
	movq	%rax, %r10
	#NO_APP
	#APP
	movq	%rax, %r15
	#NO_APP
	#APP
	movq	%rax, %r9
	#NO_APP
	#APP
	mfence
	#NO_APP
	#APP
	xorl	%esi, %esi
	#NO_APP
	leaq	-8(%rsp), %rdi
	#APP
	.globl	__litmus_inst_003901_pc0
__litmus_inst_003901_pc0:
	movq	%r10, (%rdi)
	#NO_APP
	#APP
	.globl	__litmus_inst_003901_pc1
__litmus_inst_003901_pc1:
	.globl	__litmus_inst_003901_last_committed
__litmus_inst_003901_last_committed:
	movq	(,%rdi), %r12
	#NO_APP
	#APP
	addq	$0, %r12
	#NO_APP
	#APP
	.globl	__litmus_inst_003901_pc2
__litmus_inst_003901_pc2:
	.globl	__litmus_inst_003901_first_noncommitted
__litmus_inst_003901_first_noncommitted:
	movq	%r12, %rax
	andq	$0, %rax
	orq	$1, %rax
	#NO_APP
	testq	%rax, %rax
	jne	.LBB0_3
# %bb.1:                                # %bb_3
	leaq	-8(%rsp), %rdi
	#APP
	.globl	__litmus_inst_003901_pc3
__litmus_inst_003901_pc3:
	movq	(%rdi), %r12
	#NO_APP
	#APP
	addq	$4097, %r12                     # imm = 0x1001
	subq	$4097, %r12                     # imm = 0x1001
	#NO_APP
	#APP
	.globl	__litmus_inst_003901_pc4
__litmus_inst_003901_pc4:
	movq	%r12, %rax
	#NO_APP
	#APP
	cmpq	$1, %rax
	jb	.Ltmp0
	#NO_APP
# %bb.2:                                # %bb_5
	#APP
	.globl	__litmus_inst_003901_pc5
__litmus_inst_003901_pc5:
	nop
	#NO_APP
.Ltmp0:                                 # Block address taken
.LBB0_3:                                # %end_block
	xorl	%eax, %eax
	popq	%r12
	.cfi_def_cfa_offset 16
	popq	%r15
	.cfi_def_cfa_offset 8
	retq
.Lfunc_end0:
	.size	"inst-003901", .Lfunc_end0-"inst-003901"
	.cfi_endproc
                                        # -- End function
	.section	".note.GNU-stack","",@progbits
	.addrsig
