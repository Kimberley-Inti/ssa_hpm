/* Minimal Linux PID 1: no target libc is required. */
static long call(long n,long x,long y,long z){register long a0 asm("a0")=x,a1 asm("a1")=y,a2 asm("a2")=z,a7 asm("a7")=n;asm volatile("ecall":"+r"(a0):"r"(a1),"r"(a2),"r"(a7):"memory");return a0;}
void _start(void){
 const char text[]="SSA LINUX A PASS: real userspace PID 1 on Rocket\n";
 if(call(172,0,0,0)==1)call(64,1,(long)text,sizeof(text)-1);
 call(142,0xfee1dead,672274793,0x4321fedc);
 for(;;)call(124,0,0,0);
}
