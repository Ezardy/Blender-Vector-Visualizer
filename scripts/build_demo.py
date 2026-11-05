# SPDX-License-Identifier: GPL-3.0-or-later
"""Build a clean demo in a fresh background Blender process."""
import bpy, importlib.util
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
if not bpy.app.background:
    raise RuntimeError('Run this script with blender --background --factory-startup.')
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(ROOT/'assets'/'gp_arrow_assets.blend'),link=False) as (source,dest):
    dest.node_groups=[n for n in source.node_groups if n.startswith('GP Arrow • ')]
c=bpy.data.collections.new('GP Arrow Examples');bpy.context.scene.collection.children.link(c)
def empty(name,pos):
    o=bpy.data.objects.new(name,None);c.objects.link(o);o.location=pos;o.empty_display_size=.12;return o
def host(name,pos=(0,0,0)):
    o=bpy.data.objects.new(name,bpy.data.grease_pencils.new(name));c.objects.link(o);o.location=pos;o.show_in_front=True;return o
def modifier(o,group,values=None):
    m=o.modifiers.new(group.split(' • ')[-1],'NODES');m.node_group=bpy.data.node_groups[group]
    for s in m.node_group.interface.items_tree:
        if s.item_type=='SOCKET' and s.in_out=='INPUT' and values and s.name in values:
            getattr(m.properties.inputs,s.identifier).value=values[s.name]
    return m
start=empty('Arrow Start',(3,0,1));end=empty('Arrow End',(5,1,3))
style={'Start Object':start,'End Object':end,'Show Label':True,'Label':'v'}
arrow=host('GP Arrow Example');modifier(arrow,'GP Arrow • Object to Object',style)
projection=host('GP Arrow Projection Example');modifier(projection,'GP Arrow • Object to Object',{**style,'Color':(1,.25,.06,1),'Label':'v_xy','Face Camera':False});modifier(projection,'GP Arrow • Project onto Plane')
parallel=host('GP Parallel Arrow Example',(3,-2,.5));modifier(parallel,'GP Arrow • Object to Object',style);modifier(parallel,'GP Arrow • Parallel from Origin',{'Length':1.5})
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,0,0));obstacle=bpy.context.object;obstacle.name='Obstacle'
normal=host('GP Surface Normal Example',(1.3,-.5,.5));modifier(normal,'GP Arrow • Closest Surface Normal',{'Surface Object':obstacle,'Length':1.,'Color':(.15,1,.3,1),'Show Label':True,'Label':'n'})
points=[empty(n,p) for n,p in [('Perpendicular V1 Start',(2,-3,.5)),('Perpendicular V1 End',(3,-3,.5)),('Perpendicular V2 Start',(2,-3,.5)),('Perpendicular V2 End',(2.5,-2,.5))]]
perp=host('GP Perpendicular Arrow Example',(2,-3,.5));modifier(perp,'GP Arrow • Perpendicular in Plane',{**dict(zip(['Vector 1 Start','Vector 1 End','Vector 2 Start','Vector 2 End'],points)),'Length':1.2,'Color':(.65,.15,1,1),'Show Label':True,'Label':'p'})
segstart=empty('Segment Start',(3,0,0));segend=empty('Segment End',(-3,0,0));segment=host('GP Segment Intersection Example');modifier(segment,'GP Arrow • Segment Intersection',{'Start Object':segstart,'End Object':segend,'Check Object':obstacle})
camera=bpy.data.objects.new('Demo Camera',bpy.data.cameras.new('Demo Camera'));bpy.context.scene.collection.objects.link(camera);camera.location=(11,-15,10);camera.rotation_euler=(Vector((2,-.5,1))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=11;bpy.context.scene.camera=camera
bpy.context.view_layer.update()
spec=importlib.util.spec_from_file_location('gp_arrow_demo_helper',ROOT/'scripts'/'gp_arrow_objects.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);helper.update_now();bpy.context.view_layer.update()
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_rotation=camera.rotation_euler.to_quaternion();area.spaces.active.region_3d.view_location=(2,-.5,1);area.spaces.active.region_3d.view_distance=12
(ROOT/'examples').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'examples'/'gp_arrows_demo.blend'))
print('DEMO_CHECK=clean demo saved')
