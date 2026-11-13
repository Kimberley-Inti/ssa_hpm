/* SPDX-License-Identifier: MIT */
#include "syscall.h"
extern void capacity_parent(U*);
static U word;
__attribute__((noreturn)) void plain_main(U *stack){(void)stack;word=7;capacity_parent(&word);out("PLAIN_CAPACITY_OK\n");die(0);}
