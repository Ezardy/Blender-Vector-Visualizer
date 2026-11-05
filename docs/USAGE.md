# Grease Pencil arrow assets

Created and checked in Blender 5.2.3 LTS.

The six node groups are marked as assets in `assets/gp_arrow_assets.blend`. Add the repository's `assets` directory as an Asset Library in Blender Preferences, or append the node groups from that file. A clean example scene is available at `examples/gp_arrows_demo.blend`; with that file open, choose **Current File** in the Asset Browser and search for **GP Arrow**.

## Real endpoint and intersection objects

The **GP Arrow Objects** companion add-on (`gp_arrow_objects.zip` in release bundles, source in `scripts/gp_arrow_objects.py`) creates actual child Empty objects for the Normal, Parallel, Perpendicular, and Projection arrows, and for Segment Intersection. Geometry Nodes alone cannot create Blender object datablocks. Keep the companion enabled to maintain these objects after editing, animation, or reopening Blender. The arrow geometry itself does not require the companion.

Managed child empties are named **Host • Start**, **Host • End**, or **Host • Intersection**, parented to the host, and follow its final evaluated output. Projection creates both Start and End at the projected endpoints on local XY, independent of label position. Normal, Parallel, and Perpendicular create End. They are usable in other object inputs. Each child exposes **GP Arrow Valid**. Invalid/degenerate outputs hide the child and mark it false while preserving its last valid transform. Do not feed a managed child back into the same host's calculations, which would create a dependency cycle.

Empty creation is optional: Projection provides independent **Create Start Empty** and **Create End Empty** switches. Normal, Parallel, and Perpendicular provide **Create End Empty**. They default on for compatibility with existing setups. Turning a switch off prevents new objects from being created; an existing managed child is hidden, marked invalid, and no longer follows the arrow, while remaining available to preserve object references. Enable the switch to resume tracking. Segment Intersection still produces its managed intersection object.

The add-on updates after scene edits (with a short debounce), on frame changes, and before saving. Its role tags survive duplicated node groups, and supported node assets embedded inside wrapper groups are detected. Disabling/removing the relevant modifier hides its managed output rather than deleting objects that may have other references.

## GP Arrow • Object to Object

Add this Geometry Nodes modifier to an empty **Grease Pencil** object, then set **Start Object** and **End Object**. The arrow follows their origins, including parenting and animation. Enable **Object Properties > Viewport Display > In Front** on the host object; the supplied examples already enable it.

**Thickness** is the full stroke diameter in host local units. Color, opacity, head length, and full head width are adjustable. The head is a 32-sided cone converted into filled Grease Pencil faces, so the complete arrow remains Grease Pencil and supports In Front. Head length is limited to 45% of the arrow length. Turn **Show Arrowhead** off for a line reaching the end object. Coincident endpoints produce empty geometry.

Enable **Show Label**, enter **Label**, and set its size and offset from the tip. **Face Camera** uses the active scene camera. Enable **Use Label Color** to choose an independent **Label Color**; otherwise the label follows the arrow color. The label uses a local copy of the same GP Text Nodes 5.2 asset as the existing axis labels, with the built-in font; it does not require that asset's external cache file.

## GP Arrow • Project onto Plane

Connect the first asset's **Arrow** output into this asset's **Arrow** input, or add it as the next modifier on the same Grease Pencil object.

The plane is automatically the **host object's local XY plane**, centered on the host object's origin: U is local X, V is local Y, and the plane origin is local (0, 0, 0). The shaft and endpoint positions have local Z zero; the cone retains its three-dimensional width. Move or rotate the host to position/orient the plane in the scene; parenting and scale are respected. There are no manual Plane U, Plane V, or Plane Origin inputs.

The shaft is projected onto local XY. The head remains a **three-dimensional cone** aligned with the projected shaft, preserving its circular base width and color. Head length is capped at 45% of the projected vector length, and the shaft ends at its cone base. The head can extend above and below the XY plane. An arrow normal to the plane has zero projected length and produces empty geometry. Labels have two modes, controlled by **Face Camera** on the arrow generator:

- **On:** move the label to the projected tip, retaining its camera-facing orientation and 3D offset. Its letters are not projected onto the plane.
- **Off:** place the label flat on host local XY, preserving letter shapes and size. Local X defines text right and local Y defines text up. Label Offset X/Y follow these axes; Z is ignored so the label lies in the plane.

These modes are carried through the Arrow geometry, so both direct node connections and stacked modifiers work. **Valid Plane** remains true for compatibility with existing node graphs because the local XY basis is fixed.

## GP Arrow • Parallel from Origin

Add this modifier **below GP Arrow • Object to Object on the same Grease Pencil object**, just like GP Projection. It receives the previous modifier's Arrow geometry automatically; no source object selector is needed. The order can also be **GP Arrow → GP Projection → Parallel from Origin**. Inside a node tree, connect an Arrow geometry output directly into its Arrow input.

The new arrow starts at the host's local **(0, 0, 0)**. **Reverse Direction** makes it point opposite to the source. **Length** sets the new arrow's length in host local units (default 1). Enable **Use Source Length** to preserve the source vector length instead. A rotated or scaled host still produces a vector parallel to the source in world space.

