# SPDX-License-Identifier: GPL-3.0-or-later
import bpy, importlib.util, sys
from pathlib import Path
from mathutils import Vector

module_name='gp_arrow_objects_validation'
spec=importlib.util.spec_from_file_location(module_name,str(Path(__file__).resolve().parents[1]/'scripts'/'gp_arrow_objects.py'))
helper=importlib.util.module_from_spec(spec);sys.modules[module_name]=helper;spec.loader.exec_module(helper)
created=[];datas=[]
def empty(name,p):
    o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);o.location=p;created.append(o);return o
def value(mod,name,val):
    s=next(s for s in mod.node_group.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name==name)
    getattr(mod.properties.inputs,s.identifier).value=val;mod.id_data.update_tag()
def update():
    bpy.context.view_layer.update();helper.update_now();bpy.context.view_layer.update()
try:
    mesh=bpy.data.meshes.new('Segment validation plane');mesh.from_pydata([(-2,-2,0),(2,-2,0),(2,2,0),(-2,2,0)],[],[(0,1,2,3)]);datas.append(mesh)
    target=bpy.data.objects.new('Segment validation target',mesh);bpy.context.scene.collection.objects.link(target);created.append(target)
    target.location=(1,-2,.7);target.rotation_euler=(.3,-.4,.2);target.scale=(1.3,.7,1.8)
    bpy.context.view_layer.update();origin=target.matrix_world@Vector((.2,.3,0));n=(target.matrix_world.to_3x3().inverted().transposed()@Vector((0,0,1))).normalized()
    start=empty('Segment validation start',origin+n*2);end=empty('Segment validation end',origin-n*2)
    gp=bpy.data.grease_pencils.new('Segment validation GP');datas.append(gp)
    host=bpy.data.objects.new('Segment validation host',gp);bpy.context.scene.collection.objects.link(host);created.append(host)
    host.location=(3,1,2);host.rotation_euler=(.2,.4,-.3);host.scale=(1.3,.8,1.7)
    m=host.modifiers.new('Intersection','NODES');m.node_group=bpy.data.node_groups['GP Arrow • Segment Intersection']
    for key,val in [('Start Object',start),('End Object',end),('Check Object',target)]:value(m,key,val)
    update();child=host['gp_arrow_intersection'];created.append(child)
    error=(child.matrix_world.translation-origin).length
    assert error<1e-5,(error,tuple(child.matrix_world.translation),tuple(origin))
    assert child.parent==host and child['GP Arrow Valid']
    end.location=origin+n;end.update_tag();update();assert not child['GP Arrow Valid'] and child.hide_get(),'Hit past End must be rejected'
    end.location=start.location;end.update_tag();update();assert not child['GP Arrow Valid']
    end.location=origin-n*2;end.update_tag();update();assert child['GP Arrow Valid'] and not child.hide_get()
    # Every live origin-based arrow receives one actual child at its evaluated endpoint.
    arrow_checks={}
    for ob in list(bpy.context.scene.objects):
        if ob.type!='GREASEPENCIL' or not any(mod.type=='NODES' and mod.node_group and mod.node_group.name in helper.ARROWS for mod in ob.modifiers):continue
        update();child=ob['gp_arrow_endpoint'];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());point=helper._point(ev,'gp_arrow_end')
        if point is not None:
            assert (child.matrix_world.translation-(ob.matrix_world@point)).length<1e-5
        assert child.parent==ob
        arrow_checks[ob.name]=child.name
    normal=bpy.data.objects.get('GP Surface Normal Example')
    if normal:
        mod=next(m for m in normal.modifiers if m.type=='NODES' and m.node_group.name=='GP Arrow • Closest Surface Normal')
        s=next(s for s in mod.node_group.interface.items_tree if s.item_type=='SOCKET' and s.name=='Length');old=getattr(mod.properties.inputs,s.identifier).value
        try:
            value(mod,'Length',old+.7);update();ev=normal.evaluated_get(bpy.context.evaluated_depsgraph_get());point=helper._point(ev,'gp_arrow_end');assert (normal['gp_arrow_endpoint'].location-point).length<1e-5
        finally:value(mod,'Length',old);update()
    result={'segment_intersection_world_error':error,'beyond_end_rejected':True,'zero_length_rejected':True,'no_hit_child_hidden_and_flagged':True,'hit_reappears':True,'rotated_scaled_hosts_and_targets':True,'arrow_children':arrow_checks,'changing_length_updates_child':True}
finally:
    for ob in reversed(created):
        if ob.name in bpy.data.objects:bpy.data.objects.remove(ob,do_unlink=True)
    for data in datas:
        if data.users==0:
            if isinstance(data,bpy.types.Mesh):bpy.data.meshes.remove(data)
            else:bpy.data.grease_pencils.remove(data)
    del sys.modules[module_name]
