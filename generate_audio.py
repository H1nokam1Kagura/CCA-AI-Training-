#!/usr/bin/env python3
"""
generate_audio.py — CCA Podcast Audio Generator
Imports LESSONS from generate_podcasts_v2.py and renders MP3s via OpenAI TTS-HD.

Usage:
    python generate_audio.py                    # all 16 episodes
    python generate_audio.py --ep 1 3 5         # specific episodes
    python generate_audio.py --dry-run          # preview without API calls
    python generate_audio.py --ep 1 --overwrite # re-generate existing

Cost note: tts-1-hd ≈ $0.030 per 1K chars. Full series ≈ 180K chars ≈ $5.40.
"""

import os
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Generate CCA podcast MP3s via OpenAI TTS-HD"
    )
    parser.add_argument(
        "--ep", nargs="+", type=int, metavar="N",
        help="Episode numbers to generate (default: all)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be generated without calling the API"
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Re-generate episodes that already exist"
    )
    parser.add_argument(
        "--out", default=".", metavar="DIR",
        help="Output directory for MP3 files (default: current directory)"
    )
    parser.add_argument(
        "--model", default="tts-1-hd", choices=["tts-1", "tts-1-hd"],
        help="TTS model: tts-1 (faster/cheaper) or tts-1-hd (default)"
    )
    args = parser.parse_args()

    # Load content
    try:
        from generate_podcasts_v2 import LESSONS
    except ImportError:
        print("ERROR: generate_podcasts_v2.py not found in current directory.")
        sys.exit(1)

    # Filter episodes
    episodes = LESSONS
    if args.ep:
        ep_set = set(args.ep)
        episodes = [ep for ep in LESSONS if ep["num"] in ep_set]
        missing = ep_set - {ep["num"] for ep in episodes}
        if missing:
            print(f"WARNING: Episodes not found: {sorted(missing)}")
        if not episodes:
            print("No matching episodes. Available: 1–16")
            sys.exit(1)

    # Resolve output dir
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build file mapping: ep.num → expected filename (matches index.html EPISODES array)
    FILE_NAMES = {
        1:  "Lesson_01_Why_People_Fail_the_CCA_Exam.mp3",
        2:  "Lesson_02_Agentic_Error_Handling.mp3",
        3:  "Lesson_03_Two_Critical_Failure_Modes.mp3",
        4:  "Lesson_04_MCP_Manifest_and_RPC_Enforcement.mp3",
        5:  "Lesson_05_Claude_MD_as_Control_Layer.mp3",
        6:  "Lesson_06_Claude_MD_and_Skill_MD_Policy_vs_Behavior.mp3",
        7:  "Lesson_07_Hub_and_Spoke_Agent_Architecture.mp3",
        8:  "Lesson_08_Multi_Agent_Failure_Modes.mp3",
        9:  "Lesson_09_Goal_Decomposition_in_the_Hub.mp3",
        10: "Lesson_10_Memory_Caching_and_State_Management.mp3",
        11: "Lesson_11_Managing_the_Context_Window.mp3",
        12: "Lesson_12_Determinism_Without_Schema.mp3",
        13: "Lesson_13_From_Text_to_Structure_Defining_Elements.mp3",
        14: "Lesson_14_Predicting_Goals_and_Defining_Elements.mp3",
        15: "Lesson_15_Designing_Task_Schemas.mp3",
        16: "Lesson_16_Validating_Unstructured_Outputs.mp3",
    }

    # Estimate cost
    total_chars = sum(len(ep["text"]) for ep in episodes)
    est_cost    = (total_chars / 1000) * (0.030 if args.model == "tts-1-hd" else 0.015)

    print(f"\nCCA Podcast Audio Generator")
    print(f"  Model   : {args.model}")
    print(f"  Episodes: {len(episodes)}")
    print(f"  Chars   : {total_chars:,}")
    print(f"  Est cost: ${est_cost:.2f}")
    print(f"  Output  : {out_dir}")
    print()

    if args.dry_run:
        print("DRY RUN — no API calls\n")
        for ep in episodes:
            fname = FILE_NAMES.get(ep["num"], f"Lesson_{ep['num']:02d}_{ep['slug']}.mp3")
            fpath = out_dir / fname
            exists = "EXISTS" if fpath.exists() else "NEW"
            print(f"  [{exists:6s}] ep{ep['num']:02d}  {ep['voice']:7s}  {ep['speed']}x  {len(ep['text']):,} chars  →  {fname}")
        return

    # API setup
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Try loading from .env in script directory
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("OPENAI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not api_key:
        print("ERROR: OPENAI_API_KEY not set.")
        print("  Option 1: set environment variable OPENAI_API_KEY=sk-...")
        print("  Option 2: create a .env file in the project root:  OPENAI_API_KEY=sk-...")
        sys.exit(1)

    try:
        from openai import OpenAI, RateLimitError, APIError, APIConnectionError
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai")
        sys.exit(1)

    import time

    client    = OpenAI(api_key=api_key)
    skipped   = 0
    generated = 0
    errors    = []

    def split_text(text, limit=4000):
        """Split text into chunks ≤ limit chars, breaking only at sentence boundaries."""
        if len(text) <= limit:
            return [text]
        chunks  = []
        current = ""
        for para in text.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            candidate = (current + "\n\n" + para).strip() if current else para
            if len(candidate) <= limit:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                    current = ""
                sentences = para.replace(". ", ".|").split("|")
                for sent in sentences:
                    candidate = (current + " " + sent).strip() if current else sent
                    if len(candidate) <= limit:
                        current = candidate
                    else:
                        if current:
                            chunks.append(current)
                        # Hard fallback: force-split oversized sentence at limit
                        while len(sent) > limit:
                            chunks.append(sent[:limit])
                            sent = sent[limit:]
                        current = sent
        if current:
            chunks.append(current)
        return chunks

    def concat_mp3_bytes(parts):
        """Concatenate raw MP3 byte strings — valid for CBR/VBR without re-encoding."""
        return b"".join(parts)

    def tts_with_retry(client, model, voice, input_text, speed, retries=4):
        """Call TTS API with exponential backoff on rate limit errors."""
        delay = 5
        for attempt in range(retries):
            try:
                return client.audio.speech.create(
                    model=model,
                    voice=voice,
                    input=input_text,
                    speed=speed,
                )
            except RateLimitError:
                if attempt < retries - 1:
                    print(f"\n    rate limited — waiting {delay}s...", end="", flush=True)
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise
            except APIConnectionError as e:
                if attempt < retries - 1:
                    print(f"\n    connection error — retrying in {delay}s...", end="", flush=True)
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise

    for ep in episodes:
        fname = FILE_NAMES.get(ep["num"], f"Lesson_{ep['num']:02d}_{ep['slug']}.mp3")
        fpath = out_dir / fname

        if fpath.exists() and not args.overwrite:
            print(f"  SKIP  ep{ep['num']:02d} — {fname} (use --overwrite to regenerate)")
            skipped += 1
            continue

        chunks = split_text(ep["text"])
        label  = f"ep{ep['num']:02d} — {ep['title']} ({ep['voice']}, {ep['speed']}x)"
        if len(chunks) > 1:
            print(f"  GEN   {label}  [{len(chunks)} chunks]...", end="", flush=True)
        else:
            print(f"  GEN   {label}...", end="", flush=True)

        try:
            audio_parts = []
            for chunk in chunks:
                response = tts_with_retry(
                    client, args.model, ep["voice"], chunk, ep["speed"]
                )
                audio_parts.append(response.content)

            mp3_bytes = concat_mp3_bytes(audio_parts)
            fpath.write_bytes(mp3_bytes)
            size_kb = fpath.stat().st_size // 1024
            print(f" ✓ {size_kb}KB")
            generated += 1
        except (RateLimitError, APIError, APIConnectionError, OSError) as e:
            print(f" ✗ ERROR: {e}")
            errors.append((ep["num"], str(e)))
            # Fix 1: remove partial file so next run doesn't skip a broken episode
            if fpath.exists():
                try:
                    fpath.unlink()
                    print(f"    (partial file removed — re-run to retry)")
                except OSError:
                    print(f"    (could not remove partial file: {fpath})")

    print(f"\nDone.  Generated: {generated}  Skipped: {skipped}  Errors: {len(errors)}")
    if errors:
        for num, msg in errors:
            print(f"  ep{num:02d}: {msg}")
    if generated > 0:
        print(f"\nMP3 files are in: {out_dir}")
        print("Open index.html in a browser (via local server) to use the player.")


if __name__ == "__main__":
    main()
