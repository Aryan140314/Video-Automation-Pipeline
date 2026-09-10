import os, sys

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

print("Testing transformers pipeline import...", flush=True)
import transformers
print("transformers imported version:", transformers.__version__, flush=True)
from transformers import pipeline
print("pipeline imported successfully!", flush=True)
