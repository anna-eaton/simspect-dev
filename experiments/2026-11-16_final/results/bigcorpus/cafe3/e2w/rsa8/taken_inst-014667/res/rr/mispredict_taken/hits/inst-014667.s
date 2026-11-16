	.text
	.file	"inst-014667.ll"
	.globl	"inst-014667"                   # -- Begin function inst-014667
	.p2align	4, 0x90
	.type	"inst-014667",@function
"inst-014667":                          # @inst-014667
	.cfi_startproc
# %bb.0:                                # %entry
	pushq	%r15
	.cfi_def_cfa_offset 16
	pushq	%r12
	.cfi_def_cfa_offset 24
	.cfi_offset %r12, -24
	.cfi_offset %r15, -16
	movq	$0, -16(%rsp)
	movq	$0, -8(%rsp)
	xorl	%ecx, %ecx
	#APP
	movq	%rcx, %rax
	#NO_APP
	#APP
	movq	%rcx, %rdx
	#NO_APP
	#APP
	movq	%rcx, %rsi
	#NO_APP
	#APP
	mfence
	#NO_APP
	leaq	-16(%rsp), %r10
	#APP
	.globl	__litmus_inst_014667_pc0
__litmus_inst_014667_pc0:
	movq	(,%r10), %rdi
	#NO_APP
	#APP
	movl	%edi, %r15d
	imull	%edi, %r15d
	#NO_APP
	#APP
	.globl	__litmus_inst_014667_pc1
__litmus_inst_014667_pc1:
	movq	%rdi, %rax
	andq	$0, %rax
	orq	$0, %rax
	#NO_APP
	testq	%rax, %rax
	jne	.LBB0_6
# %bb.1:                                # %bb_2
	leaq	-16(%rsp), %r10
	#APP
	.globl	__litmus_inst_014667_pc2
__litmus_inst_014667_pc2:
	movq	%rdi, 8(%r10)
	#NO_APP
	#APP
	.globl	__litmus_inst_014667_pc3
__litmus_inst_014667_pc3:
	.globl	__litmus_inst_014667_last_committed
__litmus_inst_014667_last_committed:
	movq	(,%r10), %rdi
	#NO_APP
	#APP
	.globl	__litmus_inst_014667_pc4
__litmus_inst_014667_pc4:
	.globl	__litmus_inst_014667_first_noncommitted
__litmus_inst_014667_first_noncommitted:
	movq	%rdi, %rax
	andq	$0, %rax
	orq	$0, %rax
	#NO_APP
	testq	%rax, %rax
	je	.LBB0_2
# %bb.3:                                # %bb_5
	#APP
	movswq	%di, %r12
	#NO_APP
	#APP
	.globl	__litmus_inst_014667_pc5
__litmus_inst_014667_pc5:
	movq	%rdi, %rax
	andq	$0, %rax
	orq	$0, %rax
	#NO_APP
	#APP
	cmpq	$1, %rax
	jae	.Ltmp0
	#NO_APP
# %bb.4:                                # %bb_6
	leaq	-16(%rsp), %r10
	#APP
	.globl	__litmus_inst_014667_pc6
__litmus_inst_014667_pc6:
	movq	(%r10), %rdi
	#NO_APP
	#APP
	.globl	__litmus_inst_014667_pc7
__litmus_inst_014667_pc7:
	movq	%rdi, %rax
	#NO_APP
	#APP
	cmpq	$1, %rax
	jb	.Ltmp0
	#NO_APP
# %bb.5:                                # %bb_8
	#APP
	.globl	__litmus_inst_014667_pc8
__litmus_inst_014667_pc8:
	nop
	#NO_APP
	jmp	.LBB0_6
.LBB0_2:                                # %ftbypass_4
	#APP
	.globl	__litmus_inst_014667_ftbypass4
__litmus_inst_014667_ftbypass4:
	#NO_APP
.Ltmp0:                                 # Block address taken
.LBB0_6:                                # %end_block
	xorl	%eax, %eax
	popq	%r12
	.cfi_def_cfa_offset 16
	popq	%r15
	.cfi_def_cfa_offset 8
	retq
.Lfunc_end0:
	.size	"inst-014667", .Lfunc_end0-"inst-014667"
	.cfi_endproc
                                        # -- End function
	.section	".note.GNU-stack","",@progbits
	.addrsig
