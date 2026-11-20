# SPDX-License-Identifier: GPL-3.0-or-later
"""Keep camera-facing text in camera world orientation on transformed hosts."""
import bpy

g = bpy.data.node_groups['GP Arrow • Label (GP Text Nodes 5.2)']
for n in list(g.nodes):
    if n.get('gp_camera_facing_node'):
        g.nodes.remove(n)

def node(kind, label):
    n = g.nodes.new(kind)
    n.label = label
    n['gp_camera_facing_node'] = True
    return n

camera = g.nodes['Object Info.002']
camera.transform_space = 'ORIGINAL'
self_object = node('GeometryNodeSelfObject', 'Label host')
host = node('GeometryNodeObjectInfo', 'Host world transform')
host.transform_space = 'ORIGINAL'
g.links.new(self_object.outputs[0], host.inputs['Object'])
inverse = node('FunctionNodeInvertMatrix', 'World to host')
g.links.new(host.outputs['Transform'], inverse.inputs[0])
camera_rotation = node('FunctionNodeCombineTransform', 'Camera orientation without translation or scale')
g.links.new(camera.outputs['Rotation'], camera_rotation.inputs['Rotation'])
roll = node('FunctionNodeCombineTransform', 'Label in-plane rotation')
g.links.new(g.nodes['Combine XYZ.001'].outputs[0], roll.inputs['Rotation'])

def multiply(a, b, label):
    n = node('FunctionNodeMatrixMultiply', label)
    g.links.new(a, n.inputs[0])
    g.links.new(b, n.inputs[1])
    return n.outputs[0]

world = multiply(camera_rotation.outputs[0], roll.outputs[0], 'Camera and label rotation')
local = multiply(inverse.outputs[0], world, 'Compensate host rotation and scale')
# Text is subsequently placed at its local anchor; only transform its offsets.
parts = node('FunctionNodeSeparateTransform', 'Remove inverse host translation')
g.links.new(local, parts.inputs[0])
translate = node('FunctionNodeCombineTransform', 'Cancel inverse host translation')
neg = node('ShaderNodeVectorMath', 'Negate translation')
neg.operation = 'SCALE'
neg.inputs['Scale'].default_value = -1
g.links.new(parts.outputs['Translation'], neg.inputs[0])
g.links.new(neg.outputs[0], translate.inputs['Translation'])
local = multiply(translate.outputs[0], local, 'Camera-facing local offsets')
switch = node('GeometryNodeSwitch', 'Camera or host-plane text')
switch.input_type = 'MATRIX'
g.links.new(g.nodes['Group Input.011'].outputs['Face Active Camera'], switch.inputs['Switch'])
g.links.new(roll.outputs[0], switch.inputs['False'])
g.links.new(local, switch.inputs['True'])
for name, source, destination, socket in [
    ('Transform Geometry.001', 'Transform Geometry.005', 'Join Geometry', 'Geometry'),
    ('Transform Geometry.002', 'Transform Geometry.004', 'Switch', 'True'),
]:
    transform = g.nodes[name]
    # GP layer transforms decompose matrices and lose shear. Transform realized
    # curves instead so rotated, nonuniform parents are compensated exactly.
    curves = node('GeometryNodeGreasePencilToCurves', 'Realize glyph layer transforms')
    curves.inputs['Layers as Instances'].default_value = False
    g.links.new(g.nodes[source].outputs[0], curves.inputs[0])
    g.links.new(curves.outputs[0], transform.inputs['Geometry'])
    transform.inputs['Mode'].default_value = 'Matrix'
    g.links.new(switch.outputs[0], transform.inputs['Transform'])
    gp = node('GeometryNodeCurvesToGreasePencil', 'Oriented glyph strokes')
    gp.inputs['Instances as Layers'].default_value = False
    g.links.new(transform.outputs[0], gp.inputs[0])
    for link in list(g.links):
        if link.from_node == transform and link.to_node == g.nodes[destination]:
            g.links.remove(link)
    g.links.new(gp.outputs[0], g.nodes[destination].inputs[socket])
g['gp_camera_facing_version'] = 1
result = {'camera_facing_host_compensation': True}
