import faulthandler
faulthandler.enable()

import sys
print("Python executable:", sys.executable, flush=True)

try:
    print("Testing import f5_tts...", flush=True)
    import f5_tts
    print("f5_tts imported ok", flush=True)
    
    print("Testing import f5_tts.model.modules...", flush=True)
    import f5_tts.model.modules
    print("f5_tts.model.modules imported ok", flush=True)
    
except Exception as e:
    import traceback
    traceback.print_exc()
