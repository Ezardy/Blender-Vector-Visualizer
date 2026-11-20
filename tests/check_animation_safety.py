# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise frame scrubbing across camera movement, no-hit and disabled output."""
import bpy
import importlib.util
from pathlib import Path
from math import radians

spec = importlib.util.spec_from_file_location('gp_animation_validation', Path(__file__).resolve().parents[1] / 'scripts/gp_arrow_objects.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
helper.register()

scene = bpy.context.scene
original_frame = scene.frame_current
created = []
data = []

def empty(name, position):
    obj = bpy.data.objects.new(name, None)
    scene.collection.objects.link(obj)
    obj.location = position
    created.append(obj)
    return obj

def value(mod, name, val):
    s = next(s for s in mod.node_group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == name)
    getattr(mod.properties.inputs, s.identifier).value = val
    mod.id_data.update_tag()

try:
    pivot = empty('Animation validation camera pivot', (0, 0, 0))
    start = empty('Animation validation start', (0, 0, 2))
    end = empty('Animation validation end', (0, 0, -2))
    start.parent = pivot
    end.parent = pivot
    mesh = bpy.data.meshes.new('Animation validation plane')
    data.append(mesh)
    mesh.from_pydata([(-10, -10, 0), (10, -10, 0), (10, 10, 0), (-10, 10, 0)], [], [(0, 1, 2, 3)])
    target = bpy.data.objects.new('Animation validation obstacle', mesh)
    scene.collection.objects.link(target)
    created.append(target)
    hosts = []
    for j in range(2):
        gp = bpy.data.grease_pencils.new('Animation validation GP')
        data.append(gp)
        host = bpy.data.objects.new('Animation validation intersection', gp)
        scene.collection.objects.link(host)
        created.append(host)
        mod = host.modifiers.new('Intersection', 'NODES')
        mod.node_group = bpy.data.node_groups['GP Arrow • Segment Intersection']
        for name, val in [('Start Object', start), ('End Object', end), ('Check Object', target)]:
            value(mod, name, val)
        mod.show_viewport = True
        mod.keyframe_insert('show_viewport', frame=1)
        mod.show_viewport = False
        mod.keyframe_insert('show_viewport', frame=15)
        hosts.append(host)
    for frame, angle in [(1, 54.9016), (30, 83)]:
        pivot.rotation_euler.x = radians(angle)
        pivot.keyframe_insert('rotation_euler', index=0, frame=frame)
    for cycle in range(3):
        for frame in list(range(1, 31)) + list(range(30, 0, -1)):
            previous = [host['gp_arrow_intersection']['GP Arrow Valid'] for host in hosts] if cycle or frame > 1 else None
            scene.frame_set(frame)
            if previous is not None:
                assert [host['gp_arrow_intersection']['GP Arrow Valid'] for host in hosts] == previous, 'Frame handler mutated child objects'
            helper._tick()
            bpy.context.view_layer.update()
            for host in hosts:
                child = host['gp_arrow_intersection']
                expected = frame < 15
                assert child['GP Arrow Valid'] == expected, (frame, expected)
                assert child.hide_get() != expected
                if expected:
                    assert child.location.length < 1e-4
    # The frame callback must only schedule work, including on render graphs.
    helper._dirty = False
    helper._frame(scene)
    assert helper._dirty
    result = {'camera_sweep_degrees': [54.9016, 83], 'forward_backward_frame_changes': 180, 'animated_disable_reenable': True, 'multiple_hosts': True}
    print('PASS animation safety', result)
finally:
    helper.unregister()
    actions = {obj.animation_data.action for obj in created if obj.animation_data and obj.animation_data.action}
    for obj in reversed(created):
        for child in list(obj.children):
            if child.get(helper.ROLE):
                bpy.data.objects.remove(child, do_unlink=True)
        bpy.data.objects.remove(obj, do_unlink=True)
    for item in data:
        if isinstance(item, bpy.types.Mesh):
            bpy.data.meshes.remove(item)
        else:
            bpy.data.grease_pencils.remove(item)
    for action in actions:
        if action.users == 0:
            bpy.data.actions.remove(action)
    scene.frame_set(original_frame)
