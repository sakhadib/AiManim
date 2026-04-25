# StruggleMath

StruggleMath is a local CLI that converts a math prompt into short Manim scenes and stitches them into one final video.

## Quick Start

1. Create a Python 3.10+ environment.
2. Install package:
   - `pip install -e .`
3. Ensure external tools:
   - `manim` executable is available
   - `ffmpeg` executable is available
   - Check with `manim --version` and `ffmpeg -version`
4. API key setup:
   - On first run, the CLI asks for provider and API key if key is not already stored.
   - The key is saved to secure OS keyring when available.
   - If secure keyring is unavailable, key is used for the current session only.

Run:
- `math2manim "Explain gradient descent" --provider openrouter --model your/openrouter-model-id --out outputs/final.mp4`

OpenRouter:
- Use `OPENROUTER_API_KEY` for the API key.
- The CLI asks for an OpenRouter model id if `--model` is not provided.

Dry run:
- `math2manim "Explain gradient descent" --dry-run`
