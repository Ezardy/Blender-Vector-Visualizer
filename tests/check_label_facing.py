# SPDX-License-Identifier: GPL-3.0-or-later
"""Regress camera orientation under rotated, parented, nonuniform GP hosts."""
import bpy
from mathutils import Vector

data = bpy.data.grease_pencils.new('Camera-facing validation')
host = bpy.data.objects.new('Camera-facing validation', data)
bpy.context.scene.collection.objects.link(host)
parent = bpy.data.objects.new('Camera-facing validation parent', None)
bpy.context.scene.collection.objects.link(parent)
host.parent = parent
parent.location = (2, -3, 4)
parent.rotation_euler = (.6, -.3, .9)
parent.scale = (1.4, .7, 2)
host.rotation_euler = (-.4, .5, .2)
host.scale = (.8, 1.5, .6)
mod = host.modifiers.new('Camera-facing validation', 'NODES')
mod.node_group = bpy.data.node_groups['GP Arrow • Object to Object']

def value(name, val):
    s = next(s for s in mod.node_group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == name)
    getattr(mod.properties.inputs, s.identifier).value = val
    host.update_tag()

def label_points():
    bpy.context.view_layer.update()
    ev = host.evaluated_get(bpy.context.evaluated_depsgraph_get())
    points = []
    for layer in ev.data.layers:
        for frame in layer.frames:
            drawing = frame.drawing
            mark = drawing.attributes.get('gp_arrow_label')
            if mark:
                for j, p in enumerate(drawing.attributes['position'].data):
                    if mark.data[j].value:
                        points.append(host.matrix_world @ layer.matrix_local @ Vector(p.vector))
    return points

try:
    for name, val in [('Use Positions', True), ('Start', (0, 0, 0)), ('End', (1, 0, 0)), ('Show Label', True), ('Label', 'Fg'), ('Vector Sign', True)]:
        value(name, val)
    errors = []
    for facing in [True, False, True]:
        value('Face Camera', facing)
        points = label_points()
        assert len(points) > 6, 'Missing glyphs or vector sign'
        if facing:
            normal = bpy.context.scene.camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
        else:
            normal = (host.matrix_world.to_3x3().inverted().transposed() @ Vector((0, 0, 1))).normalized()
        error = max(abs((p - points[0]).dot(normal)) for p in points)
        assert error < 2e-5, (facing, error)
        errors.append(error)
    result = {'parented_nonuniform_host_plane_errors': errors}
    print('PASS camera-facing labels', result)
finally:
    bpy.data.objects.remove(host, do_unlink=True)
    bpy.data.objects.remove(parent, do_unlink=True)
    bpy.data.grease_pencils.remove(data)
