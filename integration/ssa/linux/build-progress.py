#!/usr/bin/env python3
"""Link a read-only PC/CSR progress harness against an already built RTL model.

No generated RTL, model object or original simulator is overwritten. A separate
host main prints diagnostic fields every 100000 harness cycles.
"""
import argparse,pathlib,re,subprocess,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--workspace',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
w=a.workspace.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
b=w/'sims/verilator/generated-src/chipyard.TestHarness.RocketConfig';m=b/'chipyard.TestHarness.RocketConfig'
h=(m/'VTestHarness___024root.h').read_text();prefix=re.search(r'\b(\w+__DOT__core__DOT__)wb_reg_pc;',h).group(1);root='tile->rootp->'+prefix;csr=root+'csr__DOT__'
s='#include "VTestHarness___024root.h"\n'+(b/'emulator.cc').read_text()
code='''    if ((trace_count % 100000) == 0) {
      fprintf(stderr,"SSA_HOST_PROGRESS cycles=%llu pc=%llx prv=%u trapdepth=%u private=%u\\n",
        (unsigned long long)trace_count,(unsigned long long)ROOTwb_reg_pc,
        CSRreg_mstatus_prv,CSRreg_ssa_trap_depth,ROOTssa_trap_mode);
      fprintf(stderr,"SSA_CSR scause=%llx sepc=%llx stval=%llx satp_mode=%u satp_ppn=%llx\\n",
        (unsigned long long)CSRreg_scause,(unsigned long long)CSRreg_sepc,
        (unsigned long long)CSRreg_stval,CSRreg_satp_mode,(unsigned long long)CSRreg_satp_ppn);
    }
'''.replace('ROOT',root).replace('CSR',csr)
# Restore the literal label accidentally touched by the token substitution.
code=code.replace('SSA_'+csr,'SSA_CSR')
s=s.replace('    trace_count++;',code+'    trace_count++;')
cc=out/'ssa_progress_emulator.cc';cc.write_text(s);sim=out/'simulator-progress'
f=(m/'VTestHarness.mk').read_text().replace('\temulator \\', '\tssa_progress_emulator \\').replace('emulator.o: '+str(b/'emulator.cc'),'ssa_progress_emulator.o: '+str(cc)).replace(str(w/'sims/verilator/simulator-chipyard-RocketConfig')+':',str(sim)+':')
mk=out/'progress-model.mk';mk.write_text(f)
model=m/'VTestHarness__ALL.a';before=hashlib.sha256(model.read_bytes()).hexdigest()
cmd=['make','-C',str(m),'-f',str(mk),str(sim),'CFG_CXXFLAGS_STD_NEWEST=-std=c++17','LINK=/usr/bin/g++ -B/usr/bin/','-j4'];subprocess.run(cmd,check=True)
assert hashlib.sha256(model.read_bytes()).hexdigest()==before
(out/'progress-build.json').write_text(json.dumps(dict(command=cmd,model_sha256=before,model_unchanged=True,simulator_sha256=hashlib.sha256(sim.read_bytes()).hexdigest()),indent=2)+'\n')
print(sim)
