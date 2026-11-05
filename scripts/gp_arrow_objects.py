# SPDX-License-Identifier: GPL-3.0-or-later
bl_info = {'name': 'GP Arrow Objects', 'author': 'Blender Visualizer', 'version': (1, 0, 1), 'blender': (5, 2, 0), 'category': 'Object', 'description': 'Maintain real child empties for GP Arrow endpoints and segment intersections.'}

import bpy
from bpy.app.handlers import persistent
from mathutils import Matrix, Vector

ARROWS = {'GP Arrow • Closest Surface Normal', 'GP Arrow • Parallel from Origin', 'GP Arrow • Perpendicular in Plane'}
INTERSECTION = 'GP Arrow • Segment Intersection'
ROLE = 'gp_arrow_managed_role'
_busy = False
_dirty = True

def _roles(group, seen=None):
    seen = set() if seen is None else seen
    if group.as_pointer() in seen:
        return set()
    seen.add(group.as_pointer())
    roles = set()
    role = group.get('gp_arrow_output_role')
    if role:
        roles.add(role)
    elif group.name in ARROWS:
        roles.add('endpoint')
    elif group.name == INTERSECTION:
        roles.add('intersection')
    elif group.name == 'GP Arrow • Project onto Plane':
        roles.add('projected_endpoints')
    for n in group.nodes:
        if n.type == 'GROUP' and n.node_tree and not n.mute:
            roles.update(_roles(n.node_tree, seen))
    return roles

def _point(evaluated, attribute):
    if evaluated.type == 'GREASEPENCIL':
        drawings = (f.drawing for l in evaluated.data.layers for f in l.frames)
        for d in drawings:
            a = d.attributes.get(attribute)
            if a and len(a.data):
                return Vector(a.data[0].vector)
    return None

def _child(host, role):
    child = next((o for o in host.children if o.type == 'EMPTY' and o.get(ROLE) == role), None)
    if child is None:
        suffix = {'endpoint': 'End', 'startpoint': 'Start', 'intersection': 'Intersection'}[role]
        child = bpy.data.objects.new(f'{host.name} • {suffix}', None)
        collection = host.users_collection[0] if host.users_collection else bpy.context.scene.collection
        collection.objects.link(child)
        child.parent = host
        child.matrix_parent_inverse = Matrix.Identity(4)
        child.empty_display_type = 'PLAIN_AXES'
        child.empty_display_size = .12
        child.show_in_front = True
        child[ROLE] = role
        child['GP Arrow Valid'] = False
        child['GP Arrow Managed'] = 'Position follows the evaluated node modifier output.'
        host[{'endpoint': 'gp_arrow_endpoint', 'startpoint': 'gp_arrow_startpoint', 'intersection': 'gp_arrow_intersection'}[role]] = child
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D' and area.spaces.active.local_view and host.local_view_get(area.spaces.active):
                    child.local_view_set(area.spaces.active, True)
    return child

def update_now(scene=None, depsgraph=None):
    global _busy, _dirty
    if _busy:
        return
    _busy = True
    try:
        scene = scene if isinstance(scene, bpy.types.Scene) else bpy.context.scene
        depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
        for host in list(scene.objects):
            if host.get(ROLE) or host.type != 'GREASEPENCIL' or host.library:
                continue
            output_roles = set()
            for m in host.modifiers:
                if m.type == 'NODES' and m.node_group and m.show_viewport:
                    output_roles.update(_roles(m.node_group))
            roles = []
            if 'projected_endpoints' in output_roles:
                roles.append(('startpoint', 'gp_arrow_start'))
            if 'endpoint' in output_roles or 'projected_endpoints' in output_roles:
                roles.append(('endpoint', 'gp_arrow_end'))
            if 'intersection' in output_roles:
                roles.append(('intersection', 'gp_intersection_point'))
            roles.extend((o.get(ROLE), None) for o in host.children if o.get(ROLE) and o.get(ROLE) not in {r[0] for r in roles})
            if not roles:
                continue
            ev = host.evaluated_get(depsgraph)
            for role, attr in roles:
                child = _child(host, role)
                point = _point(ev, attr) if attr else None
                valid = point is not None
                if child.get('GP Arrow Valid') != valid:
                    child['GP Arrow Valid'] = valid
                if child.hide_get() == valid:
                    child.hide_set(not valid)
                if valid and (child.location - point).length > 1e-6:
                    child.location = point
        _dirty = False
    finally:
        _busy = False

@persistent
def _changed(*args):
    global _dirty
    if not _busy:
        _dirty = True

@persistent
def _frame(scene, depsgraph=None):
    update_now(scene, depsgraph)

@persistent
def _save(*args):
    update_now()

def _tick():
    if _dirty:
        try:
            update_now()
        except (ReferenceError, RuntimeError):
            pass
    return .1

def register():
    for handlers, fn in [(bpy.app.handlers.depsgraph_update_post, _changed), (bpy.app.handlers.load_post, _changed), (bpy.app.handlers.frame_change_post, _frame), (bpy.app.handlers.save_pre, _save)]:
        if fn not in handlers:
            handlers.append(fn)
    if not bpy.app.timers.is_registered(_tick):
        bpy.app.timers.register(_tick, first_interval=.1, persistent=True)

def unregister():
    for handlers, fn in [(bpy.app.handlers.depsgraph_update_post, _changed), (bpy.app.handlers.load_post, _changed), (bpy.app.handlers.frame_change_post, _frame), (bpy.app.handlers.save_pre, _save)]:
        if fn in handlers:
            handlers.remove(fn)
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)

if __name__ == '__main__':
    register()
