# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from mathutils import Vector

data=bpy.data.grease_pencils.new('Vector sign validation');host=bpy.data.objects.new('Vector sign validation',data);bpy.context.scene.collection.objects.link(host)
mod=host.modifiers.new('Vector sign validation','NODES');mod.node_group=bpy.data.node_groups['GP Arrow • Object to Object']
def value(mod,name,val):
    s=next(s for s in mod.node_group.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name==name)
    getattr(mod.properties.inputs,s.identifier).value=val;mod.id_data.update_tag()
def geometry(obj):
    bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());marks=[];glyphs=[];colors=[];opacity=[]
    for layer in ev.data.layers:
        for frame in layer.frames:
            d=frame.drawing;sign=d.attributes.get('gp_label_vector_sign');label=d.attributes.get('gp_arrow_label') or d.attributes.get('gp_arc_label')
            for idx,p in enumerate(d.attributes['position'].data):
                world=obj.matrix_world@layer.matrix_local@Vector(p.vector)
                if sign and sign.data[idx].value:
                    marks.append(world)
                    if d.attributes.get('vertex_color'):colors.append(tuple(d.attributes['vertex_color'].data[idx].color))
                    if d.attributes.get('opacity'):opacity.append(d.attributes['opacity'].data[idx].value)
                elif label and label.data[idx].value:glyphs.append(world)
    return marks,glyphs,colors,opacity
extra=[]
try:
    for key,val in [('Use Positions',True),('Start',(0,0,0)),('End',(1,0,0)),('Show Label',True),('Vector Sign',False),('Label','v'),('Label Size',.4),('Face Camera',False),('Use Label Color',True),('Label Color',(.9,.1,.3,1)),('Opacity',.6)]:value(mod,key,val)
    off,glyphs_off,_,_=geometry(host);assert not off and glyphs_off
    value(mod,'Vector Sign',True);short,glyphs,colors,opacity=geometry(host)
    assert len(short)==6 and len(glyphs)==len(glyphs_off)
    assert max((a-b).length for a,b in zip(glyphs,glyphs_off))<1e-6
    assert min(p.y for p in short)>max(p.y for p in glyphs)
    assert all(max(abs(c[j]-v) for j,v in enumerate((.9,.1,.3,1)))<1e-5 for c in colors)
    assert all(abs(v-.6)<1e-5 for v in opacity)
    short_width=max(p.x for p in short)-min(p.x for p in short)
    value(mod,'Label','velocity');wide,_,_,_=geometry(host);wide_width=max(p.x for p in wide)-min(p.x for p in wide);assert wide_width>short_width*3
    value(mod,'Label Size',.8);larger,_,_,_=geometry(host);assert abs((max(p.x for p in larger)-min(p.x for p in larger))/wide_width-2)<1e-4
    value(mod,'Label','');assert not geometry(host)[0]
    value(mod,'Label','v');value(mod,'Face Camera',True);camera_marks,camera_glyphs,_,_=geometry(host)
    normal=None
    for idx in range(2,len(camera_glyphs)):
        n=(camera_glyphs[1]-camera_glyphs[0]).cross(camera_glyphs[idx]-camera_glyphs[0])
        if n.length>1e-6:normal=n.normalized();break
    assert normal is not None and max(abs((p-camera_glyphs[0]).dot(normal)) for p in camera_marks)<1e-5
    inherited={}
    for name in ['GP Arrow Projection Example','GP Parallel Arrow Example','GP Surface Normal Example','GP Perpendicular Arrow Example','GP Arc Example']:
        source=bpy.data.objects[name];obj=source.copy();obj.data=source.data.copy();bpy.context.scene.collection.objects.link(obj);extra.append(obj)
        source_mod=next(m for m in obj.modifiers if m.type=='NODES' and m.node_group and any(s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name=='Vector Sign' for s in m.node_group.interface.items_tree))
        value(source_mod,'Show Label',True);value(source_mod,'Label','v');value(source_mod,'Vector Sign',True)
        assert len(geometry(obj)[0])==6,name
        for face_camera in (False,True):
            value(source_mod,'Face Camera',face_camera);assert len(geometry(obj)[0])==6,name
        value(source_mod,'Vector Sign',False);assert not geometry(obj)[0],name
        inherited[name]=True
    result={'sign_above_label':True,'glyphs_unchanged':True,'width_fits_text':True,'scales_with_label_size':True,'label_color_and_opacity':True,'blank_label_no_sign':True,'camera_alignment':True,'asset_inheritance':inherited}
finally:
    for obj in extra+[host]:
        for child in list(obj.children):
            if child.get('gp_arrow_managed_role'):bpy.data.objects.remove(child,do_unlink=True)
        d=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
        if d.users==0:bpy.data.grease_pencils.remove(d)
