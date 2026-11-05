# SPDX-License-Identifier: GPL-3.0-or-later
"""Run the Blender checks against examples/gp_arrows_demo.blend."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
checks={}
for path in sorted((ROOT/'tests').glob('check_*.py')):
    ns={'__file__':str(path),'__name__':'__main__'}
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),ns)
    checks[path.stem]=ns.get('result',{})
    print(f'PASS {path.name}')
print(f'TEST_CHECK={len(checks)} validation scripts passed')
