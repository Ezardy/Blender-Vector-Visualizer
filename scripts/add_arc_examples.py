# SPDX-License-Identifier: GPL-3.0-or-later
"""Add arc/right-angle examples while preserving existing scene objects."""
import bpy
from mathutils import Vector

collection=bpy.data.collections.get('GP Arc Examples')
if collection is None:
    collection=bpy.data.collections.new('GP Arc Examples');bpy.context.scene.collection.children.link(collection)
created=[]
for name,center,second,radius,label in [('GP Arc Example',(-2,-3,1),(.5,.8660254,0),.7,'θ'),('GP Right Angle Example',(-2,-1,1),(0,1,0),.5,'90°')]:
    if bpy.data.objects.get(name):continue
    points=[];p=Vector(center)
    for suffix,pos in [('Origin',p),('Vector 1',p+Vector((1,0,0))),('Vector 2',p+Vector(second))]:
        point=bpy.data.objects.new(name+' '+suffix,None);collection.objects.link(point);point.location=pos;point.empty_display_size=.08;points.append(point)
    host=bpy.data.objects.new(name,bpy.data.grease_pencils.new(name));collection.objects.link(host);host.location=p;host.show_in_front=True
    mod=host.modifiers.new('Angle Arc','NODES');mod.node_group=bpy.data.node_groups['GP Arrow • Angle Arc']
    values={'Vector 1 Start':points[0],'Vector 1 End':points[1],'Vector 2 Start':points[0],'Vector 2 End':points[2],'Radius':radius,'Show Label':True,'Label':label,'Face Camera':False}
    for s in mod.node_group.interface.items_tree:
        if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name in values:getattr(mod.properties.inputs,s.identifier).value=values[s.name]
    host.update_tag();created.append(host.name)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D' and area.spaces.active.local_view:
                for obj in [host]+points:obj.local_view_set(area.spaces.active,True)
bpy.context.view_layer.update()
result={'created':created}
