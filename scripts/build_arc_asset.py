# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the GP angle arc without rebuilding the existing arrow assets."""
import bpy
from math import pi
from pathlib import Path

sign_script=Path(__file__).resolve().parent/'build_vector_sign.py'
if sign_script.exists():
    sign_ns={'__file__':str(sign_script),'__name__':'__main__'}
    exec(compile(sign_script.read_text(encoding='utf-8'),str(sign_script),'exec'),sign_ns)

NAME='GP Arrow • Angle Arc'
g=bpy.data.node_groups.get(NAME) or bpy.data.node_groups.new(NAME,'GeometryNodeTree')
g.nodes.clear();g.is_modifier=True;g.use_fake_user=True
g.description='Directed GP angle arc between two coplanar lines defined by four object origins. Uses their intersection as center. Clockwise chooses the alternate sweep. A selected 90-degree angle becomes a square corner marker. Skew, parallel, or zero-length vectors produce no geometry.'

def socket(name,typ,default=None,out=False,desc=''):
    s=next((s for s in g.interface.items_tree if s.item_type=='SOCKET' and s.name==name and s.in_out==('OUTPUT' if out else 'INPUT')),None)
    if s:return s
    s=g.interface.new_socket(name=name,in_out='OUTPUT' if out else 'INPUT',socket_type='NodeSocket'+typ);s.description=desc
    if default is not None:s.default_value=default
    if typ in ('Float','Int') and not out:s.min_value=0
    return s
def node(typ,label=''):
    n=g.nodes.new(typ);n.label=label;n.width=190;return n
def link(a,b):g.links.new(a,b)
def put(n,key,value):
    if isinstance(value,bpy.types.NodeSocket):link(value,n.inputs[key])
    else:n.inputs[key].default_value=value
def vm(op,a,b=None):
    n=node('ShaderNodeVectorMath');n.operation=op;put(n,0,a)
    if b is not None:put(n,1,b)
    return n.outputs['Value' if op in ('LENGTH','DISTANCE','DOT_PRODUCT') else 'Vector']
def scalar(op,a,b=0):
    n=node('ShaderNodeMath');n.operation=op;put(n,0,a);put(n,1,b);return n.outputs[0]
def scale(a,b):
    n=node('ShaderNodeVectorMath');n.operation='SCALE';put(n,0,a);put(n,'Scale',b);return n.outputs[0]
def switch(typ,condition,a,b):
    n=node('GeometryNodeSwitch');n.input_type=typ;put(n,'Switch',condition)
    if a is not None:put(n,'False',a)
    if b is not None:put(n,'True',b)
    return n.outputs[0]
def attr(name,typ):
    n=node('GeometryNodeInputNamedAttribute');n.data_type=typ;put(n,'Name',name);return n.outputs['Attribute']
def store(geo,name,typ,value):
    n=node('GeometryNodeStoreNamedAttribute',name);n.domain='POINT';n.data_type=typ;put(n,'Geometry',geo);put(n,'Name',name);put(n,'Value',value);return n.outputs[0]
def line(a,b):
    n=node('GeometryNodeCurvePrimitiveLine');put(n,'Start',a);put(n,'End',b);return n.outputs[0]
def to_curves(geo):
    n=node('GeometryNodeGreasePencilToCurves');put(n,'Layers as Instances',False);put(n,0,geo);return n.outputs[0]
def to_gp(geo):
    n=node('GeometryNodeCurvesToGreasePencil');put(n,'Instances as Layers',False);put(n,0,geo);return n.outputs[0]
def xyz(a):
    n=node('ShaderNodeSeparateXYZ');put(n,0,a);return [n.outputs[k] for k in ('X','Y','Z')]
def join(*items):
    n=node('GeometryNodeJoinGeometry')
    for geo in items:link(geo,n.inputs[0])
    return n.outputs[0]
def transform_point(point,matrix,direction=False):
    n=node('FunctionNodeTransformDirection' if direction else 'FunctionNodeTransformPoint');put(n,0,point);put(n,'Transform',matrix);return n.outputs[0]

