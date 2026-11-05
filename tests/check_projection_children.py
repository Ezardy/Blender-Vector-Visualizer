# SPDX-License-Identifier: GPL-3.0-or-later
import bpy, importlib.util, sys
from pathlib import Path
from mathutils import Vector

spec=importlib.util.spec_from_file_location('gp_projection_children_validation',str(Path(__file__).resolve().parents[1]/'scripts'/'gp_arrow_objects.py'))
helper=importlib.util.module_from_spec(spec);sys.modules[spec.name]=helper;spec.loader.exec_module(helper)
source=bpy.data.objects['GP Arrow Projection Example'];test=source.copy();test.data=source.data.copy();test.name='Projection children validation';bpy.context.scene.collection.objects.link(test)
test.location=(1,-2,.7);test.rotation_euler=(.3,-.4,.5);test.scale=(1.3,.8,1.7)
generator=test.modifiers[0]
def value(name,v,mod=None):
    mod=mod or generator
    s=next(s for s in mod.node_group.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name==name)
    getattr(mod.properties.inputs,s.identifier).value=v;test.update_tag()
def update():
    bpy.context.view_layer.update();helper.update_now();bpy.context.view_layer.update()
try:
    projection=test.modifiers[-1]
    value('Create Start Empty',False,projection);value('Create End Empty',False,projection)
    value('Use Positions',True);value('Start',(1,2,3));value('End',(3,4,5));update()
    assert not [c for c in test.children if c.get(helper.ROLE)],'Disabled options must not create objects'
    value('Create Start Empty',True,projection);update()
    assert len([c for c in test.children if c.get(helper.ROLE)])==1
    value('Create End Empty',True,projection);update()
    start=test['gp_arrow_startpoint'];end=test['gp_arrow_endpoint']
    assert start.parent==test and end.parent==test and start.type==end.type=='EMPTY'
    error=max((start.location-Vector((1,2,0))).length,(end.location-Vector((3,4,0))).length)
    assert error<1e-5,error
    assert (start.matrix_world.translation-test.matrix_world@Vector((1,2,0))).length<1e-5
    value('Start',(-2,1,4));value('End',(5,-3,2));update()
    assert (start.location-Vector((-2,1,0))).length<1e-5 and (end.location-Vector((5,-3,0))).length<1e-5
    value('End',(-2,1,4));update();assert not start['GP Arrow Valid'] and not end['GP Arrow Valid']
    value('End',(5,-3,2));value('Create Start Empty',False,projection);value('Create End Empty',False,projection);update()
    assert start.hide_get() and end.hide_get() and not start['GP Arrow Valid'] and not end['GP Arrow Valid']
    result={'projection_start_and_end_error':error,'true_child_empties':True,'rotated_scaled_host':True,'live_endpoint_updates':True,'invalid_geometry_hides_both':True,'optional_creation_and_disable':True}
finally:
    for child in list(test.children):
        if child.get(helper.ROLE):bpy.data.objects.remove(child,do_unlink=True)
    data=test.data;bpy.data.objects.remove(test,do_unlink=True);bpy.data.grease_pencils.remove(data)
    del sys.modules[spec.name]
