# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] if '__file__' in globals() else Path(bpy.data.filepath).parent

def group(name, desc):
    g = bpy.data.node_groups.get(name) or bpy.data.node_groups.new(name, 'GeometryNodeTree')
    g.nodes.clear()
    g.description = desc
    g.is_modifier = True
    g.use_fake_user = True
    return g

def sock(g, name, typ, default=None, out=False, desc=''):
    existing=next((s for s in g.interface.items_tree if s.item_type=='SOCKET' and s.name==name and s.in_out==('OUTPUT' if out else 'INPUT')),None)
    if existing:
        existing.description=desc
        return existing
    s = g.interface.new_socket(name=name, in_out='OUTPUT' if out else 'INPUT', socket_type='NodeSocket'+typ)
    s.description = desc
    if default is not None: s.default_value = default
    if typ == 'Float' and not out: s.min_value = 0
    return s

def node(g, typ, label='', x=0, y=0):
    n = g.nodes.new(typ); n.label = label; n.location=(x,y); n.width=190
    return n

def link(g, a, b): g.links.new(a,b)

def vm(g, op, a, b=None, label=''):
    n=node(g,'ShaderNodeVectorMath',label); n.operation=op
    for i,v in enumerate([a,b]):
        if v is None: continue
        if isinstance(v,bpy.types.NodeSocket): link(g,v,n.inputs[i])
        else: n.inputs[i].default_value=v
    return n.outputs['Value'] if op in {'LENGTH','DISTANCE','DOT_PRODUCT'} else n.outputs['Vector']

def scale(g,a,b):
    n=node(g,'ShaderNodeVectorMath'); n.operation='SCALE'; link(g,a,n.inputs[0])
    if isinstance(b,bpy.types.NodeSocket): link(g,b,n.inputs['Scale'])
    else: n.inputs['Scale'].default_value=b
    return n.outputs['Vector']

def math(g,op,a,b):
    n=node(g,'ShaderNodeMath'); n.operation=op
    for i,v in enumerate([a,b]):
        if isinstance(v,bpy.types.NodeSocket): link(g,v,n.inputs[i])
        else:n.inputs[i].default_value=v
    return n.outputs[0]

def switch(g,typ,cond,a,b):
    n=node(g,'GeometryNodeSwitch');n.input_type=typ
    link(g,cond,n.inputs['Switch'])
    for name,v in [('False',a),('True',b)]:
        if isinstance(v,bpy.types.NodeSocket):link(g,v,n.inputs[name])
        elif v is not None:n.inputs[name].default_value=v
    return n.outputs[0]

def store(g,geo,name,typ,value):
    n=node(g,'GeometryNodeStoreNamedAttribute',name);n.data_type=typ;n.domain='POINT';n.inputs['Name'].default_value=name;link(g,geo,n.inputs['Geometry'])
    if isinstance(value,bpy.types.NodeSocket):link(g,value,n.inputs['Value'])
    else:n.inputs['Value'].default_value=value
    return n.outputs[0]

def named(g,name,typ):
    n=node(g,'GeometryNodeInputNamedAttribute',name);n.data_type=typ;n.inputs['Name'].default_value=name;return n.outputs['Attribute']

arrow=group('GP Arrow • Object to Object','Live Grease Pencil arrow between object origins. Use on a Grease Pencil object; enable In Front on the object. Thickness is full stroke diameter in host local units.')
sock(arrow,'Arrow','Geometry',out=True)
sock(arrow,'Start Position','Vector',out=True);sock(arrow,'End Position','Vector',out=True)
sock(arrow,'Start Object','Object');sock(arrow,'End Object','Object')
sock(arrow,'Thickness','Float',0.025)
sock(arrow,'Color','Color',(0.08,0.45,1,1))
sock(arrow,'Opacity','Float',1)
sock(arrow,'Head Length','Float',0.25)
sock(arrow,'Head Width','Float',0.18)
sock(arrow,'Show Arrowhead','Bool',True)
for s in list(arrow.interface.items_tree):
    if s.item_type=='SOCKET' and s.name=='Head Up':arrow.interface.remove(s)
sock(arrow,'Show Label','Bool',False)
sock(arrow,'Label','String','')
sock(arrow,'Label Size','Float',0.25)
sock(arrow,'Label Offset','Vector',(0.12,0.12,0))
sock(arrow,'Face Camera','Bool',True)
sock(arrow,'Use Label Color','Bool',False,desc='Enable an independent label color; otherwise follow the arrow color.')
sock(arrow,'Label Color','Color',(1,1,1,1))
for name,typ,default in [('Use Positions','Bool',False),('Start','Vector',(0,0,0)),('End','Vector',(0,0,1))]:
    sock(arrow,name,typ,default).hide_in_modifier=True
i=node(arrow,'NodeGroupInput');o=node(arrow,'NodeGroupOutput')
ends=[]
for name in ['Start Object','End Object']:
    n=node(arrow,'GeometryNodeObjectInfo',name);n.transform_space='RELATIVE';link(arrow,i.outputs[name],n.inputs['Object']);ends.append(n.outputs['Location'])
