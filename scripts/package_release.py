# SPDX-License-Identifier: GPL-3.0-or-later
"""Build local release archives; do not publish or upload anything."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist';DIST.mkdir(exist_ok=True)
with ZipFile(DIST/'gp_arrow_objects.zip','w',ZIP_DEFLATED) as archive:
    archive.write(ROOT/'scripts'/'gp_arrow_objects.py','gp_arrow_objects.py')
with ZipFile(DIST/'gp-arrows-0.1.0.zip','w',ZIP_DEFLATED) as archive:
    for relative in ['README.md','LICENSE.md','THIRD_PARTY_NOTICES.md','assets/gp_arrow_assets.blend','assets/blender_assets.cats.txt','examples/gp_arrows_demo.blend','docs/USAGE.md']:
        archive.write(ROOT/relative,relative)
    for folder in ['LICENSES','docs/images']:
        for file in sorted((ROOT/folder).rglob('*')):
            if file.is_file():archive.write(file,file.relative_to(ROOT))
    archive.write(DIST/'gp_arrow_objects.zip','gp_arrow_objects.zip')
print(f'Release archives written to {DIST}. Check THIRD_PARTY_NOTICES.md before public distribution.')
