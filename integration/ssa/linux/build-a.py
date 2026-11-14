#!/usr/bin/env python3
"""Fixed-version baseline boot image. All downloaded/build outputs stay outside Git."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,urllib.request
p=argparse.ArgumentParser();p.add_argument('--work',type=pathlib.Path,required=True);p.add_argument('--cross',default='/opt/riscv/bin/riscv64-unknown-elf-');p.add_argument('--jobs',default='8');p.add_argument('--event',action='store_true');p.add_argument('--process',action='store_true');p.add_argument('--exec',dest='exec_test',action='store_true');p.add_argument('--reference',action='store_true');a=p.parse_args()
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
 d.mkdir();run(['git','init','-b','stage4-linux'],d);run(['git','fetch','--depth=1',url,sha],d);run(['git','checkout','--detach','FETCH_HEAD'],d);return d
linux=checkout('linux','https://github.com/firesim/linux.git','5f5fd87b36e21ed59b759b69eebfa1c74955cb37')
sbi=checkout('opensbi','https://github.com/riscv/opensbi.git','a98258d0b537a295f517bbc8d813007336731fa9')
run(['git','am',src/'0001-stack-pointer-declaration.patch'],linux)
if a.process and not a.reference:run(['git','am',src/'0002-linux-task-pools.patch'],linux)
if a.exec_test and not a.reference:run(['git','am',src/'0003-linux-exec-lifecycle.patch'],linux)
if a.event and not a.reference:run(['git','am',src/'0004-linux-dtlb-event.patch'],linux)
run(['git','am',src/'0001-opensbi-rocket-platform.patch'],sbi)
if a.event and not a.reference:run(['git','am',src/'0002-opensbi-dtlb-profile.patch'],sbi)
url='https://archive.ubuntu.com/ubuntu/pool/main/b/binutils/binutils-riscv64-linux-gnu_2.38-4ubuntu2.12_amd64.deb'
deb=w/'binutils.deb';urllib.request.urlretrieve(url,deb)
assert hashlib.sha256(deb.read_bytes()).hexdigest()=='b20f8bdabeff0a43fba1efdc8b1c1d359d93e8a135d11041fd90ed945c23e866'
host=w/'host-tools';host.mkdir();run(['dpkg-deb','-x',deb,host]);b=host/'compiler-bin';b.mkdir();(b/'ld').symlink_to('../usr/bin/riscv64-linux-gnu-ld');env['LD_LIBRARY_PATH']=str(host/'usr/lib/x86_64-linux-gnu')+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
def user(source,name,flags=[]):
 run([a.cross+'gcc',*flags,'-march=rv64imac_zicsr','-mabi=lp64','-O1','-nostdlib','-nostartfiles','-static','-ffreestanding','-fno-builtin','-fno-stack-protector','-msmall-data-limit=0','-fno-optimize-sibling-calls','-Wl,--no-relax','-Wl,-e,_start','-Wl,--build-id=none',src/source,'-o',w/name])
ref=['-DREFERENCE'] if a.reference else []
user('exec-init.c' if a.exec_test else 'process-init.c' if a.process else 'init.c','init',ref+(['-DCHAIN_EVENTS'] if a.event else []))
if a.exec_test:
 user('exec-init.c','next',ref+['-DNEXT_IMAGE'])
 user('process-init.c','regress',ref+(['-DREFERENCE_SECURITY'] if a.reference else []))
if a.event:
 user('event-init.c','events',ref)
 user('exec-init.c','eventexec',ref+['-DEVENT_SESSION'])
 user('exec-init.c','eventnext',ref+['-DEVENT_SESSION','-DNEXT_IMAGE'])
listing=w/'initramfs.list';contents=f'dir /dev 0755 0 0\nnod /dev/console 0600 0 0 c 5 1\nfile /init {w}/init 0755 0 0\n'
if a.exec_test:contents+=f'file /next {w}/next 0755 0 0\nfile /regress {w}/regress 0755 0 0\n'
if a.event:
 for name in ['events','eventexec','eventnext']:contents+=f'file /{name} {w}/{name} 0755 0 0\n'
listing.write_text(contents)
(linux/'.config').write_text((src/'kernel-a.config').read_text().replace('@INITRAMFS_LIST@',str(listing)))
km=['make','ARCH=riscv','CROSS_COMPILE='+a.cross,'CC='+a.cross+'gcc -B'+str(b)+'/', 'LD='+str(host/'usr/bin/riscv64-linux-gnu-ld')]

if a.process:
 run(['scripts/config','--disable' if a.reference else '--enable','SSA_HPM','--disable','HZ_250','--enable','HZ_1000'],linux)
run(km+['olddefconfig'],linux);run(km+['KCFLAGS=-misa-spec=2.2','KAFLAGS=-misa-spec=2.2','-j'+a.jobs,'Image'],linux)
run(['dtc','-I','dts','-O','dtb','-o',w/'rocket.dtb',src/'rocket.dts'])
run(['make','PLATFORM=ssa_rocket','CROSS_COMPILE='+a.cross,'PLATFORM_RISCV_ISA=rv64imafdc_zicsr_zifencei','platform-cflags-y=-std=gnu11','FW_PAYLOAD_PATH='+str(linux/'arch/riscv/boot/Image'),'FW_PAYLOAD_FDT_PATH='+str(w/'rocket.dtb'),'FW_PAYLOAD_FDT_ADDR=0x81e00000','-j'+a.jobs],sbi)
shutil.copyfile(sbi/'build/platform/ssa_rocket/firmware/fw_payload.elf',w/'boot-a.elf');run([a.cross+'objcopy','-O','binary',w/'boot-a.elf',w/'boot-a.bin']);run(['python3',src.parent/'elf_to_hex.py',w/'boot-a.bin',w/'boot-a.hex'])
(w/'build-report.json').write_text(json.dumps(dict(passed=True,commands=commands,images={f:hashlib.sha256((w/f).read_bytes()).hexdigest() for f in ['boot-a.elf','boot-a.bin','boot-a.hex']}),indent=2)+'\n')
