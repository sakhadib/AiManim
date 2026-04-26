# Manim Skill Specification (STRICT)

This document defines the ONLY allowed patterns for generating Manim code.

The goal is:
- short scenes (≤ 5 seconds)
- minimal complexity
- high reliability
- zero runtime errors

You MUST follow all rules.

---

## 1. Code Scope Rules

You are ONLY allowed to generate code inside:

    def construct(self):

DO NOT include:
- import statements
- class definitions
- function definitions
- global variables

---

## 2. Scene Constraints

Each scene MUST satisfy:

- Total runtime ≤ 5 seconds
- Max animations: 3
- Max objects (Mobjects): 4

---

## 3. Timing Rules (MANDATORY)

Every animation MUST specify run_time.

Example:

    self.play(Create(graph), run_time=2)

Allowed:

- run_time between 0.5 and 3 seconds
- total sum of all run_time + wait ≤ 5 seconds

Allowed wait:

    self.wait(1)

DO NOT:
- omit run_time
- use long waits (>2 seconds)

---

## 4. Allowed Objects

Use ONLY these:

- Axes
- NumberPlane
- Text
- MathTex
- Dot
- Line
- Circle
- Rectangle
- Arrow

---

## 5. Allowed Animations

Use ONLY:

- Create
- Write
- FadeIn
- FadeOut
- Transform

---

## 6. Graph Plotting Pattern

Use this exact structure:

    axes = Axes()
    graph = axes.plot(lambda x: x**2)

    self.play(Create(axes), run_time=1)
    self.play(Create(graph), run_time=2)

---

## 7. Text Pattern

    text = Text("Example")
    self.play(Write(text), run_time=1.5)

Math:

    eq = MathTex("x^2")
    self.play(Write(eq), run_time=1.5)

---

## 8. Positioning Rules

Allowed:

    obj.move_to(ORIGIN)
    obj.to_edge(UP)
    obj.next_to(other, RIGHT)

DO NOT:
- use complex coordinate math
- use updaters
- use always_redraw

---

## 9. Transformation Pattern

    self.play(Transform(obj1, obj2), run_time=2)

---

## 10. Forbidden Patterns (STRICT)

DO NOT USE:

- always_redraw
- add_updater
- ValueTracker
- custom classes
- loops (for/while)
- try/except
- lambda inside animations (except simple plot)
- nested animations
- animation groups
- camera manipulation

---

## 11. Simplicity Rule

Each scene should do ONLY ONE idea:

Examples:
- draw graph
- show equation
- show tangent line

DO NOT combine multiple concepts in one scene.

---

## 12. Error Avoidance

Ensure:

- all variables are defined before use
- no typos in class names
- correct object names (Axes, not Axess)
- all objects used in play() exist

---

## 13. Output Requirements

Your output MUST:

- be valid Python code
- run without modification
- strictly follow constraints
- be minimal and clean

---

## 14. Example (VALID)

    axes = Axes()
    graph = axes.plot(lambda x: x**2)

    self.play(Create(axes), run_time=1)
    self.play(Create(graph), run_time=2)
    self.wait(1)

---

## 15. Example (INVALID)

❌ Missing run_time  
❌ Too many objects  
❌ More than 5 seconds  
❌ Using unsupported features  

---


Manim’s narration support is typically used through the **voiceover/TTS workflow**: you set a TTS service, then wrap animation code in a voiceover block so Manim can match timing to the spoken text. 

## How to use it

1. Install the voiceover plugin that matches your Manim setup.  
2. Inherit from `VoiceoverScene`.  
3. Set a speech/TTS service such as `GTTSService` or `pyttsx3`.  
4. Put narration text inside `with self.voiceover("...") as tracker:`.  
5. Use `tracker.duration` to synchronize animation runtime with the narration. 

## System-style usage

```python
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class Demo(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService(lang="en"))

        title = Text("Voice narration in Manim")

        with self.voiceover(text="This title appears while I speak.") as tracker:
            self.play(Write(title), run_time=tracker.duration)

        self.wait()
```

This is the intended pattern: narration drives the animation timing, and Manim waits if the animation ends early or keeps animating until the spoken line finishes. 

## Built-in narration options

The documented TTS choices include **gTTS**, **Azure Text to Speech**, **Coqui TTS**, and **pyttsx3**; the docs recommend gTTS as an easy starting point and Azure for higher-quality AI voices.

If you need fine control, the plugin also supports word-level timing, so you can trigger visual events at specific words in the narration.

## Practical rule

Use `tracker.duration` for most scenes, because it keeps the animation naturally aligned with the narration without manual stopwatch-style syncing. For repeated narration edits, this is much faster than exporting audio separately and syncing it in another editor.

---

## FINAL RULE

If unsure, choose the simplest possible implementation.

Reliability > visual complexity.