a=switch(arrow,'VECTOR',i.outputs['Use Positions'],ends[0],i.outputs['Start'])
b=switch(arrow,'VECTOR',i.outputs['Use Positions'],ends[1],i.outputs['End'])
delta=vm(arrow,'SUBTRACT',b,a);length=vm(arrow,'LENGTH',delta);direction=vm(arrow,'NORMALIZE',delta)
headlen=math(arrow,'MINIMUM',i.outputs['Head Length'],math(arrow,'MULTIPLY',length,0.45))
base=vm(arrow,'SUBTRACT',b,scale(arrow,direction,headlen))
n=node(arrow,'GeometryNodeCurvePrimitiveLine','Shaft');link(arrow,a,n.inputs['Start']);link(arrow,switch(arrow,'VECTOR',i.outputs['Show Arrowhead'],b,base),n.inputs['End'])
r=node(arrow,'GeometryNodeSetCurveRadius');link(arrow,n.outputs[0],r.inputs['Curve']);link(arrow,math(arrow,'MULTIPLY',i.outputs['Thickness'],0.5),r.inputs['Radius'])
gp=node(arrow,'GeometryNodeCurvesToGreasePencil');gp.inputs['Instances as Layers'].default_value=False;link(arrow,r.outputs[0],gp.inputs['Curves'])
mat=bpy.data.materials.get('GP Arrow • Stroke') or bpy.data.materials.new('GP Arrow • Stroke')
if not mat.is_grease_pencil:bpy.data.materials.create_gpencil_data(mat)
mat.grease_pencil.color=(1,1,1,1);mat.grease_pencil.show_fill=False
sm=node(arrow,'GeometryNodeSetMaterial');sm.inputs['Material'].default_value=mat;link(arrow,gp.outputs[0],sm.inputs['Geometry'])
col=node(arrow,'GeometryNodeSetGreasePencilColor');col.mode='STROKE';link(arrow,sm.outputs[0],col.inputs[0]);link(arrow,i.outputs['Color'],col.inputs['Color']);link(arrow,i.outputs['Opacity'],col.inputs['Opacity'])
shaftgeo=store(arrow,col.outputs[0],'gp_arrow_shaft','BOOLEAN',True)
# A genuine cone converted face-by-face to cyclic filled GP strokes.
cone=node(arrow,'GeometryNodeMeshCone','Conical arrowhead');cone.inputs['Vertices'].default_value=32;cone.inputs['Radius Top'].default_value=0
link(arrow,math(arrow,'MULTIPLY',i.outputs['Head Width'],.5),cone.inputs['Radius Bottom']);link(arrow,headlen,cone.inputs['Depth'])
align=node(arrow,'FunctionNodeAlignEulerToVector');align.axis='Z';link(arrow,direction,align.inputs['Vector'])
ct=node(arrow,'GeometryNodeTransform','Cone base at shaft end');link(arrow,cone.outputs['Mesh'],ct.inputs['Geometry']);link(arrow,align.outputs[0],ct.inputs['Rotation']);link(arrow,base,ct.inputs['Translation'])
split=node(arrow,'GeometryNodeSplitEdges','Separate cone faces');link(arrow,ct.outputs[0],split.inputs['Mesh'])
mc=node(arrow,'GeometryNodeMeshToCurve');link(arrow,split.outputs[0],mc.inputs['Mesh'])
cr=node(arrow,'GeometryNodeSetCurveRadius','Filled faces only');cr.inputs['Radius'].default_value=0;link(arrow,mc.outputs[0],cr.inputs['Curve'])
cg=node(arrow,'GeometryNodeCurvesToGreasePencil');cg.inputs['Instances as Layers'].default_value=False;link(arrow,cr.outputs[0],cg.inputs['Curves'])
fid=node(arrow,'GeometryNodeStoreNamedAttribute','One fill group per cone face');fid.data_type='INT';fid.domain='CURVE';fid.inputs['Name'].default_value='fill_id';link(arrow,cg.outputs[0],fid.inputs['Geometry'])
idx=node(arrow,'GeometryNodeInputIndex');link(arrow,math(arrow,'ADD',idx.outputs[0],1000000),fid.inputs['Value'])
fillmat=bpy.data.materials.get('GP Arrow • Cone Fill') or bpy.data.materials.new('GP Arrow • Cone Fill')
if not fillmat.is_grease_pencil:bpy.data.materials.create_gpencil_data(fillmat)
fillmat.grease_pencil.show_stroke=False;fillmat.grease_pencil.show_fill=True;fillmat.grease_pencil.fill_color=(1,1,1,1)
cm=node(arrow,'GeometryNodeSetMaterial');cm.inputs['Material'].default_value=fillmat;link(arrow,fid.outputs[0],cm.inputs['Geometry'])
cc=node(arrow,'GeometryNodeSetGreasePencilColor');cc.mode='FILL';link(arrow,cm.outputs[0],cc.inputs[0]);link(arrow,i.outputs['Color'],cc.inputs['Color']);link(arrow,i.outputs['Opacity'],cc.inputs['Opacity'])
headgeo=store(arrow,cc.outputs[0],'gp_arrow_head','BOOLEAN',True)
# Reuse the same text asset as the existing axis labels.
label_group=bpy.data.node_groups.get('GP Arrow • Label (GP Text Nodes 5.2)')
if not label_group:
    label_group=bpy.data.node_groups['GP Text Nodes 5.2'].copy();label_group.name='GP Arrow • Label (GP Text Nodes 5.2)';label_group.asset_clear()
