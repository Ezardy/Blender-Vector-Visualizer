# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

mesh=bpy.data.meshes.new('Normal validation mesh')
mesh.from_pydata([(-2,-2,0),(2,-2,0),(2,2,.5),(-2,2,0)],[],[(0,1,2),(0,2,3)])
target=bpy.data.objects.new('Normal validation target',mesh);bpy.context.scene.collection.objects.link(target)
target.location=(1,-2,.7);target.rotation_euler=(.3,-.4,.2);target.scale=(1.3,.7,1.8)
solid=target.modifiers.new('Evaluated surface','SOLIDIFY');solid.thickness=.2
data=bpy.data.grease_pencils.new('Normal validation arrow');host=bpy.data.objects.new('Normal validation host',data);bpy.context.scene.collection.objects.link(host)
host.rotation_euler=(.2,.4,-.5);host.scale=(1.2,.8,1.5)
m=host.modifiers.new('Surface normal','NODES');m.node_group=bpy.data.node_groups['GP Arrow • Closest Surface Normal']
def value(name,val):
    s=next(s for s in m.node_group.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name==name)
    getattr(m.properties.inputs,s.identifier).value=val;host.update_tag()
def check():
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    ev=target.evaluated_get(deps);em=ev.to_mesh()
    try:
        tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in em.vertices],[list(p.vertices) for p in em.polygons])
        point,normal,idx,distance=tree.find_nearest(host.matrix_world.translation)
    finally:ev.to_mesh_clear()
    arrow=host.evaluated_get(deps)
    ds=[f.drawing for l in arrow.data.layers for f in l.frames]
    assert ds
    sampled=host.matrix_world@Vector(ds[0].attributes['gp_surface_point'].data[0].vector)
    direction=(host.matrix_world.to_3x3()@Vector(ds[0].attributes['gp_surface_normal'].data[0].vector)).normalized()
    point_error=(sampled-point).length;normal_error=(direction-normal).length
    assert point_error<1e-5,point_error
    assert normal_error<1e-5,(normal_error,direction,normal)
    body=[]
    for d in ds:
        marker=d.attributes.get('gp_arrow_label')
        body.extend(Vector(v.vector) for idx,v in enumerate(d.attributes['position'].data) if not marker or not marker.data[idx].value)
    assert min(p.length for p in body)<1e-5
    tip=Vector(ds[0].attributes['gp_arrow_end'].data[0].vector)
    assert abs(tip.length-2)<1e-5
    return point_error,normal_error,tip
try:
    value('Surface Object',target);value('Length',2);value('Show Label',True)
    bpy.context.view_layer.update();host.location=target.matrix_world@Vector((.3,-.5,2));host.update_tag()
    p,n,tip=check()
    value('Reverse Direction',True);_,_,reverse=check();assert (tip+reverse).length<1e-5
    host.location=target.matrix_world@Vector((-.5,.7,2));host.update_tag();check()
    assert not [w.message for w in m.node_warnings]
    value('Surface Object',None);bpy.context.view_layer.update()
    assert not host.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.layers
    result={'closest_point_world_error':p,'normal_world_error':n,'rotated_nonuniform_scaled_target_and_host':True,'evaluated_target_modifiers':True,'host_origin_anchor':True,'length_and_reverse':True,'moving_host_updates':True,'missing_target_empty':True}
finally:
    bpy.data.objects.remove(host,do_unlink=True);bpy.data.grease_pencils.remove(data)
    bpy.data.objects.remove(target,do_unlink=True);bpy.data.meshes.remove(mesh)
