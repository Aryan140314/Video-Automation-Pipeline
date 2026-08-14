# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

workspace_root = os.path.abspath(SPECPATH)

added_datas = [
    (os.path.join(workspace_root, 'voices'), 'voices'),
    (os.path.join(workspace_root, 'configs'), 'configs'),
    (os.path.join(workspace_root, 'scripts'), 'scripts'),
]

hidden_imports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'engineio.async_drivers.asgi',
    'fastapi',
    'pydantic',
    'pydantic_settings',
    'torch',
    'torchaudio',
    'soundfile',
    'librosa',
    'scipy',
    'numpy',
    'pydub',
    'imageio_ffmpeg',
    'gtts',
    'win32com',
    'pythoncom',
    'psutil',
    'requests',
    'httpx',
    'tqdm',
    'rich',
    'pyyaml',
    'f5_tts',
    'chatterbox',
]

a = Analysis(
    [os.path.join(workspace_root, 'backend', 'main.py')],
    pathex=[workspace_root, os.path.join(workspace_root, 'scripts')],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'notebook',
        'IPython',
        'PIL',
        'datasets',
        'diffusers',
        'pyarrow',
        'pandas',
        'sklearn',
        'f5_tts.model.dataset',
        'f5_tts.model.trainer',
        'gradio',
        'transformers',
        'torch.testing',
        'torch.distributed',
        'torch.export',
        'torch.fx',
        'torchdiffeq',
        'vocos',
        'hydra',
        'encodec',
        'pypinyin',
        'cached_path',
        'wandb',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='tts_studio_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='backend_dist',
)