text=node(arrow,'GeometryNodeGroup','Axis-label text asset');text.node_tree=label_group
text.inputs['Font'].default_value=bpy.data.fonts.get('Bfont Regular')
for src,dst in [('Label','String'),('Label Size','Size'),('Opacity','Opacity'),('Face Camera','Face Active Camera')]:link(arrow,i.outputs[src],text.inputs[dst])
link(arrow,switch(arrow,'RGBA',i.outputs['Use Label Color'],i.outputs['Color'],i.outputs['Label Color']),text.inputs['Color'])
tr=node(arrow,'GeometryNodeTransform');link(arrow,text.outputs[0],tr.inputs['Geometry']);link(arrow,vm(arrow,'ADD',b,i.outputs['Label Offset']),tr.inputs['Translation'])
labelgeo=tr.outputs[0]
for name,typ,val in [('gp_arrow_label','BOOLEAN',True),('gp_arrow_face_camera','BOOLEAN',i.outputs['Face Camera']),('gp_arrow_tip','FLOAT_VECTOR',b)]:
    labelstore=node(arrow,'GeometryNodeStoreNamedAttribute',name);labelstore.data_type=typ;labelstore.domain='POINT';labelstore.inputs['Name'].default_value=name;link(arrow,labelgeo,labelstore.inputs['Geometry'])
    if isinstance(val,bpy.types.NodeSocket):link(arrow,val,labelstore.inputs['Value'])
    else:labelstore.inputs['Value'].default_value=val
    labelgeo=labelstore.outputs[0]
label=switch(arrow,'GEOMETRY',i.outputs['Show Label'],None,labelgeo)
allgeo=node(arrow,'GeometryNodeJoinGeometry','Shaft, cone, and optional label');link(arrow,shaftgeo,allgeo.inputs[0]);link(arrow,switch(arrow,'GEOMETRY',i.outputs['Show Arrowhead'],None,headgeo),allgeo.inputs[0]);link(arrow,label,allgeo.inputs[0])
nonzero=math(arrow,'GREATER_THAN',length,0.000001)
arrowgeo=store(arrow,allgeo.outputs[0],'gp_arrow_start','FLOAT_VECTOR',a)
arrowgeo=store(arrow,arrowgeo,'gp_arrow_end','FLOAT_VECTOR',b)
arrowgeo=store(arrow,arrowgeo,'gp_arrow_head_length','FLOAT',switch(arrow,'FLOAT',i.outputs['Show Arrowhead'],0.,headlen))
link(arrow,switch(arrow,'GEOMETRY',nonzero,None,arrowgeo),o.inputs['Arrow'])
link(arrow,a,o.inputs['Start Position']);link(arrow,b,o.inputs['End Position'])

proj=group('GP Arrow • Project onto Plane','Project the incoming arrow onto the host local XY plane through the host origin (local Z=0). The plane follows host location, rotation, parenting, and scale. Camera-facing labels retain their orientation at the projected tip; other labels lie on local XY.')
sock(proj,'Arrow','Geometry',out=True);sock(proj,'Valid Plane','Bool',out=True)
sock(proj,'Arrow','Geometry')
sock(proj,'Create Start Empty','Bool',True,desc='Create/update a real child Empty at the projected start. Requires GP Arrow Objects.')
sock(proj,'Create End Empty','Bool',True,desc='Create/update a real child Empty at the projected tip. Requires GP Arrow Objects.')
for s in list(proj.interface.items_tree):
    if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name in ['Plane U','Plane V','Plane Origin']:proj.interface.remove(s)
i=node(proj,'NodeGroupInput');o=node(proj,'NodeGroupOutput')
ux=node(proj,'ShaderNodeCombineXYZ','Host local X');ux.inputs['X'].default_value=1
vy=node(proj,'ShaderNodeCombineXYZ','Host local Y');vy.inputs['Y'].default_value=1
zero=node(proj,'ShaderNodeCombineXYZ','Host origin (local zero)')
u=ux.outputs[0];v=vy.outputs[0];origin=zero.outputs[0]
normal=vm(proj,'CROSS_PRODUCT',u,v);valid=math(proj,'GREATER_THAN',vm(proj,'LENGTH',normal),0.000001);normal=vm(proj,'NORMALIZE',normal)
p=node(proj,'GeometryNodeInputPosition').outputs[0]
distance=vm(proj,'DOT_PRODUCT',vm(proj,'SUBTRACT',p,origin),normal)
position=vm(proj,'SUBTRACT',p,scale(proj,normal,distance))
attrs={}
for name,typ in [('gp_arrow_label','BOOLEAN'),('gp_arrow_face_camera','BOOLEAN'),('gp_arrow_tip','FLOAT_VECTOR')]:
    attr=node(proj,'GeometryNodeInputNamedAttribute',name);attr.data_type=typ;attr.inputs['Name'].default_value=name;attrs[name]=attr.outputs['Attribute']
