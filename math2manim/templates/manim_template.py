"""Template utilities for Manim scene files."""

from __future__ import annotations

from textwrap import indent


def build_scene_script(
    *,
    class_name: str,
    construct_body: str,
    enable_voiceover: bool = False,
    voice_provider: str = "gtts",
    voice_lang: str = "en",
    narration: str = "",
) -> str:
    body = indent(construct_body.strip() or "pass", " " * 8)
    if not enable_voiceover:
        return (
            "from manim import *\n\n"
            f"class {class_name}(Scene):\n"
            "    def construct(self):\n"
            f"{body}\n"
        )

    provider = voice_provider.strip().lower()
    narration_text = (narration or "").strip() or "Let's walk through this step by step."

    if provider == "pyttsx3":
        service_import = "from manim_voiceover.services.pyttsx3 import PyTTSX3Service"
        service_setup = "self.set_speech_service(PyTTSX3Service())"
    else:
        service_import = "from manim_voiceover.services.gtts import GTTSService"
        service_setup = f"self.set_speech_service(GTTSService(lang={voice_lang!r}))"

    voice_body = indent(construct_body.strip() or "pass", " " * 12)
    return (
        "from manim import *\n\n"
        "from manim_voiceover import VoiceoverScene\n"
        f"{service_import}\n\n"
        f"class {class_name}(VoiceoverScene):\n"
        "    def construct(self):\n"
        f"        {service_setup}\n"
        f"        with self.voiceover(text={narration_text!r}) as tracker:\n"
        f"{voice_body}\n"
    )
