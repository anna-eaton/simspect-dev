	.text
	.file	"inst-007681.ll"
	.globl	"inst-007681"                   # -- Begin function inst-007681
	.p2align	4, 0x90
	.type	"inst-007681",@function
"inst-007681":                          # @inst-007681
	.cfi_startproc
# %bb.0:                                # %entry
	pushq	%r14
	.cfi_def_cfa_offset 16
	.cfi_offset %r14, -16
	movq	$0, -8(%rsp)
	xorl	%ecx, %ecx
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
	mfence
	#NO_APP
	#APP
	movq	%rax, %xmm14
	movq	%rdi, %xmm15
	pxor	%xmm15, %xmm14
	movq	%xmm14, %r11
	#NO_APP
	leaq	-8(%rsp), %rdx
	#APP
	.globl	__litmus_inst_007681_pc0
__litmus_inst_007681_pc0:
	movq	%rax, (%rdx)
	#NO_APP
	#APP
	.globl	__litmus_inst_007681_pc1
__litmus_inst_007681_pc1:
	.globl	__litmus_inst_007681_last_committed
__litmus_inst_007681_last_committed:
	movq	(%rdx), %rax
	#NO_APP
	#APP
	.globl	__litmus_inst_007681_pc2
__litmus_inst_007681_pc2:
	.globl	__litmus_inst_007681_first_noncommitted
__litmus_inst_007681_first_noncommitted:
	movq	%rax, %rcx
	andq	$0, %rcx
	orq	$0, %rcx
	#NO_APP
	testq	%rcx, %rcx
	je	.LBB0_1
# %bb.2:                                # %bb_3
	leaq	-8(%rsp), %rdx
	#APP
	.globl	__litmus_inst_007681_pc3
__litmus_inst_007681_pc3:
	movq	(%rdx), %rax
	#NO_APP
	#APP
	.globl	__litmus_inst_007681_pc4
__litmus_inst_007681_pc4:
	movq	%rax, %rcx
	#NO_APP
	#APP
	cmpq	$1, %rcx
	jb	.Ltmp0
	#NO_APP
# %bb.3:                                # %bb_5
	#APP
	movq	%rdi, %r14
	incq	%r14
	#NO_APP
	#APP
	.globl	__litmus_inst_007681_pc5
__litmus_inst_007681_pc5:
	nop
	#NO_APP
	jmp	.LBB0_4
.LBB0_1:                                # %ftbypass_2
	#APP
	.globl	__litmus_inst_007681_ftbypass2
__litmus_inst_007681_ftbypass2:
	#NO_APP
.Ltmp0:                                 # Block address taken
.LBB0_4:                                # %end_block
	xorl	%eax, %eax
	popq	%r14
	.cfi_def_cfa_offset 8
	retq
.Lfunc_end0:
	.size	"inst-007681", .Lfunc_end0-"inst-007681"
	.cfi_endproc
                                        # -- End function
	.section	".note.GNU-stack","",@progbits
	.addrsig