tipdistance=vm(proj,'DOT_PRODUCT',vm(proj,'SUBTRACT',attrs['gp_arrow_tip'],origin),normal)
labelpos=vm(proj,'SUBTRACT',p,scale(proj,normal,tipdistance))
projectedtip=vm(proj,'SUBTRACT',attrs['gp_arrow_tip'],scale(proj,normal,tipdistance))
relative=vm(proj,'SUBTRACT',p,attrs['gp_arrow_tip'])
planey=vm(proj,'CROSS_PRODUCT',normal,u)
planarlabel=vm(proj,'ADD',projectedtip,vm(proj,'ADD',scale(proj,u,vm(proj,'DOT_PRODUCT',relative,(1,0,0))),scale(proj,planey,vm(proj,'DOT_PRODUCT',relative,(0,1,0)))))
labelposition=switch(proj,'VECTOR',attrs['gp_arrow_face_camera'],planarlabel,labelpos)
position=switch(proj,'VECTOR',attrs['gp_arrow_label'],position,labelposition)
# Rotate the original cone onto the projected axis, retaining its circular 3D base.
source_start=named(proj,'gp_arrow_start','FLOAT_VECTOR');source_end=named(proj,'gp_arrow_end','FLOAT_VECTOR')
source_delta=vm(proj,'SUBTRACT',source_end,source_start);source_length=vm(proj,'LENGTH',source_delta);source_axis=vm(proj,'NORMALIZE',source_delta)
target_start=vm(proj,'SUBTRACT',source_start,scale(proj,normal,vm(proj,'DOT_PRODUCT',source_start,normal)))
target_end=vm(proj,'SUBTRACT',source_end,scale(proj,normal,vm(proj,'DOT_PRODUCT',source_end,normal)))
target_delta=vm(proj,'SUBTRACT',target_end,target_start);target_length=vm(proj,'LENGTH',target_delta);target_axis=vm(proj,'NORMALIZE',target_delta)
old_head_length=named(proj,'gp_arrow_head_length','FLOAT');new_head_length=math(proj,'MINIMUM',old_head_length,math(proj,'MULTIPLY',target_length,.45))
relative_head=vm(proj,'SUBTRACT',p,source_end);axial=scale(proj,source_axis,vm(proj,'DOT_PRODUCT',relative_head,source_axis))
reshaped=vm(proj,'ADD',vm(proj,'SUBTRACT',relative_head,axial),scale(proj,axial,math(proj,'DIVIDE',new_head_length,old_head_length)))
rotate=node(proj,'ShaderNodeVectorRotate','Keep the cone three dimensional');rotate.rotation_type='AXIS_ANGLE';link(proj,reshaped,rotate.inputs['Vector']);link(proj,vm(proj,'NORMALIZE',vm(proj,'CROSS_PRODUCT',source_axis,target_axis)),rotate.inputs['Axis']);link(proj,math(proj,'ARCCOSINE',math(proj,'MINIMUM',1.,math(proj,'MAXIMUM',-1.,vm(proj,'DOT_PRODUCT',source_axis,target_axis))),0),rotate.inputs['Angle'])
head_position=vm(proj,'ADD',target_end,rotate.outputs['Vector'])
target_base=vm(proj,'SUBTRACT',target_end,scale(proj,target_axis,new_head_length))
shaft_factor=math(proj,'DIVIDE',vm(proj,'DOT_PRODUCT',vm(proj,'SUBTRACT',p,source_start),source_axis),math(proj,'SUBTRACT',source_length,old_head_length))
shaft_position=vm(proj,'ADD',target_start,scale(proj,vm(proj,'SUBTRACT',target_base,target_start),shaft_factor))
position=switch(proj,'VECTOR',named(proj,'gp_arrow_shaft','BOOLEAN'),position,shaft_position)
position=switch(proj,'VECTOR',named(proj,'gp_arrow_head','BOOLEAN'),position,head_position)
curves=node(proj,'GeometryNodeGreasePencilToCurves','Bake layer transforms before projection');curves.inputs['Layers as Instances'].default_value=False;link(proj,i.outputs['Arrow'],curves.inputs[0])
real=node(proj,'GeometryNodeRealizeInstances');link(proj,curves.outputs[0],real.inputs[0])
setp=node(proj,'GeometryNodeSetPosition');link(proj,real.outputs[0],setp.inputs['Geometry']);link(proj,position,setp.inputs['Position'])
back=node(proj,'GeometryNodeCurvesToGreasePencil');back.inputs['Instances as Layers'].default_value=False;link(proj,setp.outputs[0],back.inputs[0])
projectedgeo=back.outputs[0]
for attrname in ['gp_arrow_start','gp_arrow_end']:
    endpoint=named(proj,attrname,'FLOAT_VECTOR')
    projectedendpoint=vm(proj,'SUBTRACT',endpoint,scale(proj,normal,vm(proj,'DOT_PRODUCT',vm(proj,'SUBTRACT',endpoint,origin),normal)))
    projectedgeo=store(proj,projectedgeo,attrname,'FLOAT_VECTOR',projectedendpoint)