socket('Arc','Geometry',out=True)
socket('Valid Plane','Bool',out=True)
socket('Angle','Float',out=True,desc='Magnitude of the selected sweep, in radians; may exceed pi.')
socket('Right Angle','Bool',out=True)
socket('Center','Vector',out=True,desc='Intersection of the two lines in host local coordinates.')
for name in ('Vector 1 Start','Vector 1 End','Vector 2 Start','Vector 2 End'):socket(name,'Object')
socket('Radius','Float',.7,desc='World-space radius; for the right-angle marker, the leg distance from the intersection.')
socket('Clockwise','Bool',False,desc='Direction from Vector 1 to Vector 2, viewed from the positive canonical plane normal. May select a reflex angle.')
socket('Resolution','Int',96)
socket('Coplanarity Tolerance','Float',.0001,desc='Maximum separation of the two infinite lines in world units.')
socket('Right Angle Tolerance','Float',.1,desc='Tolerance in degrees for replacing a 90-degree sweep with a square corner.')
socket('Thickness','Float',.025)
socket('Color','Color',(1,.65,.1,1));socket('Opacity','Float',1.)
socket('Show Arrowhead','Bool',True);socket('Head Length','Float',.15);socket('Head Width','Float',.12)
socket('Show Label','Bool',False);socket('Label','String','θ');socket('Label Size','Float',.25)
socket('Vector Sign','Bool',False,desc='Add mathematical vector notation above the label.')
socket('Label Gap','Float',.15);socket('Label Offset','Vector',(0,0,0),desc='Additional offset in the plane basis: Vector 1, normal cross Vector 1, normal.')
socket('Face Camera','Bool',True);socket('Use Label Color','Bool',False);socket('Label Color','Color',(1,1,1,1))
i=node('NodeGroupInput');o=node('NodeGroupOutput')
positions=[]
for name in ('Vector 1 Start','Vector 1 End','Vector 2 Start','Vector 2 End'):
    n=node('GeometryNodeObjectInfo',name);n.transform_space='ORIGINAL';put(n,'Object',i.outputs[name]);positions.append(n.outputs['Location'])
a,ae,b,be=positions;d1=vm('SUBTRACT',ae,a);d2=vm('SUBTRACT',be,b)
u=vm('NORMALIZE',d1);v=vm('NORMALIZE',d2);raw=vm('CROSS_PRODUCT',u,v);den=vm('DOT_PRODUCT',raw,raw);w=vm('SUBTRACT',b,a)
s=scalar('DIVIDE',vm('DOT_PRODUCT',vm('CROSS_PRODUCT',w,v),raw),den)
t=scalar('DIVIDE',vm('DOT_PRODUCT',vm('CROSS_PRODUCT',w,u),raw),den)
c1=vm('ADD',a,scale(u,s));c2=vm('ADD',b,scale(v,t));center=scale(vm('ADD',c1,c2),.5)
checks=[scalar('GREATER_THAN',vm('LENGTH',d1),1e-6),scalar('GREATER_THAN',vm('LENGTH',d2),1e-6),scalar('GREATER_THAN',vm('LENGTH',raw),1e-6),scalar('LESS_THAN',vm('DISTANCE',c1,c2),scalar('MAXIMUM',i.outputs['Coplanarity Tolerance'],1e-7)),scalar('GREATER_THAN',i.outputs['Radius'],1e-6)]
valid=checks[0]
for check in checks[1:]:valid=scalar('MULTIPLY',valid,check)
# Orient the plane independently of the signs of its spanning vectors.
x,y,z=xyz(raw);ax,ay,az=[scalar('ABSOLUTE',p) for p in (x,y,z)]
dominant=switch('FLOAT',scalar('GREATER_THAN',ay,az),z,y)
dominant=switch('FLOAT',scalar('GREATER_THAN',ax,scalar('MAXIMUM',ay,az)),dominant,x)
normal=scale(vm('NORMALIZE',raw),switch('FLOAT',scalar('LESS_THAN',dominant,0),1.,-1.));q=vm('CROSS_PRODUCT',normal,u)
signed=scalar('ARCTAN2',vm('DOT_PRODUCT',normal,raw),vm('DOT_PRODUCT',u,v))
positive=switch('FLOAT',scalar('LESS_THAN',signed,0),signed,scalar('ADD',signed,2*pi))
sweep=switch('FLOAT',i.outputs['Clockwise'],positive,scalar('SUBTRACT',positive,2*pi));sign=switch('FLOAT',i.outputs['Clockwise'],1.,-1.)
angle=scalar('ABSOLUTE',sweep)
right=scalar('LESS_THAN',scalar('ABSOLUTE',scalar('SUBTRACT',angle,pi/2)),scalar('MAXIMUM',scalar('MULTIPLY',i.outputs['Right Angle Tolerance'],pi/180),1e-7))
radius=i.outputs['Radius'];start=vm('ADD',center,scale(u,radius));end_basis=switch('VECTOR',right,v,scale(q,sign));end=vm('ADD',center,scale(end_basis,radius))
tangent=switch('VECTOR',right,scale(vm('CROSS_PRODUCT',normal,v),sign),scale(u,-1.))
head_length=scalar('MINIMUM',i.outputs['Head Length'],scalar('MINIMUM',scalar('MULTIPLY',scalar('MULTIPLY',angle,radius),.25),scalar('MULTIPLY',radius,.35)))
head_length=switch('FLOAT',i.outputs['Show Arrowhead'],0.,head_length);base=vm('SUBTRACT',end,scale(tangent,head_length))

