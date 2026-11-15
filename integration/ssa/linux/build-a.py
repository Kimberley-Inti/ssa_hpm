#!/usr/bin/env python3
"""Fixed-version baseline boot image. All downloaded/build outputs stay outside Git."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,urllib.request
p=argparse.ArgumentParser();p.add_argument('--work',type=pathlib.Path,required=True);p.add_argument('--cross',default='/opt/riscv/bin/riscv64-unknown-elf-');p.add_argument('--jobs',default='8');p.add_argument('--export',dest='export_test',action='store_true');p.add_argument('--event',action='store_true');p.add_argument('--cache',action='store_true');p.add_argument('--classification',action='store_true');p.add_argument('--transparent',action='store_true');p.add_argument('--performance',action='store_true');p.add_argument('--performance-switch',action='store_true');p.add_argument('--musl-cache',type=pathlib.Path);p.add_argument('--process',action='store_true');p.add_argument('--exec',dest='exec_test',action='store_true');p.add_argument('--reference',action='store_true');a=p.parse_args()
if a.performance_switch:a.performance=True
if a.performance:a.transparent=True
if a.transparent:a.classification=True
if a.classification:a.cache=True
if a.cache:a.export_test=True
if a.export_test:a.event=True
if a.event:a.exec_test=True
if a.exec_test:a.process=True
src=pathlib.Path(__file__).resolve().parent;w=a.work.resolve();w.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env['PATH']='/usr/bin:/bin:'+str(pathlib.Path(a.cross).parent)+':'+env['PATH'];env.update(GIT_COMMITTER_NAME='SSA-HPM reproduction',GIT_COMMITTER_EMAIL='reproduction@localhost')
commands=[]
def run(cmd,cwd=w):
 commands.append(dict(argv=list(map(str,cmd)),cwd=str(cwd)));print('RUN',*map(str,cmd),flush=True);subprocess.run(list(map(str,cmd)),cwd=cwd,env=env,check=True)
def checkout(name,url,sha):
 d=w/name
 if d.exists():raise SystemExit('Refusing existing source directory: '+str(d))
 d.mkdir();run(['git','init','-b','linux-reconstruction'],d);run(['git','fetch','--depth=1',url,sha],d);run(['git','checkout','--detach','FETCH_HEAD'],d);return d
linux=checkout('linux','https://github.com/firesim/linux.git','5f5fd87b36e21ed59b759b69eebfa1c74955cb37')
sbi=checkout('opensbi','https://github.com/riscv/opensbi.git','a98258d0b537a295f517bbc8d813007336731fa9')
run(['git','am',src/'0001-stack-pointer-declaration.patch'],linux)
if a.process and not a.reference:run(['git','am',src/'0002-linux-task-pools.patch'],linux)
if a.exec_test and not a.reference:run(['git','am',src/'0003-linux-exec-lifecycle.patch'],linux)
if a.event and not a.reference:run(['git','am',src/'0004-linux-dtlb-event.patch'],linux)
if a.export_test and not a.reference:run(['git','am',src/'0005-linux-result-export.patch'],linux)
if a.export_test and not a.reference:run(['git','am',src/'0006-linux-cache-profile.patch'],linux)
if a.classification and not a.reference:run(['git','am',src/'0007-linux-memory-classification.patch'],linux)
if a.transparent and not a.reference:run(['git','am',src/'0008-linux-transparent-launch.patch'],linux)
if a.transparent and not a.reference:run(['git','am',src/'0009-linux-cost-probes.patch'],linux)
if a.classification and not a.reference:run(['git','am',src/'0010-linux-classification-contract.patch'],linux)
run(['git','am',src/'0001-opensbi-rocket-platform.patch'],sbi)
if a.event and not a.reference:run(['git','am',src/'0002-opensbi-dtlb-profile.patch'],sbi)
if a.event and not a.reference:run(['git','am',src/'0003-opensbi-cache-profile.patch'],sbi)
url='https://archive.ubuntu.com/ubuntu/pool/main/b/binutils/binutils-riscv64-linux-gnu_2.38-4ubuntu2.12_amd64.deb'
deb=w/'binutils.deb';urllib.request.urlretrieve(url,deb)
assert hashlib.sha256(deb.read_bytes()).hexdigest()=='b20f8bdabeff0a43fba1efdc8b1c1d359d93e8a135d11041fd90ed945c23e866'
host=w/'host-tools';host.mkdir();run(['dpkg-deb','-x',deb,host]);b=host/'compiler-bin';b.mkdir();(b/'ld').symlink_to('../usr/bin/riscv64-linux-gnu-ld');env['LD_LIBRARY_PATH']=str(host/'usr/lib/x86_64-linux-gnu')+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
def user(source,name,flags=[]):
 run([a.cross+'gcc',*flags,*(['-DCACHE_PROFILE_TEST'] if a.cache else []),'-march=rv64imac_zicsr','-mabi=lp64','-O1','-nostdlib','-nostartfiles','-static','-ffreestanding','-fno-builtin','-fno-stack-protector','-msmall-data-limit=0','-fno-optimize-sibling-calls','-Wl,--no-relax','-Wl,-e,_start','-Wl,--build-id=none',src/source,'-o',w/name])
if a.transparent:
 cmd=['python3',src/'transparent/build-users.py','--work',w,'--cross',a.cross,'--ld-dir',b,'--jobs',a.jobs]
 if a.musl_cache:cmd+=['--musl-cache',a.musl_cache]
 run(cmd);listing=w/'initramfs.list'
 if a.performance:
  shutil.copyfile(w/'init',w/'transparent-init')
  run([a.cross+'gcc','-B'+str(b)+'/', *(['-DSSA_PERF_SWITCH_ONLY'] if a.performance_switch else []),'-march=rv64imac_zicsr','-mabi=lp64','-O1','-nostdlib','-nostartfiles','-static','-ffreestanding','-fno-builtin','-fno-stack-protector','-msmall-data-limit=0','-fno-optimize-sibling-calls','-Wl,--no-relax','-Wl,-e,_start',src/'transparent/plain-entry.S',src.parent/'performance/linux.c','-o',w/'perf-target'])
  shutil.copyfile(w/'perf-target',w/'init')
  listing.write_text(listing.read_text()+f'file /perf-target {w}/perf-target 0755 0 0\n')
  (w/'performance-users.json').write_text(json.dumps({name:hashlib.sha256((w/name).read_bytes()).hexdigest() for name in ['init','perf-target']},indent=2)+'\n')
else:
 ref=['-DREFERENCE'] if a.reference else []
 user('classification-init.c' if a.classification else 'cache-init.c' if a.cache else 'export-init.c' if a.export_test else 'exec-init.c' if a.exec_test else 'process-init.c' if a.process else 'init.c','init',ref+(['-DCHAIN_EVENTS'] if a.event else []))
 if a.export_test:user('exec-init.c','lifecycle',ref+['-DCHAIN_EVENTS'])
 if a.exec_test:
  user('exec-init.c','next',ref+['-DNEXT_IMAGE'])
  user('export-init.c' if a.cache else 'process-init.c','regress',ref+(['-DCACHE_END'] if a.cache else ['-DREFERENCE_SECURITY'] if a.reference else []))
 if a.event:
  user('event-init.c','events',ref)
  user('exec-init.c','eventexec',ref+['-DEVENT_SESSION'])
  user('exec-init.c','eventnext',ref+['-DEVENT_SESSION','-DNEXT_IMAGE'])
 if a.classification:user('classification-init.c','classnext',['-DCLASS_NEXT'])
 listing=w/'initramfs.list';contents=f'dir /dev 0755 0 0\nnod /dev/console 0600 0 0 c 5 1\nfile /init {w}/init 0755 0 0\n'
 if a.exec_test:contents+=f'file /next {w}/next 0755 0 0\nfile /regress {w}/regress 0755 0 0\n'
 if a.event:
  for name in ['events','eventexec','eventnext']:contents+=f'file /{name} {w}/{name} 0755 0 0\n'
 if a.export_test:contents+=f'file /lifecycle {w}/lifecycle 0755 0 0\n'
 if a.classification:contents+=f'file /classnext {w}/classnext 0755 0 0\n'
 listing.write_text(contents)
(linux/'.config').write_text((src/'kernel-a.config').read_text().replace('@INITRAMFS_LIST@',str(listing)).replace('loglevel=7','loglevel=1' if a.transparent else 'loglevel=7'))
km=['make','ARCH=riscv','CROSS_COMPILE='+a.cross,'CC='+a.cross+'gcc -B'+str(b)+'/', 'LD='+str(host/'usr/bin/riscv64-linux-gnu-ld')]

if a.process:
 run(['scripts/config','--disable' if a.reference else '--enable','SSA_HPM','--disable','HZ_250','--enable','HZ_1000'],linux)
if a.transparent:run(['scripts/config','--disable','INITRAMFS_COMPRESSION_GZIP','--enable','INITRAMFS_COMPRESSION_NONE'],linux)
run(km+['olddefconfig'],linux);run(km+['KCFLAGS=-misa-spec=2.2'+(' -DSSA_CACHE_PROFILE' if a.cache else '')+(' -DSSA_COST_PROFILE' if a.performance else ''),'KAFLAGS=-misa-spec=2.2','-j'+a.jobs,'Image'],linux)
run(['dtc','-I','dts','-O','dtb','-o',w/'rocket.dtb',src/'rocket.dts'])
run(['make','PLATFORM=ssa_rocket','CROSS_COMPILE='+a.cross,'PLATFORM_RISCV_ISA=rv64imafdc_zicsr_zifencei','platform-cflags-y=-std=gnu11'+(' -DSSA_CACHE_PROFILE' if a.cache else ''),'FW_PAYLOAD_PATH='+str(linux/'arch/riscv/boot/Image'),'FW_PAYLOAD_FDT_PATH='+str(w/'rocket.dtb'),'FW_PAYLOAD_FDT_ADDR=0x81e00000','-j'+a.jobs],sbi)
shutil.copyfile(sbi/'build/platform/ssa_rocket/firmware/fw_payload.elf',w/'boot-a.elf');run([a.cross+'objcopy','-O','binary',w/'boot-a.elf',w/'boot-a.bin']);run(['python3',src.parent/'elf_to_hex.py',w/'boot-a.bin',w/'boot-a.hex'])
(w/'build-report.json').write_text(json.dumps(dict(passed=True,performance=bool(a.performance),performance_switch=bool(a.performance_switch),linux_tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=linux,text=True).strip(),opensbi_tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=sbi,text=True).strip(),config_sha256=hashlib.sha256((linux/'.config').read_bytes()).hexdigest(),commands=commands,images={f:hashlib.sha256((w/f).read_bytes()).hexdigest() for f in ['boot-a.elf','boot-a.bin','boot-a.hex']}),indent=2)+'\n')
