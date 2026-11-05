# SPDX-License-Identifier: GPL-3.0-or-later
"""Run inside Blender to export the asset groups to the repository library."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
icon_script=ROOT/'scripts'/'apply_asset_icons.py'
ns={'__file__':str(icon_script),'__name__':'__main__'}
exec(compile(icon_script.read_text(encoding='utf-8'),str(icon_script),'exec'),ns)
assets={g for g in bpy.data.node_groups if g.name.startswith('GP Arrow • ') and g.asset_data}
assert len(assets)==6
bpy.data.libraries.write(str(ROOT/'assets'/'gp_arrow_assets.blend'),assets,path_remap='RELATIVE',fake_user=True,compress=True)
result={'exported':len(assets),'previews':ns['result']['previews']}