primitive=line((0,0,0),(1,0,0));resample=node('GeometryNodeResampleCurve','Arc samples');put(resample,'Curve',primitive);put(resample,'Count',scalar('MAXIMUM',i.outputs['Resolution'],8))
index=node('GeometryNodeInputIndex').outputs[0];factor=scalar('DIVIDE',index,scalar('SUBTRACT',scalar('MAXIMUM',i.outputs['Resolution'],8),1))
trimmed=scalar('SUBTRACT',sweep,scalar('MULTIPLY',sign,scalar('DIVIDE',head_length,radius)));theta=scalar('MULTIPLY',factor,trimmed)
radial=vm('ADD',scale(u,scalar('COSINE',theta)),scale(q,scalar('SINE',theta)))
arc_pos=vm('ADD',center,scale(radial,radius));arc_pos=switch('VECTOR',scalar('GREATER_THAN',factor,.999999),arc_pos,base)
setpos=node('GeometryNodeSetPosition','Circular arc to cone base');put(setpos,'Geometry',resample.outputs[0]);put(setpos,'Position',arc_pos)
corner=vm('ADD',start,scale(end_basis,radius));rect=join(line(start,corner),line(corner,base))
stroke=switch('GEOMETRY',right,setpos.outputs[0],rect)
rr=node('GeometryNodeSetCurveRadius');put(rr,0,stroke);put(rr,'Radius',scalar('MULTIPLY',i.outputs['Thickness'],.5))
stroke=to_gp(rr.outputs[0]);mat=node('GeometryNodeSetMaterial');put(mat,0,stroke);put(mat,'Material',bpy.data.materials['GP Arrow • Stroke'])
color=node('GeometryNodeSetGreasePencilColor');color.mode='STROKE';put(color,0,mat.outputs[0]);put(color,'Color',i.outputs['Color']);put(color,'Opacity',i.outputs['Opacity'])
stroke=store(color.outputs[0],'gp_arc_stroke','BOOLEAN',True)

# Reuse the GP Arrow cone, removing its straight shaft.
head=node('GeometryNodeGroup','GP Arrow conical head');head.node_tree=bpy.data.node_groups['GP Arrow • Object to Object']
put(head,'Use Positions',True);put(head,'Start',vm('SUBTRACT',end,scale(tangent,scalar('MULTIPLY',head_length,2.5))));put(head,'End',end)
put(head,'Head Length',head_length)
for name in ('Thickness','Color','Opacity','Head Width'):put(head,name,i.outputs[name])
put(head,'Show Label',False);put(head,'Show Arrowhead',True)
delete=node('GeometryNodeDeleteGeometry','Keep cone faces only');delete.domain='POINT';put(delete,0,head.outputs['Arrow']);put(delete,'Selection',scalar('SUBTRACT',1.,attr('gp_arrow_head','BOOLEAN')))
headgeo=switch('GEOMETRY',i.outputs['Show Arrowhead'],None,delete.outputs[0])

