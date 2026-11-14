#!/usr/bin/env python3
"""Link a read-only retired memory diagnostic harness against an already built RTL model.

No generated RTL, model object or original simulator is overwritten. A separate
host main prints diagnostic fields every 100000 harness cycles.
"""
import argparse,pathlib,re,subprocess,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--workspace',type=pathlib.Path,required=True);p.add_argument('--config',default='RocketConfig');p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
w=a.workspace.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
b=w/('sims/verilator/generated-src/chipyard.TestHarness.'+a.config);m=b/('chipyard.TestHarness.'+a.config)
h=(m/'VTestHarness___024root.h').read_text();prefix=re.search(r'\b(\w+__DOT__core__DOT__)wb_reg_pc;',h).group(1);root='tile->rootp->'+prefix;csr=root+'csr__DOT__'
s='#include "VTestHarness___024root.h"\n'+(b/'emulator.cc').read_text()
code = r'''    if (!tile->reset && ROOTwb_reg_valid && ROOTwb_ctrl_mem &&
        !ROOTwb_ctrl_fp && ROOTwb_reg_mem_size <= 3 &&
        ROOTwb_ctrl_mem_cmd <= 1 && !ROOTssa_trap_mode &&
        CSRreg_ssa_class_session && CSRreg_scbasereg) {
      fprintf(stderr,"SSA_WB_MEM cycle=%llu pc=%llx va=%llx valid=%u replay=%u exception=%u observe=%u miss=%u rid=%u store=%u size=%u\n",
        (unsigned long long)trace_count,(unsigned long long)ROOTwb_reg_pc,
        (unsigned long long)ROOTwb_reg_wdata,ROOTwb_valid,ROOTreplay_wb,
        ROOTwb_xcpt,ROOTmemoryClassifier_io_observe,ROOTwb_dcache_miss,
        ROOTmemoryClassifier__DOT__stack_top_data,ROOTwb_ctrl_mem_cmd,
        ROOTwb_reg_mem_size);
    }
'''.replace('ROOT',root).replace('CSR',csr)
pos=s.rfind('    tile->clock = 1;');assert pos>0;s=s[:pos]+code+s[pos:]
cc=out/'ssa_progress_emulator.cc';cc.write_text(s);sim=out/'simulator-progress'
f=(m/'VTestHarness.mk').read_text().replace('\temulator \\', '\tssa_progress_emulator \\').replace('emulator.o: '+str(b/'emulator.cc'),'ssa_progress_emulator.o: '+str(cc)).replace(str(w/('sims/verilator/simulator-chipyard-'+a.config))+':',str(sim)+':')
mk=out/'progress-model.mk';mk.write_text(f)
model=m/'VTestHarness__ALL.a';before=hashlib.sha256(model.read_bytes()).hexdigest()
cmd=['make','-C',str(m),'-f',str(mk),str(sim),'CFG_CXXFLAGS_STD_NEWEST=-std=c++17','LINK=/usr/bin/g++ -B/usr/bin/','-j4'];subprocess.run(cmd,check=True)
assert hashlib.sha256(model.read_bytes()).hexdigest()==before
(out/'progress-build.json').write_text(json.dumps(dict(command=cmd,model_sha256=before,model_unchanged=True,simulator_sha256=hashlib.sha256(sim.read_bytes()).hexdigest()),indent=2)+'\n')
print(sim)
