# 1910 Shanghai Dialect TTS: Project Architecture & Plan

## 1. Project Background and Core Challenges

This research aims to build a speech synthesis system capable of accepting **1910 Romanization (Pott)** input and generating natural speech with historical pronunciation characteristics (**Sharp-Round distinction**, **Voiced obstruent retention**, **Checked tone abruptness**).

### 1.1 Loss of Historical Phonetic Features
According to F. L. Hawks Pott's *Lessons in the Shanghai Dialect* (1907) and Joseph Edkins' grammar works, 1910s Shanghai Dialect (Old-style Wu) possessed a more complex phonological structure than modern Shanghai dialect:

*   **Sharp-Round Distinction (尖团分明)**: Clear distinction between **ts** (Sharp/Gam) and **k** (Round/Tuan).
    *   Example: "酒" (tsiu) vs "九" (jiu/kyiu) are distinct.
    *   *Modern Status*: Completely merged.
*   **Voiced/Voiceless Contrast (浊音与清音的对立)**: Complete preservation of voiced initials (b, d, g, z, v, dz).
    *   *Note*: The distinction between **z** (fricative) and **dz** (affricate) was already merging but strictly marked in Pott's system. Physical isolation is required during modeling.
*   **Abrupt Entering Tone (入声短促)**: Syllables ending in glottal stop **-k** (or **ʔ**) are extremely short.
    *   *Modern TTS Issue*: Vocoders tend to smooth these out, making them sound like departing tones (去声) and losing the "checked" quality.

### 1.2 Technical Challenge: One-to-Many Mapping & Averaging
Traditional TTS models (e.g., FastSpeech 2) face the **"Averaging" problem** when restoring historical dialects without ground truth audio. Training solely on modern data causes the model to generate a "Modern Accent" (merged Sharp/Round, lack of historical prosody).

**Solution**: Adoption of **Probabilistic Sequence Modeling**.

---

## 2. Module 1: Historical Phoneme-aware Frontend

This is the cornerstone of restoration. We cannot use modern Pinyin or Wugniu Pinyin directly; a dedicated historical phonological mapping layer is required.

### 2.1 Pott-G2P Rule Engine (Based on *Shanghai Dialect Exercises*)
A dedicated G2P module will parse the 1910 Pott system directly.

*   **Romanization Parser**: Convert Pott (e.g., `Ngoo`, `vaung-tuh`) to a custom **"Extended Old Wu IPA Set"**.
*   **Sharp-Round Forced Separation**: 
    *   **Sharp (尖音)**: `ts`, `tsh`, `s` $\rightarrow$ Map to IPA **/ts/**, **/tsʰ/**, **/s/** (even before high front vowels).
    *   **Round (团音)**: `k` (ky), `kh` (ch), `h` (hy) $\rightarrow$ Map to IPA **/k/**, **/kʰ/**, **/h/** (or /c/, /cʰ/, /ç/).
*   **Strategy**: Even if modern training data lacks Sharp sounds, the frontend must output distinct **Phoneme IDs** to allow manipulation in the Embedding layer.

### 2.2 Disentangled Phoneme Embedding
Prevent the model from "learning" to merge Sharpe/Round sounds during modern data training.

*   **Physical Isolation**: Initialize "Sharp ID" and "Round ID" vectors to be orthogonal or have a large Euclidean distance.
*   **Contrastive Loss ($L_{contrast}$)**: Penalize convergence of Sharp/Round vectors during training, forcing the model to simplify input distinctions for later fine-tuning.

---

## 3. Module 2: Probabilistic Sequence Modeling

A generative architecture to solve "Prosody Averaging" and support few-shot learning of old-style features.

### 3.1 Core Architecture: Matcha-TTS (Flow Matching)
We select **Matcha-TTS** (based on Optimal Transport Conditional Flow Matching) over Diffusion models.

*   **Speed & Detail**: Generated trajectories are straighter, allowing high-frequency detail generation (crucial for **Glottal Stops**) in fewer steps (10-50).
*   **ODE Solver**: Stable mapping from noise to acoustic features, reducing "pronunciation collapse".

### 3.2 Stochastic Duration Predictor
To simulate natural speech rhythm and the specific "Drawl vs. Rush" (拖音 vs. 促音) contrast of Old Shanghai dialect.

*   **Mechanism**: Predict duration probability distributions rather than deterministic values.
*   **Effect**: Introduces micro-variations in speed and pauses (e.g., in "Ngoo tang-tsoh vaung-tuh"), avoiding a robotic "reading tone".

---

## 4. Module 3: Cross-Temporal Fine-tuning

"Faking" the accent via Transfer Learning due to lack of 1910 recordings.

### 4.1 Base Training
*   **Dataset**: Modern high-quality Wu corpora (Common Voice Shanghai / MagicData-RAMC), ~10-50 hours.
*   **Goal**: Learn basic Wu timbre, formant structure, and accumulation.

### 4.2 Few-Shot Adaptation (Style Transfer)
*   **Data**: ~15-30 mins of recording by linguists/Pingtan actors imitating Pott's pronunciation (focusing on Sharp/Voiced sounds).
*   **Strategy**:
    *   **Freeze Backend**: Freeze Decoder & Vocoder to preserve audio quality.
    *   **Fine-tune Frontend**: Update Text Encoder & Phoneme Embedding.
    *   **Force Alignment**: Force "Sharp ID" to map to recorded "Sharp features" (strong high-frequency friction).

---

## 5. Backend Vocoder Optimization: Checked Tones

### 5.1 Challenge
Standard vocoders (MelGAN) often produce metallic or blurry sounds for Checked Tones (入声), missing the glottal stop.

### 5.2 BigVGAN Application
*   **High-Frequency Reconstruction**: Better at reproducing the abrupt glottal stop (/ʔ/).
*   **Anti-aliasing**: Preserves the rich, muddy resonance details of voiced consonants (濁音).
