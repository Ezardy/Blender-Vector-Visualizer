# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from math import pi,sqrt
from mathutils import Vector,Euler

objects=[];data=None
def empty(name,p):
    o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);o.location=p;objects.append(o);return o
try:
    center=Vector((2,-1,.4));u=Vector((1,0,0));v=Vector((.5,sqrt(3)/2,0))
    points=[empty('Arc validation endpoint',p) for p in (center,center+u,center,center+v)]
    data=bpy.data.grease_pencils.new('Arc validation');host=bpy.data.objects.new('Arc validation',data);bpy.context.scene.collection.objects.link(host);objects.append(host)
    host.location=(3,-2,.7);host.rotation_euler=(.3,-.4,.2);host.scale=(1.3,.7,1.8)
    mod=host.modifiers.new('Angle Arc','NODES');mod.node_group=bpy.data.node_groups['GP Arrow • Angle Arc']
    def value(name,val):
        s=next(s for s in mod.node_group.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name==name)
        getattr(mod.properties.inputs,s.identifier).value=val;host.update_tag()
    for name,p in zip(('Vector 1 Start','Vector 1 End','Vector 2 Start','Vector 2 End'),points):value(name,p)
    value('Radius',1.);value('Show Label',True);value('Label','theta');value('Use Label Color',True);value('Label Color',(.9,.1,.3,1));value('Show Arrowhead',True)
    def geometry():
        bpy.context.view_layer.update();ev=host.evaluated_get(bpy.context.evaluated_depsgraph_get());out={'stroke':[],'head':[],'label':[],'metadata':None,'colors':[],'strokes':0}
        for layer in ev.data.layers:
            for frame in layer.frames:
                d=frame.drawing;out['strokes']+=len(d.strokes)
                if len(d.attributes['position'].data)==0:continue
                if out['metadata'] is None:
                    out['metadata']={n:Vector(d.attributes[n].data[0].vector) for n in ('gp_arc_center','gp_arc_start','gp_arc_end')}
                    out['metadata']['angle']=d.attributes['gp_arc_angle'].data[0].value;out['metadata']['right']=d.attributes['gp_arc_right_angle'].data[0].value
                for idx,p in enumerate(d.attributes['position'].data):
                    world=host.matrix_world@layer.matrix_local@Vector(p.vector)
                    for name,attr in (('stroke','gp_arc_stroke'),('head','gp_arrow_head'),('label','gp_arc_label')):
                        a=d.attributes.get(attr)
                        if a and a.data[idx].value:out[name].append(world)
                if d.attributes.get('fill_color'):out['colors'].extend(tuple(x.color) for x in d.attributes['fill_color'].data)
        assert not [w.message for w in mod.node_warnings],[w.message for w in mod.node_warnings]
        return out
    first=geometry();assert first['stroke'] and first['head'] and first['label']
    assert abs(first['metadata']['angle']-pi/3)<1e-5 and not first['metadata']['right']
    assert (host.matrix_world@first['metadata']['gp_arc_center']-center).length<1e-5
    plane_error=max(abs(p.z-center.z) for p in first['stroke'])
    radius_error=max(abs((p-center).length-1) for p in first['stroke'][:-1])
    assert plane_error<1e-5 and radius_error<1e-5,(plane_error,radius_error)
    assert min((p-(center+v)).length for p in first['head'])<1e-5
    assert max(p.z for p in first['head'])-min(p.z for p in first['head'])>.05
    assert any(max(abs(c[j]-x) for j,x in enumerate((.9,.1,.3,1)))<1e-5 for c in first['colors'])
    value('Clockwise',True);clockwise=geometry();assert abs(clockwise['metadata']['angle']-5*pi/3)<1e-5
    assert min(p.y for p in clockwise['stroke'])<center.y-.5
    # Different starts on intersecting coplanar lines must still find the same center.
    value('Clockwise',False);points[2].location=center+2*v;points[3].location=center+3*v
    for p in points:p.update_tag()
    offset=geometry();assert (host.matrix_world@offset['metadata']['gp_arc_center']-center).length<1e-5
    points[2].location=center;points[3].location=center+Vector((0,1,0));points[2].update_tag();points[3].update_tag()
    right=geometry();assert right['metadata']['right'] and len(right['stroke'])==4
    assert abs((right['stroke'][1]-right['stroke'][0]).normalized().dot((right['stroke'][3]-right['stroke'][2]).normalized()))<1e-5
    value('Clockwise',True);reflex=geometry();assert not reflex['metadata']['right'] and len(reflex['stroke'])>4 and abs(reflex['metadata']['angle']-3*pi/2)<1e-5
    value('Clockwise',False);value('Show Arrowhead',False);value('Show Label',False);plain=geometry();assert not plain['head'] and not plain['label'] and len(plain['stroke'])==4
    rotation=Euler((.4,.3,.2)).to_matrix();u3=rotation@u;v3=rotation@v;n3=u3.cross(v3).normalized()
    for obj,p in zip(points,(center,center+u3,center,center+v3)):obj.location=p;obj.update_tag()
    value('Show Arrowhead',True);value('Show Label',True);value('Face Camera',False);tilted=geometry()
    assert max(abs((p-center).dot(n3)) for p in tilted['stroke']+tilted['label'])<1e-5
    value('Face Camera',True);facing=geometry()
    if bpy.context.scene.camera:
        camera_normal=(bpy.context.scene.camera.matrix_world.to_quaternion()@Vector((0,0,1))).normalized()
        assert max(abs((p-facing['label'][0]).dot(camera_normal)) for p in facing['label'])<1e-5
    points[2].location.z+=.5;points[3].location.z+=.5;points[2].update_tag();points[3].update_tag();assert geometry()['metadata'] is None
    points[1].location=center+u;points[2].location=center;points[3].location=center+u
    for p in points:p.update_tag()
    assert geometry()['metadata'] is None
    points[1].location=center;points[1].update_tag();assert geometry()['metadata'] is None
    result={'world_plane_error':plane_error,'world_radius_error':radius_error,'clockwise_reflex_sweep':True,'intersecting_offset_origins':True,'right_angle_rectangle':True,'right_angle_direction_respected':True,'cone_head':True,'optional_label_and_color':True,'tilted_arc_plane':True,'camera_and_planar_labels':True,'skew_vectors_empty':True,'parallel_and_zero_vectors_empty':True,'rotated_nonuniform_host':True}
finally:
    for obj in reversed(objects):bpy.data.objects.remove(obj,do_unlink=True)
    if data and data.users==0:bpy.data.grease_pencils.remove(data)