half=scalar('MULTIPLY',sweep,.5);middle=vm('ADD',scale(u,scalar('COSINE',half)),scale(q,scalar('SINE',half)))
label_radius=scalar('ADD',scalar('MULTIPLY',radius,switch('FLOAT',right,1.,2**.5)),i.outputs['Label Gap'])
anchor=vm('ADD',center,scale(middle,label_radius));ox,oy,oz=xyz(i.outputs['Label Offset'])
anchor=vm('ADD',anchor,vm('ADD',vm('ADD',scale(u,ox),scale(q,oy)),scale(normal,oz)))
text=node('GeometryNodeGroup','Arc label');text.node_tree=bpy.data.node_groups['GP Arrow • Label (GP Text Nodes 5.2)']
put(text,'String',i.outputs['Label']);put(text,'Size',i.outputs['Label Size']);put(text,'Font',bpy.data.fonts.get('Bfont Regular') or bpy.data.fonts.get('Bfont') or next(iter(bpy.data.fonts),None));put(text,'Face Active Camera',False)
put(text,'Vector Sign',i.outputs['Vector Sign'])
put(text,'Color',switch('RGBA',i.outputs['Use Label Color'],i.outputs['Color'],i.outputs['Label Color']));put(text,'Opacity',i.outputs['Opacity'])
label_curves=to_curves(text.outputs[0])
plane_rotation=node('FunctionNodeAxesToRotation','Label plane basis');plane_rotation.primary_axis='X';plane_rotation.secondary_axis='Y';put(plane_rotation,'Primary Axis',u);put(plane_rotation,'Secondary Axis',q)
camera=node('GeometryNodeInputActiveCamera');info=node('GeometryNodeObjectInfo','Active camera orientation');info.transform_space='ORIGINAL';put(info,'Object',camera.outputs[0])
# Transform entire curves: Set Position rotates control points but only
# translates their Bezier handles, distorting filled glyph outlines.
lp=node('GeometryNodeTransform','Label at selected sweep midpoint');put(lp,'Geometry',label_curves);put(lp,'Translation',anchor);put(lp,'Rotation',switch('ROTATION',i.outputs['Face Camera'],plane_rotation.outputs[0],info.outputs['Rotation']))
label=store(to_gp(lp.outputs[0]),'gp_arc_label','BOOLEAN',True);label=switch('GEOMETRY',i.outputs['Show Label'],None,label)

selfnode=node('GeometryNodeSelfObject');host=node('GeometryNodeObjectInfo','Host world transform');host.transform_space='ORIGINAL';put(host,'Object',selfnode.outputs[0])
inverse=node('FunctionNodeInvertMatrix');put(inverse,0,host.outputs['Transform'])
world_geometry=to_curves(join(stroke,headgeo,label));transform=node('GeometryNodeTransform','World arc into host coordinates');put(transform,'Mode','Matrix');put(transform,'Geometry',world_geometry);put(transform,'Transform',inverse.outputs[0])
geo=to_gp(transform.outputs[0]);local_center=transform_point(center,inverse.outputs[0]);local_start=transform_point(start,inverse.outputs[0]);local_end=transform_point(end,inverse.outputs[0])
for name,typ,value in [('gp_arc_center','FLOAT_VECTOR',local_center),('gp_arc_start','FLOAT_VECTOR',local_start),('gp_arc_end','FLOAT_VECTOR',local_end),('gp_arc_angle','FLOAT',angle),('gp_arc_right_angle','BOOLEAN',right)]:geo=store(geo,name,typ,value)
link(switch('GEOMETRY',valid,None,geo),o.inputs['Arc']);link(valid,o.inputs['Valid Plane']);link(angle,o.inputs['Angle']);link(right,o.inputs['Right Angle']);link(local_center,o.inputs['Center'])

depths={}
def depth(n):
    if n.name not in depths:depths[n.name]=1+max([depth(l.from_node) for s in n.inputs for l in s.links],default=-1)
    return depths[n.name]
rows={}
for n in g.nodes:
    d=depth(n);r=rows.get(d,0);rows[d]=r+1;n.location=(d*245,-r*235)
g.asset_mark();g.asset_data.description=g.description;g.asset_data.catalog_id='9b930084-69fa-4efa-914a-d6df09d23541'
for tag in ('Grease Pencil','Arrow','Angle','Arc'):g.asset_data.tags.new(tag)
result={'asset':g.name,'nodes':len(g.nodes)}
