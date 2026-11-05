# SPDX-License-Identifier: GPL-3.0-or-later
"""Run inside Blender to embed custom Asset Browser previews."""
import bpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ICONS={
    'GP Arrow • Object to Object':'object-to-object',
    'GP Arrow • Project onto Plane':'projection',
    'GP Arrow • Parallel from Origin':'parallel',
    'GP Arrow • Closest Surface Normal':'surface-normal',
    'GP Arrow • Perpendicular in Plane':'perpendicular',
    'GP Arrow • Segment Intersection':'segment-intersection',
}
for name,icon in ICONS.items():
    group=bpy.data.node_groups.get(name)
    if group and group.asset_data:
        group.asset_data.catalog_id='9b930084-69fa-4efa-914a-d6df09d23541'
        with bpy.context.temp_override(id=group):
            bpy.ops.ed.lib_id_load_custom_preview(filepath=str(ROOT/'docs'/'images'/'icons'/f'{icon}.png'))
result={'previews':{name:tuple(bpy.data.node_groups[name].preview.image_size) for name in ICONS if bpy.data.node_groups.get(name)}}
