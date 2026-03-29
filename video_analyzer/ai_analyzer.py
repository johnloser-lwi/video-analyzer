"""AI-based video content analysis using Ollama with a vision model."""

import base64
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional

try:
    import ollama
    HAS_OLLAMA_PKG = True
except ImportError:
    HAS_OLLAMA_PKG = False


IMAGE_ANALYSIS_PROMPT = """Analyze this image carefully and describe what you see.
Provide your response in the following JSON format (and nothing else):

{
    "scene_description": "A detailed description of what is shown in this image",
    "key_objects": "List of key objects, people, or animals visible",
    "actions": "Any actions or activities taking place (or 'none' for still scenes)",
    "setting": "The environment or location (indoor/outdoor, type of place)",
    "screen_text": "Any visible text, titles, or captions (or 'none' if no text)",
    "content_summary": "A concise 1-2 sentence summary of the image"
}

Respond ONLY with valid JSON, no extra text."""

# Default vision model
DEFAULT_MODEL = "llava"

# Number of keyframes to extract for analysis
NUM_KEYFRAMES = 6

# Prompt for the vision model
ANALYSIS_PROMPT = """Analyze this video frame carefully and describe what you see.
Provide your response in the following JSON format (and nothing else):

{
    "scene_description": "A detailed description of what is happening in this frame",
    "key_objects": "List of key objects, people, or animals visible",
    "actions": "Any actions or activities taking place",
    "setting": "The environment or location (indoor/outdoor, type of place)",
    "screen_text": "Any visible text, titles, or captions (or 'none' if no text)"
}

Respond ONLY with valid JSON, no extra text."""

SUMMARY_PROMPT = """Below are descriptions of {n} frames extracted from a single video file named "{filename}".
Combine them into one cohesive summary of the entire video.

Frame descriptions:
{descriptions}

Provide your response in the following JSON format (and nothing else):

{{
    "scene_description": "A detailed description of what happens throughout the video",
    "key_objects": "All key objects, people, or animals observed across the video",
    "actions": "All actions or activities that take place",
    "setting": "The environment or location(s) shown",
    "screen_text": "Any visible text, titles, or captions observed (or 'none')",
    "content_summary": "A concise 1-2 sentence summary of the video content"
}}

Respond ONLY with valid JSON, no extra text."""


def check_ollama() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        if HAS_OLLAMA_PKG:
            ollama.list()
            return True
        else:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
    except Exception:
        return False


def check_vision_model(model: str = DEFAULT_MODEL) -> bool:
    """Check if the specified vision model is available in Ollama."""
    try:
        if HAS_OLLAMA_PKG:
            models = ollama.list()
            model_names = [m.model for m in models.models]
            return any(model in name for name in model_names)
        else:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10,
            )
            return model in result.stdout
    except Exception:
        return False


def extract_keyframes(video_path: Path, num_frames: int = NUM_KEYFRAMES) -> list[Path]:
    """
    Extract evenly-spaced keyframes from a video file using FFmpeg.

    Returns a list of paths to the extracted frame images.
    """
    temp_dir = tempfile.mkdtemp(prefix="video_analyzer_")
    frame_paths = []

    try:
        # Get video duration first
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(video_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        duration = float(result.stdout.strip())

        if duration <= 0:
            return []

        # Calculate timestamps for evenly-spaced frames
        # Skip first and last 5% to avoid black frames
        start = duration * 0.05
        end = duration * 0.95
        interval = (end - start) / max(num_frames - 1, 1)

        for i in range(num_frames):
            timestamp = start + (i * interval)
            output_path = Path(temp_dir) / f"frame_{i:03d}.jpg"

            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", str(timestamp),
                    "-i", str(video_path),
                    "-vframes", "1",
                    "-q:v", "2",
                    str(output_path),
                ],
                capture_output=True, text=True, timeout=30,
            )

            if output_path.exists() and output_path.stat().st_size > 0:
                frame_paths.append(output_path)

    except Exception:
        pass

    return frame_paths


def analyze_frame(frame_path: Path, model: str = DEFAULT_MODEL) -> Dict:
    """Analyze a single frame image using the Ollama vision model."""
    try:
        if HAS_OLLAMA_PKG:
            response = ollama.chat(
                model=model,
                messages=[{
                    "role": "user",
                    "content": ANALYSIS_PROMPT,
                    "images": [str(frame_path)],
                }],
            )
            response_text = response.message.content
        else:
            # Fallback: use ollama CLI via subprocess
            with open(frame_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()

            # Use the REST API directly
            import urllib.request
            payload = json.dumps({
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": ANALYSIS_PROMPT,
                    "images": [img_b64],
                }],
                "stream": False,
            })
            req = urllib.request.Request(
                "http://localhost:11434/api/chat",
                data=payload.encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
                response_text = result.get("message", {}).get("content", "")

        # Parse JSON from response
        return _parse_json_response(response_text)

    except Exception as e:
        return {"error": str(e)}


def summarize_descriptions(
    frame_descriptions: list[Dict],
    filename: str,
    model: str = DEFAULT_MODEL,
) -> Dict:
    """Combine multiple frame descriptions into a single video summary."""
    # Format frame descriptions for the prompt
    desc_text = ""
    for i, desc in enumerate(frame_descriptions):
        if "error" not in desc:
            desc_text += f"\nFrame {i + 1}:\n{json.dumps(desc, indent=2)}\n"

    if not desc_text.strip():
        return {
            "scene_description": "Unable to analyze video content",
            "key_objects": "",
            "actions": "",
            "setting": "",
            "screen_text": "",
            "content_summary": "Analysis failed — no frames could be processed",
        }

    prompt = SUMMARY_PROMPT.format(
        n=len(frame_descriptions),
        filename=filename,
        descriptions=desc_text,
    )

    try:
        if HAS_OLLAMA_PKG:
            response = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.message.content
        else:
            import urllib.request
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            })
            req = urllib.request.Request(
                "http://localhost:11434/api/chat",
                data=payload.encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read().decode())
                response_text = result.get("message", {}).get("content", "")

        return _parse_json_response(response_text)

    except Exception as e:
        return {
            "scene_description": f"Error during summarization: {e}",
            "key_objects": "",
            "actions": "",
            "setting": "",
            "screen_text": "",
            "content_summary": "Analysis failed",
        }


