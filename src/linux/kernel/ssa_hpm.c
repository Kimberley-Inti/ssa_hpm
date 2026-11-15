// SPDX-License-Identifier: GPL-2.0-only
/* Single-hart SSA-HPM prototype. Physical pools are outside managed Linux RAM. */
#include <linux/init.h>
#include <linux/capability.h>
#include <linux/binfmts.h>
#include <linux/sched/signal.h>
#include <linux/fs.h>
#include <linux/io.h>
#include <linux/slab.h>
#include <linux/sched.h>
#include <linux/sched/task_stack.h>
#include <linux/cred.h>
#include <linux/irqflags.h>
#include <linux/ssa_hpm.h>
#include <asm/csr.h>
#include <asm/processor.h>
#define TOP_SIZE 0x105000UL
#define POOL_SIZE 37748736UL
#define MAX_EVENTS 12
#define RECORD_SLOTS 262144U
#define EXPORT_CHUNK 16U
#define XS_OPEN 1U
#define XS_SPILL 2U
#define XS_ALLOC 4U
#define XS_STATE 8U
#define XS_META 16U
#define XS_IO 32U
#define RUNNING 1
#define PAUSED 2
#define STOPPED 3
struct ssa_record {u64 callee,parent,count[3],reserved[6],next,rsv,pad[3];};
struct ssa_pool {unsigned long base; void *top; struct ssa_record *records; bool busy;};
struct ssa_event {
#ifdef SSA_COST_PROFILE
 u64 pause_cost[3],resume_cost[3];
#endif
 u64 s[4],r[4],depth,rid,cause,csr_cause; int other,from; unsigned long task_state,nivcsw; bool resumed,preempt;};
struct ssa_hpm_state {
 struct ssa_pool *pool;
#ifdef SSA_COST_PROFILE
 u64 init_cost[3];
#endif
 unsigned int state,role,test,uid,n;
 bool event,classify;
 bool frozen,exported;
 u64 cutoff[4],open_ids[256];
 bool legacy,bad,proof_seen,proof_valid;
 u64 session, image_id;
 u64 off[4],orig[4],common_off[4];
 struct ssa_event events[MAX_EVENTS];
};
static struct ssa_pool pools[2]={{.base=0x88000000UL},{.base=0x8c000000UL}};
static bool available,event_available;
static u64 next_session;
static volatile u64 *meta(struct ssa_pool *p){return (void *)((char *)p->top+TOP_SIZE-64);}
static volatile u64 *frame(struct ssa_pool *p,u64 n){return (void *)((char *)meta(p)-n*64);}
#define EVENT_MASK ((1ULL<<40)-1)
#ifdef SSA_CACHE_PROFILE
#define HPM_SELECTOR 514U
#define HPM_NAME "dcache_a_transactions"
#define HPM_FIELD "cache"
#else
#define HPM_SELECTOR 4098U
#define HPM_NAME "dtlb_accepted_ptw_requests"
#define HPM_FIELD "dtlb"
#endif
static unsigned int nr(struct ssa_hpm_state *p){return p->event?4:3;}
static void sample(u64 *v,bool event){
 asm volatile("fence rw,rw; csrr %0,cycle; csrr %1,instret; csrr %2,time"
  :"=r"(v[0]),"=r"(v[1]),"=r"(v[2])::"memory");
 if(event)asm volatile("csrr %0,0xc03":"=r"(v[3])::"memory");
}
/* Optional measurement build only. Never print inside the scheduler path. */
#ifdef SSA_COST_PROFILE
static void cost_delta(u64 *out,const u64 *start) {
 u64 end[3];unsigned int j;sample(end,false);
 for(j=0;j<3;j++)out[j]=end[j]-start[j];
}
static void cost_print(const char *phase,u64 session,const u64 *v,u64 detail) {
 pr_emerg("SSA_COST phase=%s pid=%d session=%llu cycle=%llu instret=%llu time=%llu detail=%llu\n",phase,current->pid,session,v[0],v[1],v[2],detail);
}
#endif
#ifdef SSA_COST_PROFILE
void ssa_hpm_cost_exec_begin(void) {
 if(current->ssa_launch_test==14 || (current->ssa_hpm && current->ssa_hpm->test==14)){
  sample(current->ssa_cost_exec_start,false);current->ssa_cost_exec_pending=true;
 }
}
void ssa_hpm_cost_exec_end(long result) {
 if(current->ssa_cost_exec_pending){
  u64 v[3];cost_delta(v,current->ssa_cost_exec_start);current->ssa_cost_exec_pending=false;
  cost_print(result<0?"exec_failed":"exec_ready",current->ssa_hpm?current->ssa_hpm->session:0,v,(u64)result);
 }
}
#endif
static void select_pool(unsigned long b,bool event){
 if(!b)csr_write(0x5c1,0);
 if(event)csr_set(0x5c0,2);else csr_clear(0x5c0,2);
 asm volatile("csrw 0x800,%0"::"r"(b):"memory");}
