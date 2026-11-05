# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from mathutils import Vector

source=bpy.data.objects['GP Arrow Example']
host=bpy.data.objects.new('Parallel validation',bpy.data.grease_pencils.new('Parallel validation'))
bpy.context.scene.collection.objects.link(host)
host.location=(3,-2,.5);host.rotation_euler=(.2,-.3,.5);host.scale=(1.2,.8,1.1)
m=host.modifiers.new('Parallel arrow','NODES');m.node_group=bpy.data.node_groups['GP Arrow • Parallel from Origin']
generator=host.modifiers.new('GP Arrow generator','NODES');generator.node_group=bpy.data.node_groups['GP Arrow • Object to Object']
for s in generator.node_group.interface.items_tree:
    if s.item_type=='SOCKET' and s.in_out=='INPUT':
        getattr(generator.properties.inputs,s.identifier).value=getattr(source.modifiers[0].properties.inputs,s.identifier).value
with bpy.context.temp_override(object=host,active_object=host):bpy.ops.object.modifier_move_to_index(modifier=generator.name,index=0)

def value(name,v):
    s=next(s for s in m.node_group.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name==name)
    getattr(m.properties.inputs,s.identifier).value=v;host.update_tag()

def geometry():
    bpy.context.view_layer.update();e=host.evaluated_get(bpy.context.evaluated_depsgraph_get());labels=[];body=[]
    for l in e.data.layers:
        for f in l.frames:
            marker=f.drawing.attributes.get('gp_arrow_label')
            for idx,v in enumerate(f.drawing.attributes['position'].data):
                (labels if marker and marker.data[idx].value else body).append(l.matrix_local@Vector(v.vector))
    return labels,body

try:
    value('Length',2.5);value('Use Source Length',False)
    bpy.context.view_layer.update()
    start=host.matrix_world.inverted()@bpy.data.objects['Arrow Start'].matrix_world.translation
    end=host.matrix_world.inverted()@bpy.data.objects['Arrow End'].matrix_world.translation
    direction=(end-start).normalized();tip=direction*2.5
    a,pts=geometry();origin_error=min(v.length for v in pts);tip_error=min((v-tip).length for v in pts)
    assert origin_error<1e-5,origin_error
    assert tip_error<1e-5,tip_error
    value('Reverse Direction',True);b,pts=geometry();reverse_error=min((v+tip).length for v in pts);assert reverse_error<1e-5
    if a:
        assert len(a)==len(b)
        assert max((y-x+2*tip).length for x,y in zip(a,b))<1e-5,'Labels must translate without mirroring'
    value('Use Source Length',True);_,pts=geometry();assert min((v+(end-start)).length for v in pts)<1e-5
    projection=host.modifiers.new('Project arrow','NODES');projection.node_group=bpy.data.node_groups['GP Arrow • Project onto Plane']
    with bpy.context.temp_override(object=host,active_object=host):bpy.ops.object.modifier_move_to_index(modifier=projection.name,index=1)
    value('Use Source Length',False);_,pts=geometry();assert pts
    value('Length',0);assert not geometry()[1]
    generator.show_viewport=False;value('Length',1);assert not geometry()[1]
    result={'host_origin_error':origin_error,'length_tip_error':tip_error,'reverse_tip_error':reverse_error,'same_object_modifier_stack':True,'rotated_scaled_host':True,'labels_not_mirrored':True,'source_length':True,'projection_before_parallel':True,'zero_length_empty':True,'empty_input_empty':True}
finally:
    data=host.data;bpy.data.objects.remove(host,do_unlink=True);bpy.data.grease_pencils.remove(data)
