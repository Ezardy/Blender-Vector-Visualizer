# GP Arrows for Blender

Seven reusable Grease Pencil Geometry Nodes assets for arrows, angle arcs, projections, surface normals, and segment intersections. The Angle Arc is tested with **Blender 5.3.0**; the earlier assets were originally checked with Blender 5.2.3 LTS.

| Asset | Preview | Purpose |
|---|---|---|
| Object to Object | ![Arrow](docs/images/icons/object-to-object.png) | Arrow between two object origins |
| Project onto Plane | ![Projection](docs/images/icons/projection.png) | Projection onto the host's local XY plane |
| Parallel from Origin | ![Parallel](docs/images/icons/parallel.png) | Same/opposite direction from the host origin |
| Closest Surface Normal | ![Normal](docs/images/icons/surface-normal.png) | Normal at the closest surface point |
| Perpendicular in Plane | ![Perpendicular](docs/images/icons/perpendicular.png) | Perpendicular to one vector in a two-vector plane |
| Segment Intersection | ![Intersection](docs/images/icons/segment-intersection.png) | First mesh intersection between two objects |
| Angle Arc | ![Angle arc](docs/images/icons/angle-arc.png) | Directed arc between coplanar vectors; square right-angle marker |

## Installation

1. Download a release bundle, or clone this repository with Git LFS installed (`git lfs pull`).
2. In Blender Preferences → File Paths → Asset Libraries, add the repository's **assets** directory.
3. Install **gp_arrow_objects.zip** from the release using Preferences → Add-ons → Install from Disk, then enable **GP Arrow Objects**. This companion creates and updates the real child Empty objects.
4. Add an asset as a modifier to a Grease Pencil object. Enable the host object's **In Front** option to display arrows over scene geometry.

The arrow geometry works without the companion; managed Start/End/Intersection objects require it. Length, thickness, color, conical heads, optional labels, and camera-facing label controls are provided where applicable.

The companion updates managed empties from Blender's main-loop timer (about 0.1 seconds after a change). Frame changes schedule an update instead of changing object visibility during dependency-graph evaluation. Camera-facing labels compensate for parent and host rotation and scale.

Projected arrows retain 3D cone heads on their XY-projected shafts. Projection has independent **Create Start Empty** / **Create End Empty** switches; Normal, Parallel, and Perpendicular also have **Create End Empty** controls.

Enable **Show Label → Vector Sign** to add a fitted right-pointing vector arrow above the label. It follows label size, color, opacity, and camera-facing/planar orientation. Object to Object, Surface Normal, Perpendicular, and Angle Arc expose the switch; Projection and Parallel inherit the source label's setting.

See [the full asset guide](docs/USAGE.md). Open [the clean demo](examples/gp_arrows_demo.blend) for working examples of all seven assets. The original personal working scene is excluded from Git.

## Repository layout

```text
assets/gp_arrow_assets.blend   Node assets with embedded previews
scripts/gp_arrow_objects.py    Companion add-on source
scripts/                      Asset, icon, demo, and release builders
tests/                        Blender validation scripts
examples/gp_arrows_demo.blend  Clean, self-contained demo scene
docs/USAGE.md                 Full usage guide
docs/images/icons/            Editable SVGs and generated PNG previews
LICENSES/                    License texts
THIRD_PARTY_NOTICES.md         Bundled label dependency and release status
```

## Development

PNG/JPEG/WebP and other raster image formats, plus `.blend` files, use Git LFS. SVG sources stay as regular Git text files. Run `git lfs install --local` after cloning if needed.

```powershell
python scripts/generate_icons.py
blender --background --factory-startup --python scripts/build_demo.py
blender --background examples/gp_arrows_demo.blend --python tests/run_checks.py
python scripts/package_release.py
```

To rebuild the node assets, run `scripts/build_arrow_assets.py` in Blender with the existing asset library open, then run `scripts/export_assets.py`. The builder reuses the bundled label group, so it does not require the original downloaded text asset. The scripts resolve paths from this repository. The release script writes the companion add-on ZIP and a complete download bundle under ignored `dist/`.

## Licensing and credits

Original node setups and icons: **CC0-1.0**. Python source: **GPL-3.0-or-later**. See [LICENSE.md](LICENSE.md).

**Before public distribution, resolve the bundled GP Text Nodes label asset's redistribution license.** Its metadata credits Johnny Matthews but contains no license. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The licenses above do not override third-party terms.