static unsigned long selected(void){unsigned long b;asm volatile("csrr %0,0x800":"=r"(b));return b;}
static void pause_task(struct task_struct *t,struct task_struct *other,bool preempt)
{
 struct ssa_hpm_state *p=t->ssa_hpm; struct ssa_event *e;
 volatile u64 *m=meta(p->pool);u64 depth=READ_ONCE(m[0]);unsigned int j;
 if(p->state!=RUNNING)return;
 if(selected()!=p->pool->base || depth>256 || p->n>=MAX_EVENTS){p->bad=true;select_pool(0,false);p->state=STOPPED;return;}
 e=&p->events[p->n++]; e->depth=depth;e->other=other?other->pid:0;e->preempt=preempt;
 e->task_state=READ_ONCE(t->state);e->nivcsw=t->nivcsw;
 e->cause=task_pt_regs(t)->cause;e->csr_cause=csr_read(CSR_SCAUSE);
 if(depth)e->rid=READ_ONCE(frame(p->pool,depth)[0]);
 if(depth>=2 && READ_ONCE(frame(p->pool,2)[0])==2){
  if(!p->proof_seen){for(j=0;j<nr(p);j++)p->orig[j]=READ_ONCE(frame(p->pool,2)[j+1]);p->proof_seen=true;p->proof_valid=true;}
  else for(j=0;j<nr(p);j++)if(READ_ONCE(frame(p->pool,2)[j+1])!=((p->orig[j]+(p->legacy?0:p->common_off[j]))&(j==3?EVENT_MASK:~0ULL)))p->proof_valid=false;
 }
 sample(e->s,p->event);select_pool(0,false);p->state=PAUSED;
}
static void resume_task(struct task_struct *t,struct task_struct *other)
{
 struct ssa_hpm_state *p=t->ssa_hpm;struct ssa_event *e;
 volatile u64 *m;u64 d[4],n;unsigned int j;
 if(p->state!=PAUSED)return;
 if(selected() || !p->n){p->bad=true;select_pool(0,false);p->state=STOPPED;return;}
 e=&p->events[p->n-1];m=meta(p->pool);n=READ_ONCE(m[0]);
 if(n!=e->depth || n>256){p->bad=true;p->state=STOPPED;return;}
 sample(e->r,p->event);e->resumed=true;e->from=other?other->pid:0;
 for(j=0;j<nr(p);j++){d[j]=(e->r[j]-e->s[j])&(j==3?EVENT_MASK:~0ULL);p->off[j]=(p->off[j]+d[j])&(j==3?EVENT_MASK:~0ULL);}
 if(p->proof_seen && n>=2 && READ_ONCE(frame(p->pool,2)[0])==2)
  for(j=0;j<nr(p);j++)p->common_off[j]=(p->common_off[j]+d[j])&(j==3?EVENT_MASK:~0ULL);
 if(!p->legacy)for(n=1;n<=e->depth;n++)for(j=0;j<nr(p);j++){
  volatile u64 *f=frame(p->pool,n);WRITE_ONCE(f[j+1],(READ_ONCE(f[j+1])+d[j])&(j==3?EVENT_MASK:~0ULL));
 }
 p->state=RUNNING;csr_write(0x5c1,p->classify?p->session:0);select_pool(p->pool->base,p->event);
}
void ssa_hpm_fork(struct task_struct *t){
#ifdef SSA_COST_PROFILE
 t->ssa_cost_exec_pending=false;
#endif
 t->ssa_hpm=NULL;t->ssa_launch_policy=0;t->ssa_launch_role=0;t->ssa_launch_test=0;t->ssa_launch_error=0;
}
void ssa_hpm_fork_done(struct task_struct *t){
 if(current->ssa_launch_policy)pr_emerg("SSA_AUTO_FORK parent=%d child=%d inherited=0 test=%u\n",current->pid,t->pid,current->ssa_launch_test);
}
int ssa_hpm_clone_check(unsigned long flags){
 if((current->ssa_launch_policy || current->ssa_hpm) && (flags&CLONE_THREAD)){
  pr_emerg("SSA_AUTO_REJECT pid=%d reason=threads errno=95\n",current->pid);return -EOPNOTSUPP;
 }
 return 0;
}
int ssa_hpm_exec_check(struct linux_binprm *bprm){
 const char *reason=NULL;
 if(!current->ssa_launch_policy)return 0;
 if(!task_no_new_privs(current))reason="no_new_privs";
 else if(get_nr_threads(current)!=1)reason="threads";
 else if(bprm->recursion_depth!=1)reason="format";
 else if(file_inode(bprm->file)->i_mode&(S_ISUID|S_ISGID))reason="setid";
 else if(!uid_eq(bprm->cred->euid,current_euid()) || !gid_eq(bprm->cred->egid,current_egid()))reason="credentials";
 if(reason){current->ssa_launch_error=-EPERM;pr_emerg("SSA_AUTO_REJECT pid=%d reason=%s errno=1\n",current->pid,reason);return -EPERM;}
 return 0;
}
void ssa_hpm_switch(struct task_struct *prev,struct task_struct *next,bool preempt)
{
 if(!available)return;
#ifdef SSA_COST_PROFILE
 if(prev->ssa_hpm && prev->ssa_hpm->test==14 && prev->ssa_hpm->state==RUNNING){
  u64 a[3];struct ssa_hpm_state *p=prev->ssa_hpm;sample(a,false);pause_task(prev,next,preempt);
  if(p->n)cost_delta(p->events[p->n-1].pause_cost,a);
 }else
#endif
 if(prev->ssa_hpm)pause_task(prev,next,preempt);
 else select_pool(0,false);
#ifdef SSA_COST_PROFILE
 if(next->ssa_hpm && next->ssa_hpm->test==14 && next->ssa_hpm->state==PAUSED){
  u64 a[3];struct ssa_hpm_state *p=next->ssa_hpm;sample(a,false);resume_task(next,prev);
  if(p->n)cost_delta(p->events[p->n-1].resume_cost,a);
 }else
#endif
 if(next->ssa_hpm)resume_task(next,prev);
}
static long export_session(struct task_struct *t,const char *reason,bool release);
long ssa_hpm_prctl(unsigned long op,unsigned long flags,unsigned long role,unsigned long test)
{
 struct ssa_hpm_state *p=current->ssa_hpm;unsigned long irq;unsigned int i;
 if(!available)return -ENODEV;
 if(op==6 || op==7){
  if(!capable(CAP_SYS_ADMIN))return -EPERM;
  if(p)return -EBUSY;
  if(op==7){if(flags || role || test)return -EINVAL;current->ssa_launch_policy=0;return 0;}
  if(flags>7 || role>2 || test>14)return -EINVAL;
  if(!task_no_new_privs(current) || get_nr_threads(current)!=1)return -EPERM;
  current->ssa_launch_policy=0x100|flags;current->ssa_launch_role=role;current->ssa_launch_test=test;current->ssa_launch_error=0;
  pr_emerg("SSA_AUTO_ARM pid=%d flags=%lu role=%lu test=%lu fork_inherit=0 exec_inherit=1\n",current->pid,flags,role,test);
  return 0;
 }
 if(op==1){
  if(get_nr_threads(current)!=1)return -EOPNOTSUPP;
  if(flags>7 || role>2 || test>14)return -EINVAL;
  if((flags&2) && !event_available)return -ENODEV;
  if(p)return -EBUSY;
  p=kzalloc(sizeof(*p),GFP_KERNEL);if(!p)return -ENOMEM;
  local_irq_save(irq);
  for(i=0;i<ARRAY_SIZE(pools);i++)if(!pools[i].busy)break;
  if(i==ARRAY_SIZE(pools)){local_irq_restore(irq);kfree(p);return -EBUSY;}
  p->pool=&pools[i];p->pool->busy=true;p->legacy=flags&1;p->event=!!(flags&2);p->classify=!!(flags&4);p->role=role;p->test=test;
  p->uid=__kuid_val(current_uid());p->state=RUNNING;
  p->session=++next_session;p->image_id=READ_ONCE(current->self_exec_id);
#ifdef SSA_COST_PROFILE
  if(test==14)sample(p->init_cost,false);
#endif
  memset((char *)p->pool->top+TOP_SIZE-1065024,0,262144*4);
  memset((void *)meta(p->pool),0,64);WRITE_ONCE(meta(p->pool)[1],1);
  current->ssa_hpm=p;asm volatile("fence rw,rw":::"memory");select_pool(p->pool->base,p->event);
  csr_write(0x5c1,p->classify?p->session:0);
  if(p->classify){
   csr_write(0x5c3,i);csr_write(0x5c2,1);
   while(csr_read(0x5c2)&2)cpu_relax();
   csr_write(0x5c3,0);
  }
#ifdef SSA_COST_PROFILE
  if(test==14){u64 a[3];memcpy(a,p->init_cost,sizeof(a));cost_delta(p->init_cost,a);}
#endif
  pr_emerg("SSA_BEGIN pid=%d session=%llu image=%llu pool=%lu depth=%llu next=%llu selector=%lu\n",current->pid,p->session,p->image_id,p->pool->base,READ_ONCE(meta(p->pool)[0]),READ_ONCE(meta(p->pool)[1]),selected());
  if(p->event)pr_emerg("SSA_EVENT_BEGIN pid=%d session=%llu abi=2 selector=%u width=40 depth=0 next=1 profile=%s\n",current->pid,p->session,HPM_SELECTOR,HPM_NAME);
  local_irq_restore(irq);return 0;
 }
 if(flags || role || test)return -EINVAL;
 if(op==3){
  local_irq_save(irq);i=!p && !selected();local_irq_restore(irq);
  if(i)pr_emerg("SSA_UNMONITORED pid=%d selector=0\n",current->pid);
  return i?0:1;
 }
 if(op==4){
  if(!p)return -EINVAL;
  local_irq_save(irq);
  if(p->state!=RUNNING || selected()!=p->pool->base || p->bad){local_irq_restore(irq);return -EIO;}
  i=READ_ONCE(meta(p->pool)[0]);
  pr_emerg("SSA_CHECK pid=%d session=%llu image=%llu depth=%u next=%llu selector=%lu\n",current->pid,p->session,p->image_id,i,READ_ONCE(meta(p->pool)[1]),selected());
  local_irq_restore(irq);return i;
 }
 if(op==5){
  if(!p)return -EINVAL;
  if(p->state!=STOPPED)return -EBUSY;
  if(p->exported)return -EALREADY;
  return export_session(current,"stop",false);
 }
 if(op!=2 || !p)return -EINVAL;
 local_irq_save(irq);
 if(p->state!=RUNNING || selected()!=p->pool->base || p->bad){local_irq_restore(irq);return -EIO;}
 if(READ_ONCE(meta(p->pool)[0]) || READ_ONCE(meta(p->pool)[2])){local_irq_restore(irq);return -EBUSY;}
 sample(p->cutoff,p->event);select_pool(0,false);p->frozen=true;p->state=STOPPED;i=READ_ONCE(meta(p->pool)[1]);
 local_irq_restore(irq);return i?i-1:-EIO;
}
/* Word checksum v1: bounded corruption detection, not authentication. */
static u64 export_hash(u64 h,u64 x){return (h^x)*1099511628211ULL;}
static int read_chunk(struct task_struct *t,struct ssa_hpm_state *p,u64 sid,
                      u64 total,u64 first,unsigned int count,struct ssa_record *out)
{
 void *v;
 if(t!=current || t->ssa_hpm!=p || p->session!=sid || !p->pool->busy ||
    p->state!=STOPPED || !p->frozen)return -ESTALE;
 if(total>=RECORD_SLOTS || !first || !count || count>EXPORT_CHUNK ||
    first>total || count>total-first+1)return -ERANGE;
 v=memremap(p->pool->base-POOL_SIZE+first*sizeof(*out),count*sizeof(*out),MEMREMAP_WB);
 if(!v)return -ENOMEM;
 memcpy(out,v,count*sizeof(*out));memunmap(v);return 0;
}
/* Read one frozen sidecar row. IRQ exclusion protects the hart CSR selector;
 * pool ownership protects the epoch bank until XRELEASE. No user selector API. */