projectedgeo=store(proj,projectedgeo,'gp_arrow_tip','FLOAT_VECTOR',projectedtip)
projectedgeo=store(proj,projectedgeo,'gp_arrow_head_length','FLOAT',new_head_length)
projectedgeo=store(proj,projectedgeo,'gp_arrow_create_start','BOOLEAN',i.outputs['Create Start Empty'])
projectedgeo=store(proj,projectedgeo,'gp_arrow_create_end','BOOLEAN',i.outputs['Create End Empty'])
delete=node(proj,'GeometryNodeDeleteGeometry','Hide a zero-length projected vector');delete.domain='POINT';link(proj,projectedgeo,delete.inputs['Geometry']);link(proj,math(proj,'LESS_THAN',target_length,.000001),delete.inputs['Selection'])
link(proj,delete.outputs[0],o.inputs['Arrow']);link(proj,valid,o.inputs['Valid Plane'])

parallel=group('GP Arrow • Parallel from Origin','Reposition the incoming GP Arrow geometry at this host origin. Stack after GP Arrow or GP Projection on the same object. Reverse Direction flips the vector; Length controls its length unless Use Source Length is on. Preserves styling and readable labels.')
sock(parallel,'Arrow','Geometry',out=True)
for s in list(parallel.interface.items_tree):
    if s.item_type=='SOCKET' and s.name=='GP Arrow':parallel.interface.remove(s)
sock(parallel,'Arrow','Geometry',desc='Incoming geometry from the previous GP Arrow modifier on this object, or an Arrow node output.')
sock(parallel,'Reverse Direction','Bool',False)
sock(parallel,'Length','Float',1.0,desc='Desired length in host local units, when Use Source Length is off.')
sock(parallel,'Use Source Length','Bool',False)
sock(parallel,'Create End Empty','Bool',True)
parallel.interface.move(next(s for s in parallel.interface.items_tree if s.item_type=='SOCKET' and s.name=='Arrow' and s.in_out=='INPUT'),1)
i=node(parallel,'NodeGroupInput');o=node(parallel,'NodeGroupOutput')
cv=node(parallel,'GeometryNodeGreasePencilToCurves','Bake incoming layer transforms');cv.inputs['Layers as Instances'].default_value=False;link(parallel,i.outputs['Arrow'],cv.inputs[0])
def endpoint(name):
    attr=named(parallel,name,'FLOAT_VECTOR')
    sample=node(parallel,'GeometryNodeSampleIndex',name);sample.data_type='FLOAT_VECTOR';sample.domain='POINT';sample.inputs['Index'].default_value=0;link(parallel,cv.outputs[0],sample.inputs['Geometry']);link(parallel,attr,sample.inputs['Value'])
    return sample.outputs[0]
start=endpoint('gp_arrow_start');end=endpoint('gp_arrow_end')
delta=vm(parallel,'SUBTRACT',end,start);srclen=vm(parallel,'LENGTH',delta);direction=vm(parallel,'NORMALIZE',delta)
length=switch(parallel,'FLOAT',i.outputs['Use Source Length'],i.outputs['Length'],srclen)
sign=switch(parallel,'FLOAT',i.outputs['Reverse Direction'],1.,-1.)
tip=scale(parallel,direction,math(parallel,'MULTIPLY',length,sign))
p=node(parallel,'GeometryNodeInputPosition').outputs[0];q=vm(parallel,'SUBTRACT',p,start);along=vm(parallel,'DOT_PRODUCT',q,direction)
across=vm(parallel,'SUBTRACT',q,scale(parallel,direction,along))
bodypos=vm(parallel,'ADD',scale(parallel,across,sign),scale(parallel,tip,math(parallel,'DIVIDE',along,srclen)))
labelpos=vm(parallel,'ADD',p,vm(parallel,'SUBTRACT',tip,end))
position=switch(parallel,'VECTOR',named(parallel,'gp_arrow_label','BOOLEAN'),bodypos,labelpos)
sp=node(parallel,'GeometryNodeSetPosition');link(parallel,cv.outputs[0],sp.inputs['Geometry']);link(parallel,position,sp.inputs['Position'])
back=node(parallel,'GeometryNodeCurvesToGreasePencil');back.inputs['Instances as Layers'].default_value=False;link(parallel,sp.outputs[0],back.inputs[0])
geo=store(parallel,back.outputs[0],'gp_arrow_start','FLOAT_VECTOR',(0,0,0))
geo=store(parallel,geo,'gp_arrow_end','FLOAT_VECTOR',tip)
geo=store(parallel,geo,'gp_arrow_tip','FLOAT_VECTOR',tip)
geo=store(parallel,geo,'gp_arrow_head_length','FLOAT',math(parallel,'MULTIPLY',named(parallel,'gp_arrow_head_length','FLOAT'),math(parallel,'DIVIDE',length,srclen)))
geo=store(parallel,geo,'gp_arrow_create_end','BOOLEAN',i.outputs['Create End Empty'])
valid=math(parallel,'MULTIPLY',math(parallel,'GREATER_THAN',srclen,.000001),math(parallel,'GREATER_THAN',length,.000001))
link(parallel,switch(parallel,'GEOMETRY',valid,None,geo),o.inputs['Arrow'])