def analyze_image(
    image_path: Path,
    model: str = DEFAULT_MODEL,
    verbose: bool = False,
) -> Dict:
    """
    Analyze a single image file directly with the vision model.
    No keyframe extraction needed.
    """
    if verbose:
        print(f"    Sending image to {model}...")

    try:
        if HAS_OLLAMA_PKG:
            response = ollama.chat(
                model=model,
                messages=[{
                    "role": "user",
                    "content": IMAGE_ANALYSIS_PROMPT,
                    "images": [str(image_path)],
                }],
            )
            response_text = response.message.content
        else:
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()

            import urllib.request
            payload = json.dumps({
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": IMAGE_ANALYSIS_PROMPT,
                    "images": [img_b64],
                }],
                "stream": False,
            })
            req = urllib.request.Request(
                "http://localhost:11434/api/chat",
                data=payload.encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
                response_text = result.get("message", {}).get("content", "")

        return _parse_json_response(response_text)

    except Exception as e:
        return {
            "scene_description": f"Error analyzing image: {e}",
            "key_objects": "",
            "actions": "",
            "setting": "",
            "screen_text": "",
            "content_summary": "Analysis failed",
        }


def analyze_video(
    video_path: Path,
    model: str = DEFAULT_MODEL,
    num_frames: int = NUM_KEYFRAMES,
    verbose: bool = False,
) -> Dict:
    """
    Full AI analysis pipeline for a video file:
    1. Extract keyframes
    2. Analyze each frame
    3. Summarize into a single description

    Returns a dict with keys: scene_description, key_objects, actions,
    setting, screen_text, content_summary.
    """
    if verbose:
        print(f"    Extracting {num_frames} keyframes...")

    frames = extract_keyframes(video_path, num_frames)

    if not frames:
        return {
            "scene_description": "Could not extract frames from video",
            "key_objects": "",
            "actions": "",
            "setting": "",
            "screen_text": "",
            "content_summary": "Frame extraction failed",
        }

    if verbose:
        print(f"    Analyzing {len(frames)} frames with {model}...")

    # Analyze each frame
    frame_descriptions = []
    for i, frame in enumerate(frames):
        if verbose:
            print(f"    Processing frame {i + 1}/{len(frames)}...")
        desc = analyze_frame(frame, model)
        frame_descriptions.append(desc)

    if verbose:
        print(f"    Generating summary...")

    # Summarize all frame descriptions
    summary = summarize_descriptions(frame_descriptions, video_path.name, model)

    # Clean up temp frames
    for frame in frames:
        try:
            frame.unlink()
            frame.parent.rmdir()
        except Exception:
            pass

    return summary


def analyze_media(
    media_path: Path,
    media_type: str,
    model: str = DEFAULT_MODEL,
    num_frames: int = NUM_KEYFRAMES,
    verbose: bool = False,
) -> Dict:
    """
    Dispatch to the correct analysis function based on media type.

    - 'video' → extract keyframes → analyze → summarize
    - 'image' → send directly to vision model
    - 'gif'   → send first frame or treat as image
    """
    if media_type == "video":
        return analyze_video(media_path, model, num_frames, verbose)
    elif media_type in ("image", "gif"):
        return analyze_image(media_path, model, verbose)
    else:
        return analyze_video(media_path, model, num_frames, verbose)


def _parse_json_response(text: str) -> Dict:
    """Extract and parse JSON from a model response (handles markdown fences)."""
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code fences
    if "```" in text:
        # Find content between ``` markers
        parts = text.split("```")
        for part in parts:
            clean = part.strip()
            # Remove optional language tag (e.g., "json\n")
            if clean.startswith("json"):
                clean = clean[4:].strip()
            try:
                return json.loads(clean)
            except json.JSONDecodeError:
                continue

    # Try to find JSON object in the text
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    # Return raw text as description if all parsing fails
    return {
        "scene_description": text[:500],
        "key_objects": "",
        "actions": "",
        "setting": "",
        "screen_text": "",
        "content_summary": text[:200],
    }
