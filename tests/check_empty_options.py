# SPDX-License-Identifier: GPL-3.0-or-later
import bpy,importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('gp_empty_options_validation',Path(__file__).resolve().parents[1]/'scripts'/'gp_arrow_objects.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
checks={}
for name in ['GP Parallel Arrow Example','GP Surface Normal Example','GP Perpendicular Arrow Example']:
    source=bpy.data.objects[name];host=source.copy();host.data=source.data.copy();bpy.context.scene.collection.objects.link(host)
    mod=next(m for m in reversed(list(host.modifiers)) if m.type=='NODES' and m.node_group and m.node_group.name in helper.ARROWS)
    s=next(s for s in mod.node_group.interface.items_tree if s.item_type=='SOCKET' and s.name=='Create End Empty')
    try:
        getattr(mod.properties.inputs,s.identifier).value=False;host.update_tag();bpy.context.view_layer.update();helper.update_now()
        assert not any(c.get(helper.ROLE) for c in host.children)
        getattr(mod.properties.inputs,s.identifier).value=True;host.update_tag();bpy.context.view_layer.update();helper.update_now()
        child=host['gp_arrow_endpoint'];assert child.parent==host and child['GP Arrow Valid']
        getattr(mod.properties.inputs,s.identifier).value=False;host.update_tag();bpy.context.view_layer.update();helper.update_now()
        assert child.hide_get() and not child['GP Arrow Valid']
        checks[name]=True
    finally:
        for child in list(host.children):
            if child.get(helper.ROLE):bpy.data.objects.remove(child,do_unlink=True)
        data=host.data;bpy.data.objects.remove(host,do_unlink=True);bpy.data.grease_pencils.remove(data)
result={'optional_end_empty_controls':checks}
