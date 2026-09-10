import py_compile, sys
try:
    print("Compiling modules.py...", flush=True)
    py_compile.compile(r"E:\TTS\.venv\Lib\site-packages\f5_tts\model\modules.py", doraise=True)
    print("Compilation ok!", flush=True)
except Exception as e:
    print("Compile error:", e, flush=True)
