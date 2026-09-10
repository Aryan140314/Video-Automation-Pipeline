import sys, traceback
try:
    print("Testing rjieba...", flush=True)
    import rjieba
    print("rjieba imported ok!", flush=True)
except Exception:
    traceback.print_exc()
