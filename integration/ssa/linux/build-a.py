#!/usr/bin/env python3
"""Fixed-version baseline boot image. All downloaded/build outputs stay outside Git."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,urllib.request
p=argparse.ArgumentParser();p.add_argument('--work',type=pathlib.Path,required=True);p.add_argument('--cross',default='/opt/riscv/bin/riscv64-unknown-elf-');p.add_argument('--jobs',default='8');a=p.parse_args()
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
run(['git','am',src/'0001-opensbi-rocket-platform.patch'],sbi)
url='https://archive.ubuntu.com/ubuntu/pool/main/b/binutils/binutils-riscv64-linux-gnu_2.38-4ubuntu2.12_amd64.deb'
deb=w/'binutils.deb';urllib.request.urlretrieve(url,deb)
assert hashlib.sha256(deb.read_bytes()).hexdigest()=='b20f8bdabeff0a43fba1efdc8b1c1d359d93e8a135d11041fd90ed945c23e866'
host=w/'host-tools';host.mkdir();run(['dpkg-deb','-x',deb,host]);b=host/'compiler-bin';b.mkdir();(b/'ld').symlink_to('../usr/bin/riscv64-linux-gnu-ld');env['LD_LIBRARY_PATH']=str(host/'usr/lib/x86_64-linux-gnu')+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
run([a.cross+'gcc','-march=rv64gc','-mabi=lp64d','-O1','-nostdlib','-nostartfiles','-static','-fno-builtin','-fno-stack-protector','-Wl,-e,_start','-Wl,--build-id=none',src/'init.c','-o',w/'init'])
listing=w/'initramfs.list';listing.write_text(f'dir /dev 0755 0 0\nnod /dev/console 0600 0 0 c 5 1\nfile /init {w}/init 0755 0 0\n')
(linux/'.config').write_text((src/'kernel-a.config').read_text().replace('@INITRAMFS_LIST@',str(listing)))
km=['make','ARCH=riscv','CROSS_COMPILE='+a.cross,'CC='+a.cross+'gcc -B'+str(b)+'/', 'LD='+str(host/'usr/bin/riscv64-linux-gnu-ld')]
run(km+['olddefconfig'],linux);run(km+['KCFLAGS=-misa-spec=2.2','KAFLAGS=-misa-spec=2.2','-j'+a.jobs,'Image'],linux)
run(['dtc','-I','dts','-O','dtb','-o',w/'rocket.dtb',src/'rocket.dts'])
run(['make','PLATFORM=ssa_rocket','CROSS_COMPILE='+a.cross,'PLATFORM_RISCV_ISA=rv64imafdc_zicsr_zifencei','platform-cflags-y=-std=gnu11','FW_PAYLOAD_PATH='+str(linux/'arch/riscv/boot/Image'),'FW_PAYLOAD_FDT_PATH='+str(w/'rocket.dtb'),'FW_PAYLOAD_FDT_ADDR=0x81e00000','-j'+a.jobs],sbi)
shutil.copyfile(sbi/'build/platform/ssa_rocket/firmware/fw_payload.elf',w/'boot-a.elf');run([a.cross+'objcopy','-O','binary',w/'boot-a.elf',w/'boot-a.bin']);run(['python3',src.parent/'elf_to_hex.py',w/'boot-a.bin',w/'boot-a.hex'])
(w/'build-report.json').write_text(json.dumps(dict(passed=True,commands=commands,images={f:hashlib.sha256((w/f).read_bytes()).hexdigest() for f in ['boot-a.elf','boot-a.bin','boot-a.hex']}),indent=2)+'\n')
