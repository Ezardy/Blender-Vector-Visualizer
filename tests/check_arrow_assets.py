# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from mathutils import Vector

source=bpy.data.objects['GP Arrow Projection Example']
test=source.copy();test.data=source.data.copy();test.name='Arrow Asset Validation'
bpy.context.scene.collection.objects.link(test)
test.location=(1,-2,.7);test.rotation_euler=(.3,-.4,.6);test.scale=(1.3,.8,1.7)
first,last=test.modifiers[0],test.modifiers[-1]

def value(mod,name,val):
    s=next(s for s in mod.node_group.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name==name)
    getattr(mod.properties.inputs,s.identifier).value=val
    test.update_tag()

def geometry():
    global last_shafts,last_heads
    last_shafts=[];last_heads=[]
    bpy.context.view_layer.update()
    e=test.evaluated_get(bpy.context.evaluated_depsgraph_get())
    labels=[];body=[];colors=[];strokes=0
    for layer in e.data.layers:
        for frame in layer.frames:
            d=frame.drawing;strokes+=len(d.strokes)
            marker=d.attributes.get('gp_arrow_label')
            heads=d.attributes.get('gp_arrow_head');shafts=d.attributes.get('gp_arrow_shaft')
            for idx,v in enumerate(d.attributes['position'].data):
                p=layer.matrix_local@Vector(v.vector)
                (labels if marker and marker.data[idx].value else body).append(p)
                if heads and heads.data[idx].value:last_heads.append(p)
                if shafts and shafts.data[idx].value:last_shafts.append(p)
            if marker and any(v.value for v in marker.data) and d.attributes.get('fill_color'):
                colors.extend(tuple(v.color) for v in d.attributes['fill_color'].data)
    return labels,body,colors,strokes

try:
    value(first,'Show Label',True);value(first,'Label','Test');value(first,'Face Camera',True)
    value(first,'Use Label Color',True);value(first,'Label Color',(.9,.1,.3,1));value(first,'Show Arrowhead',True)
    normal=Vector((0,0,1));origin=Vector((0,0,0))
    last.show_viewport=False;test.update_tag();a,body,colors,count=geometry()
    assert a and any(max(abs(c[j]-x) for j,x in enumerate((.9,.1,.3,1)))<1e-5 for c in colors)
    end_socket=next(s for s in first.node_group.interface.items_tree if s.item_type=='SOCKET' and s.name=='End Object')
    end=getattr(first.properties.inputs,end_socket.identifier).value
    tip=test.matrix_world.inverted()@end.matrix_world.translation
    assert min((v-tip).length for v in body)<1e-5, 'Cone tip must meet end origin'
    last.show_viewport=True;test.update_tag();b,body,_,_=geometry()
    shift=-normal*(tip-origin).dot(normal)
    assert len(a)==len(b)
    camera_error=max((y-x-shift).length for x,y in zip(a,b))
    assert camera_error<1e-5,camera_error
    assert max(abs((v-origin).dot(normal)) for v in last_shafts)<1e-5
    cone_depth=max(v.z for v in last_heads)-min(v.z for v in last_heads)
    assert cone_depth>.01,'Projected cone must retain a circular 3D base'
    projected_start=last_shafts[0];projected_tip=Vector((tip.x,tip.y,0))
    axis=(projected_tip-projected_start).normalized()
    head_length=-min((v-projected_tip).dot(axis) for v in last_heads)
    expected_base=projected_tip-axis*head_length
    assert min((v-expected_base).length for v in last_shafts)<1e-5,'Shaft must meet cone base'
    assert min((v-projected_tip).length for v in last_heads)<1e-5,'Projected cone tip must remain at the projected endpoint'
    worldnormal=(test.matrix_world.to_3x3().inverted().transposed()@normal).normalized()
    worldplane_error=max(abs((test.matrix_world@v-test.matrix_world.translation).dot(worldnormal)) for v in last_shafts)
    assert worldplane_error<1e-5
    assert all(s.name not in ['Plane U','Plane V','Plane Origin'] for s in last.node_group.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT')
    assert max(abs((v-origin).dot(normal)) for v in b)>1e-4,'Camera labels should retain 3D orientation'
    value(first,'Face Camera',False)
    last.show_viewport=False;test.update_tag();flat_source,_,_,_=geometry()
    last.show_viewport=True;test.update_tag();flat,body,_,_=geometry()
    plane_error=max(abs((v-origin).dot(normal)) for v in flat+last_shafts)
    assert plane_error<1e-5,plane_error
    shape_error=max(abs((x-flat_source[0]).length-(y-flat[0]).length) for x,y in zip(flat_source,flat))
    assert shape_error<1e-5,shape_error
    value(first,'Show Arrowhead',False);last.show_viewport=False;test.update_tag();_,body,_,headless_count=geometry()
    assert len(body)==2 and min((v-tip).length for v in body)<1e-5
    value(first,'Show Label',False);_,body,_,line_count=geometry();assert line_count==1
    value(first,'Show Arrowhead',True);_,body,_,cone_count=geometry();assert cone_count==34
    warnings=[w.message for m in test.modifiers for w in m.node_warnings]
    assert not warnings,warnings
    result={'camera_label_translation_error':camera_error,'projected_cone_depth':cone_depth,'host_xy_world_plane_error':worldplane_error,'rotated_scaled_translated_host':True,'automatic_host_plane':True,'planar_label_max_distance':plane_error,'planar_label_shape_error':shape_error,'independent_label_color':True,'cone_tip_at_end':True,'headless_line_reaches_end':True,'cone_faces_plus_shaft':cone_count,'warnings':warnings}
finally:
    data=test.data;bpy.data.objects.remove(test,do_unlink=True)
    if data.users==0:bpy.data.grease_pencils.remove(data)
