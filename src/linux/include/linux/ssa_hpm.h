/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef _LINUX_SSA_HPM_H
#define _LINUX_SSA_HPM_H
#include <linux/errno.h>
#include <linux/types.h>
struct task_struct;
struct linux_binprm;
#ifdef CONFIG_SSA_HPM
void ssa_hpm_fork(struct task_struct *p);
void ssa_hpm_fork_done(struct task_struct *p);
void ssa_hpm_switch(struct task_struct *prev, struct task_struct *next, bool preempt);
void ssa_hpm_exit(struct task_struct *p, long code);
int ssa_hpm_exec_check(struct linux_binprm *bprm);
int ssa_hpm_clone_check(unsigned long flags);
void ssa_hpm_exec_ready(unsigned long entry,unsigned long app,unsigned long interp);
void ssa_hpm_exec(struct task_struct *p);
long ssa_hpm_prctl(unsigned long op, unsigned long flags, unsigned long role, unsigned long test);
#else
static inline void ssa_hpm_fork(struct task_struct *p) {}
static inline void ssa_hpm_fork_done(struct task_struct *p) {}
static inline void ssa_hpm_switch(struct task_struct *p, struct task_struct *n, bool v) {}
static inline void ssa_hpm_exit(struct task_struct *p,long c) {}
static inline int ssa_hpm_exec_check(struct linux_binprm *b) {return 0;}
static inline int ssa_hpm_clone_check(unsigned long f) {return 0;}
static inline void ssa_hpm_exec_ready(unsigned long e,unsigned long a,unsigned long i) {}
static inline void ssa_hpm_exec(struct task_struct *p) {}
static inline long ssa_hpm_prctl(unsigned long o,unsigned long f,unsigned long r,unsigned long t) {return -EINVAL;}
#endif
#if defined(CONFIG_SSA_HPM) && defined(SSA_COST_PROFILE)
void ssa_hpm_cost_exec_begin(void);
void ssa_hpm_cost_exec_end(long result);
#else
static inline void ssa_hpm_cost_exec_begin(void) {}
static inline void ssa_hpm_cost_exec_end(long result) {}
#endif
#endif
