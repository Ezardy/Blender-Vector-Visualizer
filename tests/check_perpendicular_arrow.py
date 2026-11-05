# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from mathutils import Vector

points=[]
for idx,p in enumerate([(1,2,3),(3,3,3.5),(-1,4,.2),(0,6,2)]):
    o=bpy.data.objects.new('Perpendicular validation endpoint',None);bpy.context.scene.collection.objects.link(o);o.location=p;points.append(o)
data=bpy.data.grease_pencils.new('Perpendicular validation');host=bpy.data.objects.new('Perpendicular validation',data);bpy.context.scene.collection.objects.link(host)
host.location=(3,-2,.5);host.rotation_euler=(.3,-.4,.5);host.scale=(1.3,.7,1.8)
m=host.modifiers.new('Perpendicular in plane','NODES');m.node_group=bpy.data.node_groups['GP Arrow • Perpendicular in Plane']
def value(name,v):
    s=next(s for s in m.node_group.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name==name)
    getattr(m.properties.inputs,s.identifier).value=v;host.update_tag()
def tip():
    bpy.context.view_layer.update();e=host.evaluated_get(bpy.context.evaluated_depsgraph_get())
    ds=[f.drawing for l in e.data.layers for f in l.frames]
    if not ds:return None
    end=Vector(ds[0].attributes['gp_arrow_end'].data[0].vector)
    assert abs(end.length-2)<1e-5
    assert Vector(ds[0].attributes['gp_arrow_start'].data[0].vector).length<1e-6
    return (host.matrix_world.to_3x3()@end).normalized()
try:
    for name,p in zip(['Vector 1 Start','Vector 1 End','Vector 2 Start','Vector 2 End'],points):value(name,p)
    value('Length',2);value('Show Label',True)
    a=(points[1].location-points[0].location).normalized();b=(points[3].location-points[2].location).normalized();n=a.cross(b).normalized()
    direction=tip();perpendicular_error=abs(direction.dot(a));plane_error=abs(direction.dot(n))
    assert perpendicular_error<1e-6 and plane_error<1e-6
    value('Vector 1 Start',points[1]);value('Vector 1 End',points[0]);assert (tip()+direction).length<1e-5
    value('Vector 1 Start',points[0]);value('Vector 1 End',points[1])
    value('Vector 2 Start',points[3]);value('Vector 2 End',points[2]);assert (tip()-direction).length<1e-5
    value('Reverse Direction',True);assert (tip()+direction).length<1e-5
    value('Vector 2 Start',points[0]);value('Vector 2 End',points[1]);assert tip() is None
    value('Vector 1 End',points[0]);assert tip() is None
    assert not [w.message for w in m.node_warnings]
    result={'perpendicular_world_error':perpendicular_error,'plane_world_error':plane_error,'nonorthogonal_spanning_vectors':True,'rotated_scaled_host':True,'first_vector_reversal_flips_arrow':True,'second_vector_reversal_keeps_arrow':True,'reverse_switch':True,'zero_and_parallel_vectors_empty':True,'host_origin_and_length':True}
finally:
    bpy.data.objects.remove(host,do_unlink=True);bpy.data.grease_pencils.remove(data)
    for p in points:bpy.data.objects.remove(p,do_unlink=True)
