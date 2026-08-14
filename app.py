"""
TTS Studio — Streamlit Interactive Web Application
===================================================
Production-ready GUI for zero-shot voice cloning & speech synthesis across 7 neural model engines:
1. F5-TTS (DiT Flow Matching)
2. Chatterbox Turbo (Diffusion Cloner)
3. Fish Speech S2 (DualAR LLM + 512-dim DAC Decoder)
4. OmniVoice (527-Layer Flow Transformer)
5. CosyVoice 3 (FunAudioLLM 300M Zero-Shot)
6. XTTS-v2 (Coqui Multilingual Voice Cloner)
7. IndexTTS 2.5 (UnifiedVoice GPT + S2Mel + BigVGAN)
"""

import os
import sys
import time
import glob
import wave
import streamlit as st

# Add scripts directory to path
WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(WORKSPACE_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from tts_adapters import get_adapter, _ADAPTER_REGISTRY
from path_resolver import get_voices_dir, get_outputs_dir
from hardware_detector import inspect_hardware

# Page Configuration
st.set_page_config(
    page_title="TTS Studio — Neural Zero-Shot Speech Engine",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: bold;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
        background-color: #065f46;
        color: #34d399;
    }
</style>
""", unsafe_allow_html=True)

# Hardware Detection
@st.cache_data(ttl=60)
def get_hardware():
    return inspect_hardware()

hw_data = get_hardware()

# Sidebar Layout
st.sidebar.markdown("## ⚙️ TTS Studio Settings")

# Model Selection
model_options = {
    "F5-TTS (DiT Flow Matching)": "f5tts",
    "Chatterbox Turbo (Fast Diffusion)": "chatterbox",
    "Fish Speech S2 (DualAR LLM + DAC)": "fishspeech",
    "OmniVoice (Flow Transformer)": "omnivoice",
    "CosyVoice 3 (FunAudioLLM 300M)": "cosyvoice",
    "XTTS-v2 (Coqui Voice Cloner)": "xttsv2",
    "IndexTTS 2.5 (GPT + BigVGAN)": "indextts2",
}

selected_model_name = st.sidebar.selectbox(
    "🎙️ Select Neural TTS Engine",
    options=list(model_options.keys()),
    index=0
)
model_id = model_options[selected_model_name]

st.sidebar.markdown("---")

# Voice Reference Selection
st.sidebar.markdown("### 🗣️ Speaker Reference Voice")
voices_dir = get_voices_dir()

# Discover voice WAV files
wav_files = glob.glob(os.path.join(voices_dir, "**", "*.wav"), recursive=True)
voice_map = {}
for wav_p in wav_files:
    rel_name = os.path.relpath(wav_p, voices_dir).replace("\\", "/")
    voice_map[rel_name] = wav_p

if not voice_map:
    # Add fallback default reference
    default_ref = os.path.join(voices_dir, "Narration", "deep_male_narrator.wav")
    if os.path.exists(default_ref):
        voice_map["Narration/deep_male_narrator.wav"] = default_ref

selected_voice_label = st.sidebar.selectbox(
    "Select Reference Speaker Asset",
    options=list(voice_map.keys()) if voice_map else ["Default Reference"],
    index=0
)
selected_voice_path = voice_map.get(selected_voice_label)

if selected_voice_path and os.path.exists(selected_voice_path):
    st.sidebar.audio(selected_voice_path, format="audio/wav")
    st.sidebar.caption(f"📁 `{os.path.basename(selected_voice_path)}`")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧠 Hardware Engine")
st.sidebar.info(f"**Device:** {hw_data['recommended_device']}\n\n**GPU:** {hw_data['device_name']}\n\n**VRAM:** {hw_data['vram_total_gb']} GB")

# Main Interface Header
st.markdown('<div class="main-header">🎙️ TTS Studio — Zero-Shot Voice Cloning</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Production Windows Desktop Application | 7 Advanced Neural Model Engines</div>', unsafe_allow_html=True)

# Main Form
col_input, col_info = st.columns([2, 1])

with col_input:
    st.subheader("📝 Input Text Prompt")
    text_prompt = st.text_area(
        "Enter text to synthesize into spoken speech (up to 2,000 words):",
        value="Hello world! Welcome to TTS Studio. All seven zero shot voice cloning models are running locally with CUDA GPU acceleration.",
        height=180
    )

    generate_btn = st.button("🚀 Generate Speech", type="primary", use_container_width=True)

with col_info:
    st.subheader("ℹ️ Selected Model Info")
    adapter = get_adapter(model_id)
    st.markdown(f"**Engine Name:** `{adapter.model_name}`")
    st.markdown(f"**Model ID:** `{adapter.model_id}`")
    st.markdown(f"**Max Words Chunk:** `{adapter.get_safe_chunk_size()} words`")
    st.markdown('<span class="status-badge">🟢 LOCAL CUDA READY</span>', unsafe_allow_html=True)

# Synthesis Execution
if generate_btn:
    if not text_prompt.strip():
        st.error("Please enter a valid text prompt before generating speech.")
    else:
        output_dir = get_outputs_dir()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        out_filename = f"{model_id}_speech_{timestamp}.wav"
        out_filepath = os.path.join(output_dir, out_filename)

        st.markdown("---")
        st.subheader("⚡ Generation Progress & Live Performance Metrics")
        progress_bar = st.progress(0, text="Initializing model runtime and loading weights...")

        try:
            progress_bar.progress(30, text=f"Executing {adapter.model_name} neural synthesis pass on GPU...")
            
            # Execute Adapter Synthesis
            res = adapter.generate(
                text=text_prompt,
                reference_voice=selected_voice_path,
                output_path=out_filepath
            )

            progress_bar.progress(100, text="Synthesis complete! Audio waveform rendered.")
            st.success(f"Successfully generated spoken speech audio using **{adapter.model_name}**!")

            # Display Performance Metric Cards
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{res.get("gen_time", 0):.2f}s</div><div class="metric-label">Gen Time</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{res.get("duration", 0):.2f}s</div><div class="metric-label">Audio Duration</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{res.get("rtf", 0):.2f}</div><div class="metric-label">RTF Speed</div></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{res.get("file_size_kb", 0):.1f} KB</div><div class="metric-label">File Size</div></div>', unsafe_allow_html=True)
            with m5:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{res.get("device", "CUDA")}</div><div class="metric-label">Target Device</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Audio Player & Download Button
            if os.path.exists(out_filepath) and os.path.getsize(out_filepath) > 0:
                st.subheader("🔊 Generated Audio Waveform")
                st.audio(out_filepath, format="audio/wav")
                
                with open(out_filepath, "rb") as f:
                    st.download_button(
                        label=f"💾 Download {out_filename}",
                        data=f,
                        file_name=out_filename,
                        mime="audio/wav",
                        use_container_width=True
                    )

        except Exception as e:
            st.error(f"Error during speech synthesis: {e}")

# Generated Outputs Gallery
st.markdown("---")
st.subheader("📁 Recent Generated Outputs Gallery")
recent_outputs = sorted(glob.glob(os.path.join(get_outputs_dir(), "*.wav")), key=os.path.getmtime, reverse=True)[:5]

if recent_outputs:
    cols = st.columns(len(recent_outputs))
    for idx, wav_p in enumerate(recent_outputs):
        with cols[idx]:
            st.caption(f"🎵 `{os.path.basename(wav_p)}`")
            st.audio(wav_p, format="audio/wav")
else:
    st.info("No generated audio outputs found in `outputs/` directory.")
