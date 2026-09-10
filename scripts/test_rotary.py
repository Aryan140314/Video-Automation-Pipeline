import sys, traceback
try:
    print("Testing apply_rotary_pos_emb...", flush=True)
    from x_transformers.x_transformers import apply_rotary_pos_emb
    print("apply_rotary_pos_emb imported ok!", flush=True)
except Exception:
    traceback.print_exc()
