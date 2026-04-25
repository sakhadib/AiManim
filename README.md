# StruggleMath

StruggleMath is a local CLI that converts a math prompt into short Manim scenes and stitches them into one final video.

## Quick Start

1. Create a Python 3.10+ environment.
2. Install package:
   - `pip install -e .`
3. Ensure external tools:
   - `manim` executable is available
   - `ffmpeg` executable is available
4. API key setup:
   - On first run, the CLI asks for provider and API key if key is not already stored.
   - The key is saved to secure OS keyring when available.
   - If secure keyring is unavailable, key is used for the current session only.

Run:
- `math2manim "Explain gradient descent" --provider openai --model gpt-4.1-mini --out outputs/final.mp4`

Dry run:
- `math2manim "Explain gradient descent" --dry-run`
