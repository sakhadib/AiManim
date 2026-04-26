# AIManim

AIManim turns plain-language math prompts into short Manim animations.

It plans the explanation, generates Manim scene code with an AI model, renders each scene, repairs failed code when possible, and stitches the result into a final video.

Repository: [github.com/sakhadib/aimanim](https://github.com/sakhadib/aimanim)

## Features

- Prompt-to-video workflow for math explanations
- OpenRouter, OpenAI, and Gemini provider support
- Configurable model id per provider
- Automatic scene planning
- Adaptive scene planning controls (`--min-scenes`, `--max-scenes`, `--target-total-seconds`)
- Manim code generation with validation and repair
- Optional voiceover narration via Manim voiceover services (gTTS or pyttsx3)
- Planner regeneration when AI returns invalid JSON/plan structure
- Code generation regeneration when AI returns invalid construct bodies
- Progress messages while the pipeline runs
- Timestamped debug artifacts under `temp/`
- Intermediate scene scripts, repair attempts, logs, rendered media, and plans saved for inspection
- FFmpeg stitching into one final `.mp4`
- Partial-output stitching: failed or missing scenes are skipped and remaining scenes are stitched in order

## Requirements

- Python 3.10+
- [Manim Community](https://www.manim.community/)
- [FFmpeg](https://ffmpeg.org/)
- An API key for your chosen AI provider

Check your render tools:

```powershell
python -m manim --version
ffmpeg -version
```

## Installation

Clone the repository:

```powershell
git clone https://github.com/sakhadib/aimanim.git
cd aimanim
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the package:

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
```

Optional voiceover dependencies:

```powershell
python -m pip install -e ".[voice]"
```

## First-Time Setup

Run the setup wizard:

```powershell
aimanim setup
```

The wizard asks for:

- Provider
- Model id
- API key

AIManim stores provider/model defaults in:

```text
~/.aimanim/config.json
```

API keys are read from environment variables or stored in your OS keyring when available.

Supported environment variables:

```text
OPENROUTER_API_KEY
OPENAI_API_KEY
GEMINI_API_KEY
```

For OpenRouter:

```powershell
$env:OPENROUTER_API_KEY="your-openrouter-key"
```

## Usage

Generate a video after setup:

```powershell
aimanim "Explain Fibonacci numbers and their mind-blowing facts"
```

Explicit generate command:

```powershell
aimanim generate "Explain linear regression"
```

Generate with all options:

```powershell
aimanim generate "Explain Fibonacci numbers and their mind-blowing facts" --provider openrouter --model deepseek/deepseek-v4-flash --out outputs/final.mp4 --codegen-workers 4
```

Generate a longer, richer explanation by targeting more scenes and total duration:

```powershell
aimanim generate "Explain eigen vectors with worked examples" --provider openai --min-scenes 10 --max-scenes 20 --target-total-seconds 120 --codegen-workers 8
```

If you omit `--model` for OpenRouter, AIManim prompts for the model id:

```powershell
aimanim generate "Explain linear regression" --provider openrouter --out outputs/final.mp4
```

Dry run without rendering:

```powershell
aimanim generate "Explain gradient descent" --provider openrouter --model deepseek/deepseek-v4-flash --dry-run
```

Generate with narration voiceover:

```powershell
aimanim generate "Explain Newton-Raphson method" --provider openai --voiceover --voice-provider gtts --voice-lang en --out outputs/newton_voice.mp4
```

Legacy command alias:

```powershell
math2manim "Explain circles" --provider openrouter --model deepseek/deepseek-v4-flash
```

## CLI Commands

```powershell
aimanim setup
aimanim providers
aimanim config
aimanim doctor
aimanim generate "Explain derivatives"
aimanim "Explain circles"
```

Command overview:

- `setup`: configure default provider, model id, and API key.
- `providers`: list supported providers, key status, model defaults, and environment variables.
- `config`: print the current CLI config.
- `doctor`: check Manim, FFmpeg, default provider, default model, and API key status.
- `generate`: create a video from a math prompt.
- Root prompt shortcut: `aimanim "Explain ..."`.

Initial scene code generation runs in parallel by default. Tune it with:

```powershell
aimanim generate "Explain Fourier series" --codegen-workers 6
```

Rendering still runs scene-by-scene so Manim media output and repair logs stay predictable.

Scene planning controls:

```powershell
aimanim generate "Explain Newton-Raphson" --min-scenes 15 --max-scenes 25 --target-total-seconds 150
```

Non-interactive mode for CI or scripts:

```powershell
aimanim generate "Explain derivatives" --provider openai --model gpt-4.1-mini --non-interactive
```

If `--non-interactive` is enabled and setup is missing, AIManim fails with a clear message instead of prompting.

## Voiceover

AIManim can render narration directly inside each generated Manim scene.

- Enable with `--voiceover`.
- Choose provider with `--voice-provider gtts` or `--voice-provider pyttsx3`.
- Set language for gTTS with `--voice-lang` (for example `en`, `en-us`, `hi`).

Examples:

```powershell
aimanim generate "Explain eigen vectors" --voiceover --voice-provider gtts --voice-lang en
aimanim generate "Explain gradient descent" --voiceover --voice-provider pyttsx3
```

Dependency notes:

- Voiceover mode requires `manim-voiceover` plus the selected speech backend.
- If voiceover dependencies are missing, AIManim fails early with a clear preflight error.

## Reliability Behavior

- Planner stage auto-regenerates if AI output is invalid JSON, schema-invalid, or violates scene-count bounds.
- Codegen stage auto-regenerates when output cannot be normalized/validated as `construct()` body code.
- Render stage retries per scene with AI-assisted fixes up to `--max-retries`.
- Environment failures (missing/blocked Manim dependencies) are surfaced clearly and are not treated as AI-fixable.
- If a scene fails or a scene video is missing, the run continues and stitches remaining valid scenes in order.
- If all scenes fail, the run exits with a clear "nothing to stitch" style error.

## Debug Artifacts

Every run creates a timestamped folder:

```text
temp/<timestamp>/
```

Example structure:

```text
temp/20260425_225204/
  prompt.txt
  plan.json
  concat_list.txt
  ffmpeg_stdout.log
  ffmpeg_stderr.log
  scenes/
    scene_001/
      scene.json
      construct_initial.py
      repair_1.py
      attempt_1/
        construct_body.py
        scene_1.py
        stdout.log
        stderr.log
  media/
```

Use this folder to inspect generated Manim code, render errors, repair attempts, and intermediate video files.

## Providers

Supported providers:

```text
openrouter
openai
gemini
```

Examples:

```powershell
aimanim generate "Explain Bayes theorem" --provider openrouter --model deepseek/deepseek-v4-flash
aimanim generate "Explain derivatives" --provider openai --model gpt-4.1-mini
aimanim generate "Explain prime numbers" --provider gemini --model gemini-1.5-flash
```

## Development

Install development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Run tests:

```powershell
python -m pytest
```

Run a syntax check:

```powershell
python -m compileall math2manim tests
```

## Notes

- AIManim avoids LaTeX-dependent Manim helpers by default, preferring `Text()` labels for easier Windows setup.
- If generated code fails, the repair loop receives the Manim console error and asks the model for corrected code.
- If the issue is environmental, such as missing Manim, missing FFmpeg, or blocked native dependencies, AIManim stops early with a clearer error.

## License

AIManim is open source under the MIT License. See [LICENSE](LICENSE).
