# StruggleMath — System Implementation Plan

## Objective

## Concrete Development Plan (Execution Checklist)

This checklist is the implementation contract for the current MVP build.

1. Bootstrap package + dependencies
    - Create package structure under `math2manim/`.
    - Add `pyproject.toml`, `.gitignore`, and basic `README.md`.
2. Implement strict schema contracts
    - Add `Scene` and `ScenePlan` with validation for duration, element count, animation limits, and exactly 2 scenes for MVP.
3. Implement provider strategy layer
    - Add `LLMProvider` base interface.
    - Add `OpenAIProvider`, `GeminiProvider`, and factory selection.
4. Implement planning and constrained codegen
    - Build planner that returns strict JSON scene plans.
    - Build codegen that emits `construct()` body only and rejects forbidden snippets.
5. Implement execution + repair loop
    - Execute Manim through subprocess and capture stderr.
    - Attempt minimal repair up to `max_retries=3`.
6. Implement rendering and stitching
    - Render each scene to mp4 with low quality (`-ql`) default.
    - Stitch scenes using FFmpeg concat and fail clearly when FFmpeg is missing.
7. Implement CLI (Typer)
    - Command: `math2manim "<prompt>"`.
    - Options: `--provider`, `--model`, `--out`, `--max-retries`, `--keep-scenes`, `--dry-run`.
    - `--dry-run` prints validated scene plan and generated code only.
8. Implement workflow orchestration
    - Provide LangGraph-compatible workflow module and runnable pipeline entry.
9. Add tests and verification
    - Unit tests: schema + provider factory.
    - Smoke test: planner + codegen dry-run path.
10. Validate MVP acceptance
    - Exactly 2 scenes generated.
    - Retry path available.
    - Final stitched output produced by full run when Manim + FFmpeg are installed.

### Current Status

- Project scaffolded and modules implemented per structure.
- Unit + smoke tests created and passing (`7 passed`).

Build a local, OS-agnostic CLI tool that:
1. Takes a math prompt
2. Generates structured scene plans using an LLM
3. Converts each scene into constrained Manim code
4. Executes and auto-repairs code if errors occur
5. Renders each scene as a short video (≤5 sec)
6. Optionally generates narration
7. Stitches all scenes into a final video
8. Cleans intermediate artifacts

---

## Core Design Principles

- Strict intermediate representation (IR)
- Bounded generation (≤5 sec per scene)
- Constrained code generation (construct() only)
- Retry loop with max attempts (3)
- OS-agnostic (no shell-specific logic)
- Modular architecture
- Pluggable LLM providers (strategy pattern)

---

## Tech Stack

- Python 3.10+
- Manim
- LangGraph
- Pydantic
- FFmpeg (external dependency)
- Optional TTS (OpenAI / ElevenLabs / Coqui)

## Development Environment
- Windows 11

---

## Project Structure

```

math2manim/
│
├── cli/
│   └── main.py
│
├── core/
│   ├── planner/
│   │   └── scene_planner.py
│   ├── codegen/
│   │   └── manim_codegen.py
│   ├── executor/
│   │   └── runner.py
│   ├── repair/
│   │   └── fixer.py
│   ├── renderer/
│   │   └── render.py
│   ├── stitcher/
│   │   └── stitch.py
│   └── utils/
│       └── paths.py
│
├── providers/
│   ├── base.py
│   ├── openai_provider.py
│   ├── gemini_provider.py
│   └── factory.py
│
├── workflows/
│   └── langgraph_flow.py
│
├── schemas/
│   └── scene.py
│
├── templates/
│   └── manim_template.py
│
├── prompts/
│   ├── planner.txt
│   ├── codegen.txt
│   ├── repair.txt
│   └── manim_skill.md
│
└── outputs/

````

---

## Scene Plan Schema (STRICT)

Use Pydantic.

```python
class Scene(BaseModel):
    id: int
    goal: str
    narration: str
    duration_sec: float
    visual_elements: list[str]

    @validator("duration_sec")
    def max_duration(cls, v):
        if v > 5:
            raise ValueError("Scene duration exceeds 5 seconds")
        return v
````

---

## LLM Strategy Pattern

Define base interface:

```python
class LLMProvider:
    def generate(self, prompt: str) -> str:
        pass
```

Factory:

```python
def get_provider(name: str):
    ...
```

User selects provider via CLI.

---

## LangGraph Workflow

Nodes:

* parse_prompt
* generate_scene_plan
* validate_plan
* generate_manim_code
* execute_code
* fix_code (conditional loop)
* render_scene
* stitch_video

Graph:

START → plan → validate → loop scenes → stitch → END

Retry logic:

* max_attempts = 3

LangGraph is used because it supports stateful multi-step workflows with retries and branching.

---

## Code Generation Rules (CRITICAL)

LLM must ONLY generate code inside:

```python
def construct(self):
```

Forbidden:

* imports
* class definitions
* external dependencies

All code inserted into template:

```python
from manim import *

class SceneX(Scene):
    def construct(self):
        # LLM GENERATED CODE
```

---

## Scene Constraints

Each scene must satisfy:

* duration ≤ 5 seconds
* max 3 animations
* max 4 visual elements

---

## Execution Engine

Use subprocess:

```python
subprocess.run(
    ["manim", "-q", "l", file, scene_name],
    capture_output=True,
    text=True
)
```

Capture stderr → send to repair module.

---

## Error Repair Loop

Input to LLM:

```
Error Type:
Error Message:
Code:
```

Instruction:

* Fix ONLY the error
* Do NOT rewrite full code

Max retries = 3

---

## Rendering

Each scene produces:

```
scene_1.mp4
scene_2.mp4
```

---

## Stitching

Use FFmpeg concat:

```
file 'scene_1.mp4'
file 'scene_2.mp4'
```

Command:

```bash
ffmpeg -f concat -safe 0 -i list.txt -c copy final.mp4
```

---

## File Management

Use:

* pathlib
* tempfile

After success:

* delete intermediate files (unless --keep-scenes)

---

## CLI Interface

Command:

```
math2manim "Explain gradient descent"
```

Options:

```
--provider openai
--model gpt-4.1
--out output.mp4
--max-retries 3
--keep-scenes
--dry-run
```

---

## Cross-Platform Rules

* No shell-specific commands
* Use pathlib for all paths
* Detect ffmpeg via shutil.which()
* Use TemporaryDirectory for temp files

---

## Prompt Design

### planner.txt

* Convert prompt → structured scenes
* Enforce duration + element limits

### codegen.txt

* Generate ONLY construct() code
* Follow manim_skill.md strictly

### repair.txt

* Fix minimal errors

### manim_skill.md

Defines:

* allowed patterns
* forbidden patterns
* timing constraints

---

## MVP Scope (STRICT)

First version must:

1. Generate 2 scenes
2. Produce valid Manim code
3. Render successfully
4. Stitch into final video

NO:

* TTS
* advanced planning
* caching

---

## Success Criteria

* Works on Windows + Linux
* Produces valid video from prompt
* Handles at least 1 retry case
* No manual intervention required

---

## Future Extensions (NOT NOW)

* TTS integration
* parallel rendering
* symbolic math (SymPy)
* caching
* style templates
* dataset generation

---

## Implementation Order

1. schemas
2. provider system
3. planner
4. codegen
5. executor
6. repair loop
7. renderer
8. stitcher
9. CLI
10. LangGraph integration

---

## Final Instruction

Build minimal, working pipeline first.
Do NOT optimize early.
Do NOT over-engineer.

Execution > elegance.
