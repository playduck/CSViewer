# -*- mode: python -*-

from pathlib import Path
import os
import sys
import importlib

# add qtmodern qss files
package_imports = [['qtmodern', ['resources/frameless.qss', 'resources/style.qss']]]
added_file = []
for package, files in package_imports:
    proot = Path(importlib.import_module(package).__file__).parent
    added_file.extend((proot / f, package) for f in files)

# add custom qss
added_file.extend([(
    Path(os.path.abspath("./style.qss")),
    "user"
)])

# add icons
assets = "assets"
icon_files = [f for f in os.listdir(assets) if os.path.isfile(os.path.join(assets, f))]
for icon_file in icon_files:
    added_file.extend([(
        Path(os.path.abspath(os.path.join(assets, icon_file) )),
        assets
    )])

print(added_file)

block_cipher = None

print(os.path.abspath(os.path.join(assets, "icon-512.icns")))


a = Analysis(['CSViewer.py'],
             pathex=['/Users/robin/PycharmProjects/CSViewer'],
             binaries=[],
             datas=added_file,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

if sys.platform == "darwin":
    exe = EXE(pyz,
                a.scripts,
                a.binaries,
                a.zipfiles,
                a.datas,
                name="CSViewer",
                debug=False,
                bootloader_ignore_signals=False,
                strip=False,
                upx=True,
                runtime_tmpdir=None,
                console=True,
                icon=os.path.abspath(os.path.join(assets, "icon-512.icns"))
    )
else:
    exe = EXE(pyz,
            a.scripts,
            a.binaries,
            a.zipfiles,
            a.datas,
            [],
            name='CSViewer',
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            runtime_tmpdir=None,
            console=True,
            icon=os.path.abspath(os.path.join(assets, "icon-512.ico"))
    )

# Package the executable file into .app if on OS X
if sys.platform == "darwin":
    app = BUNDLE(exe,
                    name="CSViewer.app",
                    info_plist={
                        "NSHighResolutionCapable": "True",
                        "LSBackgroundOnly": "False",
                        "NSRequiresAquaSystemAppearance": "True"
                        # should be false to support dark mode
                        # known bug: https://github.com/pyinstaller/pyinstaller/issues/4615 with Qt
                    },
                    icon=os.path.abspath(os.path.join(assets, "icon-512.icns"))
                    )
