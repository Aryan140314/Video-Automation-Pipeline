import sys, traceback
try:
    print("Testing import f5_tts.model.modules with full exception logging...", flush=True)
    import f5_tts.model.modules
    print("modules imported ok!", flush=True)
except Exception:
    traceback.print_exc()
except BaseException as be:
    print("Caught base exception:", repr(be), flush=True)
    traceback.print_exc()