static void class_row(struct ssa_hpm_state *p,unsigned int id,u64 v[8])
{
 unsigned long irq;
 local_irq_save(irq);
 csr_write(0x5c1,p->session);csr_write(0x5c3,id);
 v[0]=csr_read(0x5c4);v[1]=csr_read(0x5c5);v[2]=csr_read(0x5c6);v[3]=csr_read(0x5c7);
 v[4]=csr_read(0x5c8);v[5]=csr_read(0x5c9);v[6]=csr_read(0x5ca);v[7]=csr_read(0x5cb);
 csr_write(0x5c1,0);
 local_irq_restore(irq);
}
static void export_class(struct ssa_hpm_state *p,u64 total)
{
 u64 v[8],h=14695981039346656037ULL;unsigned int i,j,n=min_t(u64,total,63);
 class_row(p,0,v);
 pr_emerg("SSA_MBEGIN version=1 rule=1 session=%llu total=%llu emitted=%u width=64 aggregation=exclusive scope=retired_integer_virtual history=16 capacity=63 status=%llu depth=%llu spill=%llu unframed=%llu inputs=%llu evictions=%llu dropped=%llu\n",p->session,total,n,v[0],v[1],v[2],v[3],v[5],v[6],v[7]);
 for(i=1;i<=n;i++){
  class_row(p,i,v);
  pr_emerg("SSA_MRECORD session=%llu id=%u total=%llu warmup=%llu scalar=%llu stream=%llu irregular=%llu\n",p->session,i,v[0],v[1],v[2],v[3],v[4]);
  h=export_hash(h,i);for(j=0;j<5;j++)h=export_hash(h,v[j]);
  cond_resched();
 }
 pr_emerg("SSA_MEND session=%llu emitted=%u hash=%016llx\n",p->session,n,h);
}
static long export_session(struct task_struct *t,const char *reason,bool release)
{
 struct ssa_hpm_state *p=t->ssa_hpm;unsigned long irq;unsigned int i,j,status=0;
 volatile u64 *m;u64 depth,next,spill,errors,total,emitted=0,seq=0,allhash=14695981039346656037ULL;
 u64 *open_ids;struct ssa_record *buf=NULL;bool complete;
#ifdef SSA_COST_PROFILE
 u64 cost_start[3],cost_freeze[3],cost_total[3],cost_copy[3]={0};
 if(p && p->test==14)sample(cost_start,false);
#endif
 if(!p)return -EINVAL;
 open_ids=p->open_ids;
 /* Own descriptor remains attached and slot busy until terminal/release. */
 if(p->exported)goto done;
 local_irq_save(irq);
 if(!p->frozen){sample(p->cutoff,p->event);select_pool(0,false);p->frozen=true;}
 p->state=STOPPED;m=meta(p->pool);
 depth=READ_ONCE(m[0]);next=READ_ONCE(m[1]);spill=READ_ONCE(m[2]);errors=READ_ONCE(m[3]);
 if(depth)status|=XS_OPEN;
 if(spill)status|=XS_SPILL;
 if(errors)status|=XS_ALLOC;
 if(p->bad)status|=XS_STATE;
 if(!next || next>RECORD_SLOTS || depth>256)status|=XS_META;
 total=(!next || next>RECORD_SLOTS)?0:next-1;
 for(i=0;i<depth && i<256;i++){open_ids[i]=READ_ONCE(frame(p->pool,i+1)[0]);if(!open_ids[i] || open_ids[i]>total)status|=XS_META;}
 local_irq_restore(irq);
 /* No monitor selection; IRQs may run and scheduler may select another pool.
  * This task stays STOPPED. It never touches SCBaseReg again while exporting. */
#ifdef SSA_COST_PROFILE
 if(p->test==14)cost_delta(cost_freeze,cost_start);
#endif
 complete=!status;
 pr_emerg("SSA_SESSION pid=%d session=%llu image=%llu reason=%s comm=%s selector=0 cutoff_cycle=%llu cutoff_instret=%llu cutoff_time=%llu\n",t->pid,p->session,p->image_id,reason,t->comm,p->cutoff[0],p->cutoff[1],p->cutoff[2]);
 pr_emerg("SSA_EXPORT pid=%d uid=%u role=%u test=%u legacy=%u pool=%lu complete=%u depth=%llu next=%llu spill=%llu events=%u session=%llu\n",t->pid,p->uid,p->role,p->test,p->legacy,p->pool->base,complete,depth,next,spill,p->n,p->session);
 for(i=0;i<p->n;i++){
  struct ssa_event *e=&p->events[i];
  pr_emerg("SSA_SWITCH pid=%d test=%u role=%u event=%u to=%d from=%d depth=%llu rid=%llu state=%lu ivcsw=%lu cause=%016llx csr_cause=%016llx resumed=%u preempt=%u session=%llu\n",t->pid,p->test,p->role,i,e->other,e->from,e->depth,e->rid,e->task_state,e->nivcsw,e->cause,e->csr_cause,e->resumed,e->preempt,p->session);
  for(j=0;j<nr(p);j++)pr_emerg("SSA_SAMPLE pid=%d event=%u counter=%u S=%016llx R=%016llx delta=%016llx session=%llu\n",t->pid,i,j,e->s[j],e->r[j],(e->r[j]-e->s[j])&(j==3?EVENT_MASK:~0ULL),p->session);
 }
 pr_emerg("SSA_XBEGIN version=1 session=%llu pid=%d image=%llu abi=%u total=%llu capacity=%u chunk=%u counters=%u reason=%s pool=%lu next=%llu depth=%llu spill=%llu errors=%llu status=%u legacy=%u policy=%s profile=%s classification=%u class_rule=%u class_rows=%u\n",p->session,t->pid,p->image_id,p->event?2:1,total,RECORD_SLOTS-1,EXPORT_CHUNK,nr(p),reason,p->pool->base,next,depth,spill,errors,status,p->legacy,p->legacy?"interval_inclusive_no_rebase":"interval_inclusive_pause_rebase",p->event?HPM_NAME:"base",p->classify,p->classify?1:0,p->classify?(unsigned int)min_t(u64,total,63):0);
 for(j=0;j<nr(p);j++){
  static const char *names[]={"cycle","instret","time",HPM_NAME};
  pr_emerg("SSA_XCOUNTER session=%llu index=%u name=%s width=%u selector=%u\n",p->session,j,names[j],j==3?40:64,j==3?HPM_SELECTOR:0);
 }
 if(total)buf=kmalloc_array(EXPORT_CHUNK,sizeof(*buf),GFP_KERNEL);
 if(total && !buf)status|=XS_IO;
 while(emitted<total && !(status&XS_IO)){
  u64 first=emitted+1,h=14695981039346656037ULL;unsigned int count=min_t(u64,EXPORT_CHUNK,total-emitted),k;
#ifdef SSA_COST_PROFILE
  u64 read_start[3],read_cost[3];if(p->test==14)sample(read_start,false);
#endif
  if(read_chunk(t,p,p->session,total,first,count,buf)){status|=XS_IO;break;}
#ifdef SSA_COST_PROFILE
  if(p->test==14){cost_delta(read_cost,read_start);for(j=0;j<3;j++)cost_copy[j]+=read_cost[j];}
#endif
  pr_emerg("SSA_XCHUNK session=%llu seq=%llu first=%llu count=%u\n",p->session,seq,first,count);
  for(k=0;k<count;k++){
   struct ssa_record *r=&buf[k];u64 id=first+k;unsigned int open=0;
   for(i=0;i<depth && i<256;i++)if(open_ids[i]==id)open++;
   pr_emerg("SSA_RECORD pid=%d id=%llu callee=%016llx parent=%llu cycle=%llu instret=%llu time=%llu session=%llu open=%u\n",t->pid,id,r->callee,r->parent,r->count[0],r->count[1],r->count[2],p->session,open);
   if(p->event)pr_emerg("SSA_EVENT_RECORD pid=%d session=%llu id=%llu parent=%llu callee=%016llx " HPM_FIELD "=%llu open=%u\n",t->pid,p->session,id,r->parent,r->callee,r->reserved[0],open);
   {u64 words[]={id,r->parent,r->callee,r->count[0],r->count[1],r->count[2],p->event?r->reserved[0]:0,open};
    for(j=0;j<ARRAY_SIZE(words);j++){h=export_hash(h,words[j]);allhash=export_hash(allhash,words[j]);}}
  }
  emitted+=count;
  pr_emerg("SSA_XCHUNK_END session=%llu seq=%llu count=%u hash=%016llx\n",p->session,seq,count,h);
  seq++;cond_resched();
 }
 kfree(buf);
 if(p->classify)export_class(p,total);
 for(i=0;i<depth && i<256;i++)pr_emerg("SSA_XFRAME session=%llu frame=%u rid=%llu status=abandoned\n",p->session,i+1,open_ids[i]);
 pr_emerg("SSA_XEND session=%llu chunks=%llu emitted=%llu total=%llu hash=%016llx status=%u records_complete=%u\n",p->session,seq,emitted,total,allhash,status,emitted==total && !(status&XS_IO));
 if(p->proof_seen && next==3 && !depth && !spill)for(j=0;j<nr(p);j++){
  u64 final=READ_ONCE(frame(p->pool,2)[j+1]);u64 mask=j==3?EVENT_MASK:~0ULL;u64 diff=(final-p->orig[j])&mask;u64 value=j==3?p->pool->records[2].reserved[0]:p->pool->records[2].count[j];
  pr_emerg("SSA_ACCOUNT pid=%d test=%u role=%u counter=%u original=%016llx final=%016llx off=%016llx recorded=%016llx raw=%016llx valid=%u rebased=%u session=%llu\n",t->pid,p->test,p->role,j,p->orig[j],final,p->common_off[j],value,(value+diff)&mask,p->proof_valid,diff==p->common_off[j],p->session);
 }
 if(p->event)pr_emerg("SSA_EVENT_SESSION pid=%d session=%llu reason=%s cutoff=%llu policy=%lu\n",t->pid,p->session,reason,p->cutoff[3],csr_read(0x5c0));
 if(!strcmp(reason,"exec"))for(i=1;i<=depth && i<=256;i++){
  volatile u64 *f=frame(p->pool,i);
  pr_emerg("SSA_OPEN pid=%d session=%llu frame=%u rid=%llu status=abandoned entry_cycle=%llu entry_instret=%llu entry_time=%llu\n",t->pid,p->session,i,READ_ONCE(f[0]),READ_ONCE(f[1]),READ_ONCE(f[2]),READ_ONCE(f[3]));
  if(p->event)pr_emerg("SSA_EVENT_OPEN pid=%d session=%llu frame=%u rid=%llu entry=%llu\n",t->pid,p->session,i,READ_ONCE(f[0]),READ_ONCE(f[4]));
 }
 if(!strcmp(reason,"exec"))pr_emerg("SSA_EXEC_END pid=%d session=%llu complete=%u selector=0\n",t->pid,p->session,!status);
 else if(!strcmp(reason,"exit"))pr_emerg("SSA_EXIT pid=%d complete=%u selector=0 session=%llu\n",t->pid,!status,p->session);
#ifdef SSA_COST_PROFILE
 if(p->test==14){
  cost_delta(cost_total,cost_start);
  cost_print("dictionary_init",p->session,p->init_cost,1048576);
  cost_print("freeze",p->session,cost_freeze,depth);
  cost_print("record_copy",p->session,cost_copy,total);
  cost_print("export",p->session,cost_total,total);
  for(i=0;i<p->n;i++){
   cost_print("pause",p->session,p->events[i].pause_cost,p->events[i].depth);
   if(p->events[i].resumed)cost_print("resume",p->session,p->events[i].resume_cost,p->events[i].depth);
  }
 }
#endif
 p->exported=true;
done:
 if(release){
  pr_emerg("SSA_XRELEASE session=%llu pid=%d pool=%lu reason=%s\n",p->session,t->pid,p->pool->base,reason);
  local_irq_save(irq);p->pool->busy=false;t->ssa_hpm=NULL;local_irq_restore(irq);kfree(p);
 }
 return status&XS_IO?-EIO:0;
}
static void finish_session(struct task_struct *t,bool exec){export_session(t,exec?"exec":"exit",true);}
void ssa_hpm_exit(struct task_struct *t,long code){
 if(t->ssa_launch_policy)pr_emerg("SSA_AUTO_END pid=%d code=%ld signal=%ld monitored=%u error=%d\n",t->pid,code,code&127,!!t->ssa_hpm,t->ssa_launch_error);
 finish_session(t,false);
}
/* Called only after exec_mmap has committed: old userspace cannot return. */
void ssa_hpm_exec(struct task_struct *t){finish_session(t,true);}
/* ELF ready: mappings/creds/stack finalized and start_thread prepared, no U instruction yet.
 * The old session was retired only at exec_mmap commitment. A late loader failure
 * never calls this hook, and ordinary ENOENT returns with the old descriptor. */
