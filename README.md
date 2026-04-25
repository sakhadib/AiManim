# AIManim

AIManim turns plain-language math prompts into short Manim animations.

It plans the explanation, generates Manim scene code with an AI model, renders each scene, repairs failed code when possible, and stitches the result into a final video.

Repository: [github.com/sakhadib/aimanim](https://github.com/sakhadib/aimanim)

## Features

- Prompt-to-video workflow for math explanations
- OpenRouter, OpenAI, and Gemini provider support
- Configurable model id per provider
- Automatic scene planning
- Manim code generation with validation and repair
- Progress messages while the pipeline runs
- Timestamped debug artifacts under `temp/`
- Intermediate scene scripts, repair attempts, logs, rendered media, and plans saved for inspection
- FFmpeg stitching into one final `.mp4`

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
python -m pip install -e .
python -m pip install manim
```

## API Keys

AIManim can read API keys from environment variables or ask for them on first run. When possible, keys are stored in your OS keyring.

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

Generate a video:

```powershell
python -m math2manim.cli.main "Explain Fibonacci numbers and their mind-blowing facts" --provider openrouter --model deepseek/deepseek-v4-flash --out outputs/final.mp4
```

If you omit `--model` for OpenRouter, AIManim prompts for the model id:

```powershell
python -m math2manim.cli.main "Explain linear regression" --provider openrouter --out outputs/final.mp4
```

Dry run without rendering:

```powershell
python -m math2manim.cli.main "Explain gradient descent" --provider openrouter --model deepseek/deepseek-v4-flash --dry-run
```

Installed console script:

```powershell
math2manim "Explain circles" --provider openrouter --model deepseek/deepseek-v4-flash
```

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
python -m math2manim.cli.main "Explain Bayes theorem" --provider openrouter --model deepseek/deepseek-v4-flash
python -m math2manim.cli.main "Explain derivatives" --provider openai --model gpt-4.1-mini
python -m math2manim.cli.main "Explain prime numbers" --provider gemini --model gemini-1.5-flash
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
