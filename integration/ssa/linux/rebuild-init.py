#!/usr/bin/env python3
"""Rebuild only the initramfs payload in an existing pinned-source image workspace."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess
p=argparse.ArgumentParser();p.add_argument('--work',type=pathlib.Path,required=True);p.add_argument('--reference-security',action='store_true');p.add_argument('--cross',default='/opt/riscv/bin/riscv64-unknown-elf-');p.add_argument('--name',default='boot-process');a=p.parse_args();w=a.work.resolve();src=pathlib.Path(__file__).resolve().parent
assert (w/'build-report.json').exists(),'Use build-a.py for the initial pinned checkout/build'
config=(w/'linux/.config').read_text();assert ('CONFIG_SSA_HPM=y' in config)!=a.reference_security
assert a.name.replace('-','').isalnum()
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(w/'host-tools/usr/lib/x86_64-linux-gnu')+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
cmds=[]
def run(cmd,cwd=w):
 cmds.append({'argv':list(map(str,cmd)),'cwd':str(cwd)});print('RUN',*map(str,cmd),flush=True);subprocess.run(list(map(str,cmd)),cwd=cwd,env=env,check=True)
flags=['-DREFERENCE','-DREFERENCE_SECURITY'] if a.reference_security else []
run([a.cross+'gcc',*flags,'-march=rv64imac_zicsr','-mabi=lp64','-O1','-nostdlib','-nostartfiles','-static','-ffreestanding','-fno-builtin','-fno-stack-protector','-msmall-data-limit=0','-fno-optimize-sibling-calls','-Wl,--no-relax','-Wl,-e,_start','-Wl,--build-id=none',src/'process-init.c','-o',w/'init'])
run(['make','ARCH=riscv','CROSS_COMPILE='+a.cross,'CC='+a.cross+'gcc -B'+str(w/'host-tools/compiler-bin')+'/', 'LD='+str(w/'host-tools/usr/bin/riscv64-linux-gnu-ld'),'KCFLAGS=-misa-spec=2.2','KAFLAGS=-misa-spec=2.2','-j6','Image'],w/'linux')
run(['make','PLATFORM=ssa_rocket','CROSS_COMPILE='+a.cross,'PLATFORM_RISCV_ISA=rv64imafdc_zicsr_zifencei','platform-cflags-y=-std=gnu11','FW_PAYLOAD_PATH='+str(w/'linux/arch/riscv/boot/Image'),'FW_PAYLOAD_FDT_PATH='+str(w/'rocket.dtb'),'FW_PAYLOAD_FDT_ADDR=0x81e00000','-j6'],w/'opensbi')
shutil.copyfile(w/'opensbi/build/platform/ssa_rocket/firmware/fw_payload.elf',w/(a.name+'.elf'))
run([a.cross+'objcopy','-O','binary',w/(a.name+'.elf'),w/(a.name+'.bin')]);run(['python3',src.parent/'elf_to_hex.py',w/(a.name+'.bin'),w/(a.name+'.hex')])
report={'passed':True,'commands':cmds,'reference_only':a.reference_security,'input_sha256':hashlib.sha256((src/'process-init.c').read_bytes()).hexdigest(),'images':{f:hashlib.sha256((w/(a.name+f)).read_bytes()).hexdigest() for f in ['.elf','.bin','.hex']}}
(w/(a.name+'-report.json')).write_text(json.dumps(report,indent=2)+'\n')
