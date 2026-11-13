#!/usr/bin/env python3
"""Pinned musl loader and separate ordinary Linux targets; no SSA linked into targets."""
import argparse,pathlib,subprocess,json,os,hashlib,urllib.request,tarfile,shutil
p=argparse.ArgumentParser();p.add_argument('--work',type=pathlib.Path,required=True);p.add_argument('--cross',required=True);p.add_argument('--ld-dir',type=pathlib.Path,required=True);p.add_argument('--musl-cache',type=pathlib.Path);p.add_argument('--jobs',default='6');a=p.parse_args();w=a.work.resolve();src=pathlib.Path(__file__).resolve().parent;env=os.environ.copy();env['LD_LIBRARY_PATH']=str(a.ld_dir.parent/'usr/lib/x86_64-linux-gnu');cmds=[]
def run(cmd,cwd=w):
 cmds.append({'argv':list(map(str,cmd)),'cwd':str(cwd)});subprocess.run(list(map(str,cmd)),cwd=cwd,env=env,check=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
tar=w/'musl-1.2.5.tar.gz';urllib.request.urlretrieve('https://musl.libc.org/releases/musl-1.2.5.tar.gz',tar);assert sha(tar)=='a9a118bbe84d8764da0ea0d28b3ab3fae8477fc7e4085d90102b8596fc7c75e4'
if a.musl_cache:
 musl=a.musl_cache.resolve()
 with tarfile.open(tar) as t:
  for member in t:
   if member.isfile():
    f=musl/pathlib.PurePosixPath(member.name).relative_to('musl-1.2.5');assert f.read_bytes()==t.extractfile(member).read(),str(f)
 assert (musl/'lib/libc.so').exists()
else:
 with tarfile.open(tar) as t:t.extractall(w)
 musl=w/'musl-1.2.5';menv=env.copy();menv['CC']=a.cross+'gcc -B'+str(a.ld_dir)+'/';menv['CROSS_COMPILE']=a.cross
 cmd=['./configure','--target=riscv64-linux-musl','--prefix=/usr','--syslibdir=/lib','--disable-static'];cmds.append({'argv':cmd,'cwd':str(musl),'CC':menv['CC']});subprocess.run(cmd,cwd=musl,env=menv,check=True)
 run(['make','-j'+a.jobs,'lib/libc.so'],musl)
run([a.cross+'objcopy','--strip-unneeded',musl/'lib/libc.so',w/'ld-musl-riscv64.so.1'])
common=[a.cross+'gcc','-B'+str(a.ld_dir)+'/', '-O1','-nostdlib','-nostartfiles','-ffreestanding','-fno-builtin','-fno-stack-protector','-msmall-data-limit=0','-fno-optimize-sibling-calls','-Wl,--no-relax','-Wl,--build-id=none']
static=common+['-march=rv64imac_zicsr','-mabi=lp64','-static','-Wl,-e,_start']
workload=src.parent.parent/'classification/workload.S'
for name,files,flags in [('init',[src/'launcher.c'],[]),('plain',[src/'plain-entry.S',src/'plain.c',workload],[]),('plain-next',[src/'plain-entry.S',src/'plain.c',workload],['-DNEXT_TARGET']),('plain-capacity',[src/'plain-entry.S',src/'capacity.c',src/'capacity.S'],[])]:run(static+flags+files+['-o',w/name])
dyn=common+['-march=rv64gc','-mabi=lp64d']
run(dyn+['-fPIC','-shared','-Wl,-soname,libplain.so','-Wl,-Bsymbolic',src/'shared.c','-o',w/'libplain.so'])
run(dyn+['-DDYNAMIC_TARGET','-Wl,-e,_start','-Wl,--dynamic-linker=/lib/ld-musl-riscv64.so.1','-Wl,-z,now','-Wl,-rpath,/lib',src/'plain-entry.S',src/'plain.c',workload,'-L'+str(w),'-lplain','-o',w/'plain-dynamic'])
# Manual compatibility suite is explicitly not an ordinary target.
run(static+[src.parent/'classification-init.c','-o',w/'class-regress'])
run(static+['-DCLASS_NEXT',src.parent/'classification-init.c','-o',w/'classnext'])
rows={}
for name in ['init','plain','plain-next','plain-capacity','plain-dynamic','libplain.so','ld-musl-riscv64.so.1','class-regress','classnext']:
 elf=w/name;dump=subprocess.check_output([a.cross+'objdump','-d',elf],text=True);syms=subprocess.check_output([a.cross+'readelf','-sW',elf],text=True);ph=subprocess.check_output([a.cross+'readelf','-lW',elf],text=True);dynamic=subprocess.check_output([a.cross+'readelf','-dW',elf],text=True)
 ordinary=name in ['plain','plain-next','plain-capacity','plain-dynamic','libplain.so']
 if ordinary:
  assert '535341' not in dump.lower(),name
  assert not __import__('re').search(r'\ba7,\s*(?:167|0xa7)\b',dump),name
  assert not __import__('re').search(r'\bcsr\w*\s+[^\n]*(?:0x800|0x5c[0-9a-b])',dump),name
  assert not __import__('re').search(r'\bssa_hpm|\bsc_event|\bapi$',syms,__import__('re').M),name
 symbols={}
 for line in syms.splitlines():
  f=line.split()
  if len(f)==8 and f[0][:-1].isdigit() and f[-1] in ['class_common','class_access','scalar_parent','stream_parent','irregular_parent','replace','fail_fork','terminate','hold','task_parent','task_common','capacity_parent','dynamic_parent','shared_inner','shared_entry']:symbols[f[-1]]=int(f[1],16)
 rows[name]={'sha256':sha(elf),'ordinary_target':ordinary,'no_ssa_calls_checked':ordinary,'symbols':symbols,'dynamic_interpreter':'/lib/ld-musl-riscv64.so.1' if name=='plain-dynamic' else None}
 (w/(name+'.disassembly.txt')).write_text(dump)
 if name=='plain-dynamic':assert '/lib/ld-musl-riscv64.so.1' in ph and 'libplain.so' in dynamic
contents='dir /dev 0755 0 0\nnod /dev/console 0600 0 0 c 5 1\ndir /lib 0755 0 0\n'
for name in ['init','plain','plain-next','plain-capacity','plain-dynamic','class-regress','classnext']:contents+=f'file /{name} {w/name} 0755 0 0\n'
contents+=f'file /setid {w}/plain 04755 0 0\nfile /lib/libplain.so {w}/libplain.so 0755 0 0\nfile /lib/ld-musl-riscv64.so.1 {w}/ld-musl-riscv64.so.1 0755 0 0\n'
assert 'file /classnext ' in contents and 'file /plain-next ' in contents
(w/'initramfs.list').write_text(contents)
(w/'transparent-users.json').write_text(json.dumps({'passed':True,'commands':cmds,'musl_version':'1.2.5','musl_source_sha256':sha(tar),'musl_cache_reused':bool(a.musl_cache),'musl_sources_match_pinned_archive':True,'musl_original_loader_sha256':sha(musl/'lib/libc.so'),'inputs':rows},indent=2)+'\n')
print('PASS: separate ordinary ELFs contain no SSA calls, dynamic PT_INTERP/DT_NEEDED verified',flush=True)