surface=group('GP Arrow • Closest Surface Normal','Sample the nearest surface point to the host origin in world space and draw its normal from the host origin using GP Arrow. Supports evaluated mesh modifiers and transformed hosts/targets.')
sock(surface,'Arrow','Geometry',out=True)
sock(surface,'Closest Point','Vector',out=True,desc='Closest surface point in host local coordinates.')
sock(surface,'Surface Normal','Vector',out=True,desc='Unit normal direction in host local coordinates.')
sock(surface,'Distance','Float',out=True,desc='Distance from host origin to surface in world units.')
sock(surface,'Surface Object','Object')
sock(surface,'Length','Float',1.0)
sock(surface,'Reverse Direction','Bool',False)
sock(surface,'Create End Empty','Bool',True)
styles=['Thickness','Color','Opacity','Show Arrowhead','Head Length','Head Width','Show Label','Label','Label Size','Label Offset','Face Camera','Use Label Color','Label Color']
for name in styles:
    s=next(s for s in arrow.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name==name)
    default=s.default_value
    if s.socket_type in ['NodeSocketVector','NodeSocketColor']:default=tuple(default)
    if name=='Label':default='n'
    sock(surface,name,s.socket_type.removeprefix('NodeSocket'),default)
i=node(surface,'NodeGroupInput');o=node(surface,'NodeGroupOutput')
target=node(surface,'GeometryNodeObjectInfo','Evaluated target mesh');target.transform_space='ORIGINAL';link(surface,i.outputs['Surface Object'],target.inputs['Object'])
real=node(surface,'GeometryNodeRealizeInstances');link(surface,target.outputs['Geometry'],real.inputs[0])
world=node(surface,'GeometryNodeTransform','Find closest point in world space');world.inputs['Mode'].default_value='Matrix';link(surface,real.outputs[0],world.inputs['Geometry']);link(surface,target.outputs['Transform'],world.inputs['Transform'])
selfnode=node(surface,'GeometryNodeSelfObject')
host=node(surface,'GeometryNodeObjectInfo','Host origin and transform');host.transform_space='ORIGINAL';link(surface,selfnode.outputs[0],host.inputs['Object'])
inverse=node(surface,'FunctionNodeInvertMatrix');link(surface,host.outputs['Transform'],inverse.inputs[0])
near=node(surface,'GeometryNodeProximity');near.target_element='FACES';link(surface,world.outputs[0],near.inputs['Geometry']);link(surface,host.outputs['Location'],near.inputs['Sample Position'])
normal=node(surface,'GeometryNodeInputNormal')
cap=node(surface,'GeometryNodeCaptureAttribute','Geometric face normals');cap.domain='FACE';cap.capture_items.new('VECTOR','Face Normal');link(surface,world.outputs[0],cap.inputs['Geometry']);link(surface,normal.outputs['Normal'],cap.inputs['Face Normal'])
sample=node(surface,'GeometryNodeSampleNearestSurface','Normal at closest surface point');sample.data_type='FLOAT_VECTOR';link(surface,cap.outputs['Geometry'],sample.inputs['Mesh']);link(surface,cap.outputs['Face Normal'],sample.inputs['Value']);link(surface,host.outputs['Location'],sample.inputs['Sample Position'])
localnormal=node(surface,'FunctionNodeTransformDirection');link(surface,sample.outputs['Value'],localnormal.inputs['Direction']);link(surface,inverse.outputs[0],localnormal.inputs['Transform'])
direction=vm(surface,'NORMALIZE',localnormal.outputs[0])
tip=scale(surface,direction,math(surface,'MULTIPLY',i.outputs['Length'],switch(surface,'FLOAT',i.outputs['Reverse Direction'],1.,-1.)))
point=node(surface,'FunctionNodeTransformPoint');link(surface,near.outputs['Position'],point.inputs['Vector']);link(surface,inverse.outputs[0],point.inputs['Transform'])
draw=node(surface,'GeometryNodeGroup','Draw with GP Arrow');draw.node_tree=arrow;draw.inputs['Use Positions'].default_value=True;draw.inputs['Start'].default_value=(0,0,0);link(surface,tip,draw.inputs['End'])
for name in styles:link(surface,i.outputs[name],draw.inputs[name])
geo=store(surface,draw.outputs['Arrow'],'gp_surface_point','FLOAT_VECTOR',point.outputs[0])
geo=store(surface,geo,'gp_surface_normal','FLOAT_VECTOR',direction)
geo=store(surface,geo,'gp_arrow_create_end','BOOLEAN',i.outputs['Create End Empty'])
link(surface,switch(surface,'GEOMETRY',sample.outputs['Is Valid'],None,geo),o.inputs['Arrow'])
link(surface,point.outputs[0],o.inputs['Closest Point']);link(surface,direction,o.inputs['Surface Normal']);link(surface,near.outputs['Distance'],o.inputs['Distance'])