Thickness, colors, label, and whether the head is present come from the source. Length changes scale the arrow along its direction, including cone length, while preserving its transverse width. Labels move to the new tip without mirroring their text. Missing sources and zero-length vectors produce empty geometry. Endpoint metadata remains in the geometry so the result can be used by the other GP Arrow assets. Enable **In Front** on the host for overlay display.

## GP Arrow • Closest Surface Normal

Add this modifier to a Grease Pencil host and choose a mesh in **Surface Object**. It finds the closest surface point to the host origin in world space, samples that face's geometric normal, and draws an arrow **from the host origin** along the normal. Moving the host or target updates the result. Target modifiers are included, and rotated/nonuniformly scaled hosts and targets are supported. Normals follow the mesh face winding; **Reverse Direction** flips the arrow.

**Length** is in host local units. Thickness, color, opacity, cone/head visibility, and label controls match GP Arrow. The modifier draws through the GP Arrow node group, so its output supports GP Projection and Parallel from Origin. Enable **In Front** on the host for overlay display. A missing target or target without mesh faces produces empty geometry. Choose a different target object from the host to avoid a dependency cycle.

The group also exposes **Closest Point** and **Surface Normal** in host local coordinates, and **Distance** in world units, for use inside node graphs. The sampled point determines the direction; the visible arrow starts at the host rather than at that surface point.

## GP Arrow • Perpendicular in Plane

Set **Vector 1 Start**, **Vector 1 End**, **Vector 2 Start**, and **Vector 2 End** to four object references (references may share objects). Each vector is End minus Start, using world-space object origins. The modifier draws from the host origin, perpendicular to Vector 1, in the plane spanned by the two vector directions. The plane is translated through the host origin; the endpoint objects define its directions, not its location. Length and all GP Arrow style/label controls are available.

The first vector sets the directed orientation: reversing Vector 1 reverses the arrow. Vector 2 supplies the plane, so reversing Vector 2 alone leaves the arrow direction unchanged. The convention chooses a world-space unit plane normal whose largest absolute component is positive, then uses **normal cross Vector 1**. Thus, for the XY plane, +X produces +Y and +Y produces -X. **Reverse Direction** selects the opposite result. This fixed convention has an orientation seam where the dominant plane-normal component changes sign; use Reverse Direction to choose the desired side.

The calculation remains perpendicular in world space with rotated/nonuniformly scaled hosts. **Length** uses host local units. All four object inputs must be assigned. Zero-length or parallel spanning vectors produce empty geometry; the group exposes **Valid Plane** and the host-local **Direction**. Outputs are compatible with the GP Projection and Parallel from Origin modifiers.

## GP Arrow • Segment Intersection

Add this modifier to a Grease Pencil host and assign **Start Object**, **End Object**, and **Check Object** (an evaluated mesh). It finds the **first surface hit between Start and End**, along the Start-to-End direction. It does not extend past End. The GP Arrow Objects companion creates **Host • Intersection** at that hit. The node geometry is an invisible GP carrier for the result, not a visible arrow.

The node group also outputs **Hit**, **Hit Point** (host local), and **Distance** (world units from Start). Missing/empty targets, zero-length segments, and no intersections produce no point; the child is hidden and marked invalid. All calculations use world space before converting to the host, so transformed targets and hosts are supported.

The **GP Arrow Examples** collection contains the original arrow examples, a surface-normal example targeting Obstacle, **GP Perpendicular Arrow Example** with four dedicated endpoint empties, and **GP Segment Intersection Example** with two segment endpoint empties targeting Obstacle. Existing scene objects are retained.

Verified: cone tip alignment, filled cone output, independent label color, headless line reaching the end object, camera-facing label orientation, and labels lying on the host XY plane without distortion. A translated, rotated, nonuniformly scaled host verifies that the plane follows the host origin and axes. Plane/label placement and shape errors were below 0.000001. The earlier version also verified moving endpoints, zero-length arrows, and stroke radius/color.

Parallel-arrow checks cover the same-object modifier stack, host-origin anchoring, custom and source lengths, both directions, rotated/nonuniformly scaled hosts, unmirrored labels, projection before the parallel modifier, empty geometry inputs, and zero lengths.

Surface-normal checks compare the sampled point and normal against an independently built BVH of the evaluated world-space target mesh, with both target and host rotated and nonuniformly scaled. They also verify target modifiers, host movement, length, reverse direction, origin anchoring, and missing targets. Point/normal errors were below 0.000001.

Perpendicular-arrow checks verify world-space perpendicularity and plane membership, nonorthogonal spanning vectors, nonuniform host transforms, both vector-reversal behaviors, Reverse Direction, host origin/length, and degenerate inputs. Dot-product errors were below 0.000001.

Real-object checks verify endpoint placement, parenting, length updates, transformed segment intersections, rejection of hits beyond End, zero-length segments, and hiding/reappearing intersection objects. Intersection position error was below 0.000001.