void ssa_hpm_exec_ready(unsigned long entry,unsigned long app,unsigned long interp){
 long error;
 if(!current->ssa_launch_policy){ssa_hpm_cost_exec_end(0);return;}
 error=ssa_hpm_prctl(1,current->ssa_launch_policy&7,current->ssa_launch_role,current->ssa_launch_test);
 current->ssa_launch_error=error;
 if(error)select_pool(0,false);
 pr_emerg("SSA_AUTO_RESULT pid=%d image=%llu test=%u role=%u flags=%u enabled=%u error=%ld reason=%s dynamic=%u entry=%016lx app=%016lx interp=%016lx session=%llu\n",current->pid,(u64)current->self_exec_id,current->ssa_launch_test,current->ssa_launch_role,current->ssa_launch_policy&7,!error,error,error==-EBUSY?"pool_exhausted":error?"enable_failed":"enabled",!!interp,entry,app,interp,current->ssa_hpm?current->ssa_hpm->session:0);
 ssa_hpm_cost_exec_end(0);
}
static int __init ssa_hpm_init(void)
{
 unsigned int i,j;
 if(num_possible_cpus()!=1)return -EINVAL;
 for(i=0;i<ARRAY_SIZE(pools);i++){
  pools[i].top=memremap(pools[i].base-TOP_SIZE,TOP_SIZE,MEMREMAP_WB);
  pools[i].records=memremap(pools[i].base-POOL_SIZE,8192,MEMREMAP_WB);
  if(!pools[i].top || !pools[i].records){
   for(j=0;j<=i;j++){if(pools[j].top)memunmap(pools[j].top);if(pools[j].records)memunmap(pools[j].records);}
   return -ENOMEM;
  }
 }
 select_pool(0,false);csr_write(0x5c0,3);event_available=!!(csr_read(0x5c0)&2);csr_write(0x5c0,1);available=true;
 pr_emerg("SSA_EVENT_CAPABLE value=%u\n",event_available);
 BUILD_BUG_ON(sizeof(struct ssa_record)!=128);
 pr_emerg("SSA_LINUX_READY user_triggers=1 harts=1 export_limit=%u\n",RECORD_SLOTS-1);
 return 0;
}
late_initcall(ssa_hpm_init);
