/* SPDX-License-Identifier: BSD-2-Clause
 * Fixed single-hart Chipyard RocketConfig platform for reproducible RTL boots.
 * Uses upstream OpenSBI CLINT, PLIC and HTIF implementations unchanged.
 */
#include <sbi/riscv_asm.h>
#include <sbi/sbi_platform.h>
#include <sbi/sbi_console.h>
#include <sbi_utils/irqchip/plic.h>
#include <sbi_utils/sys/clint.h>
#include <sbi_utils/sys/htif.h>
static struct plic_data plic={.addr=0xc000000,.num_src=1};
static struct clint_data clint={.addr=0x2000000,.first_hartid=0,.hart_count=1,.has_64bit_mmio=TRUE};
static int irq_init(bool cold){int r=0;if(cold)r=plic_cold_irqchip_init(&plic);return r?r:plic_warm_irqchip_init(&plic,0,1);}
static int ipi_init(bool cold){int r=0;if(cold)r=clint_cold_ipi_init(&clint);return r?r:clint_warm_ipi_init();}
static int timer_init(bool cold){int r=0;if(cold)r=clint_cold_timer_init(&clint,NULL);return r?r:clint_warm_timer_init();}
static int hpm_init(bool cold){
#ifdef SSA_CACHE_PROFILE
 csr_write(0x323,0x202); /* native EventSet2 bit1: completed D-cache TL A */
#else
 csr_write(0x323,0x1002); /* event set2, DTLB accepted PTW request bit4 */
#endif
 csr_write(0xb03,0);
 csr_clear(0x320,8);
 csr_clear(0x106,8); /* HPM3 is kernel-managed; U-mode cannot read it. */
 sbi_printf("SSA_HPM_PROFILE selector=%lu width=40 counter=%lu user=%lu\n",csr_read(0x323),csr_read(0xb03),csr_read(0x106)&8);
 return 0;
}
static const struct sbi_platform_operations ops={
 .final_init=hpm_init,
 .console_putc=htif_putc,.console_getc=htif_getc,
 .irqchip_init=irq_init,.ipi_init=ipi_init,.ipi_send=clint_ipi_send,.ipi_clear=clint_ipi_clear,
 .timer_init=timer_init,.timer_value=clint_timer_value,
 .timer_event_start=clint_timer_event_start,.timer_event_stop=clint_timer_event_stop,
 .system_reset=htif_system_reset,
};
const struct sbi_platform platform={
 .opensbi_version=OPENSBI_VERSION,.platform_version=SBI_PLATFORM_VERSION(0,1),
 .name="SSA-HPM RocketConfig hart0",.features=SBI_PLATFORM_DEFAULT_FEATURES,
 .hart_count=1,.hart_stack_size=SBI_PLATFORM_DEFAULT_HART_STACK_SIZE,
 .platform_ops_addr=(unsigned long)&ops,
};