perp=group('GP Arrow • Perpendicular in Plane','Draw from the host origin perpendicular to Vector 1 within the plane spanned by Vectors 1 and 2. Four object origins define the vectors. Reversing Vector 1 reverses the arrow; Vector 2 defines the plane. Plane normal uses a canonical world-space sign (largest absolute component positive).')
sock(perp,'Arrow','Geometry',out=True);sock(perp,'Direction','Vector',out=True,desc='Unit arrow direction in host local coordinates, including Reverse Direction.')
sock(perp,'Valid Plane','Bool',out=True)
for name in ['Vector 1 Start','Vector 1 End','Vector 2 Start','Vector 2 End']:sock(perp,name,'Object')
sock(perp,'Length','Float',1.)
sock(perp,'Reverse Direction','Bool',False)
sock(perp,'Create End Empty','Bool',True)
for name in styles:
    s=next(s for s in arrow.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name==name)
    default=s.default_value
    if s.socket_type in ['NodeSocketVector','NodeSocketColor']:default=tuple(default)
    if name=='Label':default='p'
    sock(perp,name,s.socket_type.removeprefix('NodeSocket'),default)
i=node(perp,'NodeGroupInput');o=node(perp,'NodeGroupOutput')
positions=[]
for name in ['Vector 1 Start','Vector 1 End','Vector 2 Start','Vector 2 End']:
    info=node(perp,'GeometryNodeObjectInfo',name);info.transform_space='ORIGINAL';link(perp,i.outputs[name],info.inputs['Object']);positions.append(info.outputs['Location'])
u=vm(perp,'NORMALIZE',vm(perp,'SUBTRACT',positions[1],positions[0]));v=vm(perp,'NORMALIZE',vm(perp,'SUBTRACT',positions[3],positions[2]))
rawnormal=vm(perp,'CROSS_PRODUCT',u,v);valid=math(perp,'GREATER_THAN',vm(perp,'LENGTH',rawnormal),.000001)
xyz=node(perp,'ShaderNodeSeparateXYZ','Canonical world plane orientation');link(perp,rawnormal,xyz.inputs[0])
x,y,z=[xyz.outputs[n] for n in ['X','Y','Z']]
ax,ay,az=[math(perp,'ABSOLUTE',a,0) for a in [x,y,z]]
dominant=switch(perp,'FLOAT',math(perp,'GREATER_THAN',ay,az),z,y)
dominant=switch(perp,'FLOAT',math(perp,'GREATER_THAN',ax,math(perp,'MAXIMUM',ay,az)),dominant,x)
normal=scale(perp,vm(perp,'NORMALIZE',rawnormal),switch(perp,'FLOAT',math(perp,'LESS_THAN',dominant,0),1.,-1.))
worlddir=vm(perp,'CROSS_PRODUCT',normal,u)
selfnode=node(perp,'GeometryNodeSelfObject');host=node(perp,'GeometryNodeObjectInfo','Host world transform');host.transform_space='ORIGINAL';link(perp,selfnode.outputs[0],host.inputs['Object'])
inverse=node(perp,'FunctionNodeInvertMatrix');link(perp,host.outputs['Transform'],inverse.inputs[0])
local=node(perp,'FunctionNodeTransformDirection');link(perp,worlddir,local.inputs['Direction']);link(perp,inverse.outputs[0],local.inputs['Transform'])
direction=scale(perp,vm(perp,'NORMALIZE',local.outputs[0]),switch(perp,'FLOAT',i.outputs['Reverse Direction'],1.,-1.))
tip=scale(perp,direction,i.outputs['Length'])
draw=node(perp,'GeometryNodeGroup','Draw with GP Arrow');draw.node_tree=arrow;draw.inputs['Use Positions'].default_value=True;draw.inputs['Start'].default_value=(0,0,0);link(perp,tip,draw.inputs['End'])
for name in styles:link(perp,i.outputs[name],draw.inputs[name])
geo=store(perp,draw.outputs['Arrow'],'gp_arrow_create_end','BOOLEAN',i.outputs['Create End Empty'])
link(perp,switch(perp,'GEOMETRY',valid,None,geo),o.inputs['Arrow']);link(perp,direction,o.inputs['Direction']);link(perp,valid,o.inputs['Valid Plane'])

intersection=group('GP Arrow • Segment Intersection','Find the first hit on Check Object between Start Object and End Object, including evaluated mesh modifiers. The GP Arrow Objects companion creates a real child Empty at the hit. No hit hides the managed Empty.')
sock(intersection,'Geometry','Geometry',out=True);sock(intersection,'Hit','Bool',out=True);sock(intersection,'Hit Point','Vector',out=True,desc='Intersection in host local coordinates.');sock(intersection,'Distance','Float',out=True,desc='Distance from Start in world units.')
for name in ['Start Object','End Object','Check Object']:sock(intersection,name,'Object')
i=node(intersection,'NodeGroupInput');o=node(intersection,'NodeGroupOutput')
infos=[]
for name in ['Start Object','End Object','Check Object']:
    n=node(intersection,'GeometryNodeObjectInfo',name);n.transform_space='ORIGINAL';link(intersection,i.outputs[name],n.inputs['Object']);infos.append(n)
