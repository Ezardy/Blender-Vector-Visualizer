# SPDX-License-Identifier: GPL-3.0-or-later
"""Add optional mathematical vector notation to the shared GP label group."""
import bpy

g=bpy.data.node_groups['GP Arrow • Label (GP Text Nodes 5.2)']
if not any(s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name=='Vector Sign' for s in g.interface.items_tree):
    s=g.interface.new_socket(name='Vector Sign',in_out='INPUT',socket_type='NodeSocketBool');s.default_value=False
    s.description='Draw a small right-pointing vector arrow above the label.'
target=g.nodes['Transform Geometry.005']
if 'gp_vector_sign_base_node' not in g:
    original=target.inputs['Geometry'].links[0]
    g['gp_vector_sign_base_node']=original.from_node.name
    g['gp_vector_sign_base_socket']=list(original.from_node.outputs).index(original.from_socket)
for n in list(g.nodes):
    if n.get('gp_vector_sign_node'):g.nodes.remove(n)
base=g.nodes[g['gp_vector_sign_base_node']].outputs[g['gp_vector_sign_base_socket']]
g.links.new(base,target.inputs['Geometry'])
made=[]
def node(typ,label=''):
    n=g.nodes.new(typ);n.label=label;n['gp_vector_sign_node']=True;n.width=180;made.append(n);return n
def put(n,key,value):
    if isinstance(value,bpy.types.NodeSocket):g.links.new(value,n.inputs[key])
    else:n.inputs[key].default_value=value
def math(op,a,b=0):
    n=node('ShaderNodeMath');n.operation=op;put(n,0,a);put(n,1,b);return n.outputs[0]
def vector(x,y,z=0):
    n=node('ShaderNodeCombineXYZ');put(n,'X',x);put(n,'Y',y);put(n,'Z',z);return n.outputs[0]
inputs=node('NodeGroupInput','Vector notation controls')
curves=node('GeometryNodeGreasePencilToCurves','Unrotated glyph geometry');put(curves,0,base);put(curves,'Layers as Instances',False)
bounds=node('GeometryNodeBoundBox','Fit the sign to the actual label');put(bounds,'Geometry',curves.outputs[0])
lo=node('ShaderNodeSeparateXYZ');put(lo,0,bounds.outputs['Min'])
hi=node('ShaderNodeSeparateXYZ');put(hi,0,bounds.outputs['Max'])
size=inputs.outputs['Size'];center=math('MULTIPLY',math('ADD',lo.outputs['X'],hi.outputs['X']),.5)
width=math('MAXIMUM',math('SUBTRACT',hi.outputs['X'],lo.outputs['X']),math('MULTIPLY',size,.35))
left=math('SUBTRACT',center,math('MULTIPLY',width,.5));right=math('ADD',center,math('MULTIPLY',width,.5))
height=math('ADD',hi.outputs['Y'],math('MULTIPLY',size,.18))
head_length=math('MINIMUM',math('MULTIPLY',size,.16),math('MULTIPLY',width,.3))
head_x=math('SUBTRACT',right,head_length);head_y=math('MULTIPLY',size,.075)
join=node('GeometryNodeJoinGeometry','Mathematical vector arrow')
for a,b in [(vector(left,height),vector(right,height)),(vector(head_x,math('ADD',height,head_y)),vector(right,height)),(vector(head_x,math('SUBTRACT',height,head_y)),vector(right,height))]:
    line=node('GeometryNodeCurvePrimitiveLine');put(line,'Start',a);put(line,'End',b);g.links.new(line.outputs[0],join.inputs[0])
radius=node('GeometryNodeSetCurveRadius');put(radius,0,join.outputs[0]);put(radius,'Radius',math('MULTIPLY',size,.018))
gp=node('GeometryNodeCurvesToGreasePencil');put(gp,0,radius.outputs[0]);put(gp,'Instances as Layers',False)
mat=node('GeometryNodeSetMaterial');put(mat,0,gp.outputs[0]);put(mat,'Material',bpy.data.materials['GP Arrow • Stroke'])
color=node('GeometryNodeSetGreasePencilColor');color.mode='STROKE';put(color,0,mat.outputs[0]);put(color,'Color',inputs.outputs['Color']);put(color,'Opacity',inputs.outputs['Opacity'])
tag=node('GeometryNodeStoreNamedAttribute','Vector-sign points');tag.data_type='BOOLEAN';tag.domain='POINT';put(tag,0,color.outputs[0]);put(tag,'Name','gp_label_vector_sign');put(tag,'Value',True)
count=node('GeometryNodeAttributeDomainSize');count.component='CURVE';put(count,0,curves.outputs[0])
enabled=math('MULTIPLY',inputs.outputs['Vector Sign'],math('GREATER_THAN',count.outputs['Point Count'],0))
switch=node('GeometryNodeSwitch');switch.input_type='GEOMETRY';put(switch,'Switch',enabled);put(switch,'True',tag.outputs[0])
combined=node('GeometryNodeJoinGeometry','Label and optional vector sign');g.links.new(base,combined.inputs[0]);g.links.new(switch.outputs[0],combined.inputs[0]);g.links.new(combined.outputs[0],target.inputs['Geometry'])
# The original Z-depth and camera-rotation nodes transform the glyphs and sign together.
frame=node('NodeFrame','Vector notation above label');frame.label='Optional vector notation — fitted to label bounds'
for idx,n in enumerate(made[:-1]):n.parent=frame;n.location=((idx%6)*220,-(idx//6)*180)
frame.location=(-1500,-1800)
g['gp_vector_sign_version']=1

installed=[]
for name in ['GP Arrow • Object to Object','GP Arrow • Closest Surface Normal','GP Arrow • Perpendicular in Plane','GP Arrow • Angle Arc']:
    outer=bpy.data.node_groups.get(name)
    if not outer:continue
    socket=next((s for s in outer.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name=='Vector Sign'),None)
    if socket is None:
        socket=outer.interface.new_socket(name='Vector Sign',in_out='INPUT',socket_type='NodeSocketBool');socket.default_value=False
        socket.description='Add mathematical vector notation above the label. Projection and Parallel inherit this from the source.'
    label_socket=next((s for s in outer.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name=='Show Label'),None)
    if label_socket:outer.interface.move(socket,list(outer.interface.items_tree).index(label_socket)+1)
    source=next((n for n in outer.nodes if n.type=='GROUP_INPUT'),None)
    if source:
        for n in outer.nodes:
            if n.type=='GROUP' and n.node_tree and (n.node_tree==g or (name in ['GP Arrow • Closest Surface Normal','GP Arrow • Perpendicular in Plane'] and n.node_tree.name=='GP Arrow • Object to Object')):
                if n.inputs.get('Vector Sign'):outer.links.new(source.outputs['Vector Sign'],n.inputs['Vector Sign'])
    installed.append(name)
result={'vector_sign_controls':installed,'shared_label_group':g.name}
