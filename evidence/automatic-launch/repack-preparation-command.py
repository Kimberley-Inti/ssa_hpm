from pathlib import Path
import subprocess,json,os,shutil,hashlib
w=Path('/tmp/ssa-hpm-stage10/uncompressed-linux');p=w/'build-report.json';q=json.loads(p.read_text());env=os.environ.copy();env['PATH']='/usr/bin:/bin:/opt/riscv/bin:'+env['PATH'];env['LD_LIBRARY_PATH']=str(w/'host-tools/usr/lib/x86_64-linux-gnu');commands=[]
def run(argv,cwd):
 c={'argv':list(map(str,argv)),'cwd':str(cwd)};commands.append(c);print('REPACK',c,flush=True);subprocess.run(c['argv'],cwd=cwd,env=env,check=True)
run(['scripts/config','--disable','INITRAMFS_COMPRESSION_GZIP','--enable','INITRAMFS_COMPRESSION_NONE','--set-str','INITRAMFS_SOURCE',str(w/'initramfs.list')],w/'linux')
old=Path('/tmp/ssa-hpm-stage10/independent-linux')
original=next(c for c in q['commands'] if c['argv'][0]=='make' and c['argv'][-1]=='olddefconfig')
km=[v.replace(str(old),str(w)) for v in original['argv'][:-1]]
run(km+['olddefconfig'],w/'linux');run(km+['KCFLAGS=-misa-spec=2.2 -DSSA_CACHE_PROFILE','KAFLAGS=-misa-spec=2.2','-j6','Image'],w/'linux')
old=Path('/tmp/ssa-hpm-stage10/independent-linux')
last=next(c for c in reversed(q['commands']) if c['argv'][0]=='make' and 'PLATFORM=ssa_rocket' in c['argv'])
argv=[v.replace(str(old),str(w)) for v in last['argv']];run(argv,w/'opensbi')
shutil.copyfile(w/'opensbi/build/platform/ssa_rocket/firmware/fw_payload.elf',w/'boot-a.elf')
run(['/opt/riscv/bin/riscv64-unknown-elf-objcopy','-O','binary',w/'boot-a.elf',w/'boot-a.bin'],w)
run(['python3','/home/lxf/chipyard/ssa/elf_to_hex.py',w/'boot-a.bin',w/'boot-a.hex'],w)
q['uncompressed_followup_commands']=commands;q['uncompressed_followup_reason']='Copy independently reconstructed public-source workspace and cached objects; change only initramfs compression to avoid slow C gzip inflate in RTL; same target ELF bytes and model';q['images']={n:hashlib.sha256((w/n).read_bytes()).hexdigest() for n in ['boot-a.elf','boot-a.bin','boot-a.hex']};q['initramfs_compression']='none';p.write_text(json.dumps(q,indent=2)+'\n');assert (w/'linux/usr/initramfs_inc_data').read_bytes()[:6]==b'070701';print('PASS UNCOMPRESSED IMAGE',flush=True)
