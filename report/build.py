#!/usr/bin/env python3
"""Build the report without leaving TeX intermediates in the source tree."""
import argparse,pathlib,shutil,subprocess,tempfile,zipfile
root=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',help='tectonic or latexmk executable');a=p.parse_args()
engine=a.engine or shutil.which('tectonic') or shutil.which('latexmk')
if not engine:p.error('install Tectonic or latexmk; source/README.md lists the required TeX packages')
with tempfile.TemporaryDirectory(prefix='ssa-report-') as d:
 w=pathlib.Path(d)/'source';shutil.copytree(root/'source',w)
 cmd=[engine,'--keep-logs','main.tex'] if 'tectonic' in pathlib.Path(engine).name else [engine,'-pdf','-interaction=nonstopmode','-halt-on-error','main.tex']
 subprocess.run(cmd,cwd=w,check=True)
 log=(w/'main.log').read_text(errors='replace')
 for marker in ('Overfull','Missing character','There were undefined references'):
  if marker in log:raise SystemExit('Resolve report layout/reference warning: '+marker)
 shutil.copy2(w/'main.pdf',root/'SSA-HPM-report.pdf')
with zipfile.ZipFile(root/'SSA-HPM-overleaf.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
 for f in sorted((root/'source').rglob('*')):
  if f.is_file():
   info=zipfile.ZipInfo(f.relative_to(root/'source').as_posix(),(2026,11,15,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
   z.writestr(info,f.read_bytes())
print('Built report PDF and complete editable source ZIP.')