start,end,check=infos
real=node(intersection,'GeometryNodeRealizeInstances');link(intersection,check.outputs['Geometry'],real.inputs[0])
world=node(intersection,'GeometryNodeTransform');world.inputs['Mode'].default_value='Matrix';link(intersection,real.outputs[0],world.inputs['Geometry']);link(intersection,check.outputs['Transform'],world.inputs['Transform'])
delta=vm(intersection,'SUBTRACT',end.outputs['Location'],start.outputs['Location'])
ray=node(intersection,'GeometryNodeRaycast','First hit limited to the segment');ray.data_type='FLOAT';link(intersection,world.outputs[0],ray.inputs['Target Geometry']);link(intersection,start.outputs['Location'],ray.inputs['Source Position']);link(intersection,vm(intersection,'NORMALIZE',delta),ray.inputs['Ray Direction']);link(intersection,vm(intersection,'LENGTH',delta),ray.inputs['Ray Length'])
selfnode=node(intersection,'GeometryNodeSelfObject');host=node(intersection,'GeometryNodeObjectInfo');host.transform_space='ORIGINAL';link(intersection,selfnode.outputs[0],host.inputs['Object'])
inv=node(intersection,'FunctionNodeInvertMatrix');link(intersection,host.outputs['Transform'],inv.inputs[0])
hit=node(intersection,'FunctionNodeTransformPoint');link(intersection,ray.outputs['Hit Position'],hit.inputs['Vector']);link(intersection,inv.outputs[0],hit.inputs['Transform'])
line=node(intersection,'GeometryNodeCurvePrimitiveLine','Invisible carrier for hit metadata');link(intersection,hit.outputs[0],line.inputs['Start']);link(intersection,hit.outputs[0],line.inputs['End'])
radius=node(intersection,'GeometryNodeSetCurveRadius');radius.inputs['Radius'].default_value=0;link(intersection,line.outputs[0],radius.inputs[0])
gp=node(intersection,'GeometryNodeCurvesToGreasePencil');gp.inputs['Instances as Layers'].default_value=False;link(intersection,radius.outputs[0],gp.inputs[0])
geo=store(intersection,gp.outputs[0],'gp_intersection_point','FLOAT_VECTOR',hit.outputs[0])
valid=math(intersection,'MULTIPLY',ray.outputs['Is Hit'],math(intersection,'GREATER_THAN',vm(intersection,'LENGTH',delta),.000001))
link(intersection,switch(intersection,'GEOMETRY',valid,None,geo),o.inputs['Geometry']);link(intersection,valid,o.inputs['Hit']);link(intersection,hit.outputs[0],o.inputs['Hit Point']);link(intersection,ray.outputs['Hit Distance'],o.inputs['Distance'])

# Lay out by dependency depth, keeping every node inspectable.
for g in [parallel,surface,perp]:g['gp_arrow_output_role']='endpoint'
proj['gp_arrow_output_role']='projected_endpoints'
intersection['gp_arrow_output_role']='intersection'
# Existing modifiers receive Blender's initial False for newly added bool sockets.
# Migrate once to preserve their previous automatic-empty behavior.
for g,names in [(proj,['Create Start Empty','Create End Empty']),(parallel,['Create End Empty']),(surface,['Create End Empty']),(perp,['Create End Empty'])]:
    if not g.get('gp_arrow_empty_options_version'):
        for obj in bpy.data.objects:
            for mod in obj.modifiers:
                if mod.type=='NODES' and mod.node_group==g:
                    for s in g.interface.items_tree:
                        if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name in names:
                            getattr(mod.properties.inputs,s.identifier).value=True
        g['gp_arrow_empty_options_version']=1
order=['Arrow','Start Position','End Position','Start Object','End Object','Thickness','Color','Opacity','Show Arrowhead','Head Length','Head Width','Show Label','Label','Label Size','Label Offset','Face Camera','Use Label Color','Label Color']
for index,name in enumerate(order):
    s=next((s for s in arrow.interface.items_tree if s.item_type=='SOCKET' and s.name==name),None)
    if s:arrow.interface.move(s,index)
for g in [arrow,proj,parallel,surface,perp,intersection]:
    depths={}
    def depth(n,seen=None):
        if n.name in depths:return depths[n.name]
        seen=set() if seen is None else seen
        if n.name in seen:return 0
        upstream=[l.from_node for s in n.inputs for l in s.links]
        d=1+max([depth(x,seen|{n.name}) for x in upstream],default=-1);depths[n.name]=d;return d
    rows={}
    for n in g.nodes:
        d=depth(n);row=rows.get(d,0);rows[d]=row+1;n.location=(d*250,-row*260)
    g.asset_mark();g.asset_data.description=g.description
    for tag in ['Grease Pencil','Arrow','Geometry Nodes']:g.asset_data.tags.new(tag)

preview_script=ROOT/'scripts'/'apply_asset_icons.py'
if preview_script.exists():
    preview_ns={'__file__':str(preview_script),'__name__':'__main__'}
    exec(compile(preview_script.read_text(encoding='utf-8'),str(preview_script),'exec'),preview_ns)
result={'groups':[g.name for g in [arrow,proj,parallel,surface,perp,intersection]],'nodes':[len(g.nodes) for g in [arrow,proj,parallel,surface,perp,intersection]]}
