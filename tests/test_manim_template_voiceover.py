from math2manim.templates.manim_template import build_scene_script


def test_build_scene_script_without_voiceover_uses_scene_base() -> None:
    script = build_scene_script(class_name="Scene1", construct_body="self.wait(1)")
    assert "class Scene1(Scene):" in script
    assert "VoiceoverScene" not in script


def test_build_scene_script_with_gtts_voiceover() -> None:
    script = build_scene_script(
        class_name="Scene1",
        construct_body="self.wait(1)",
        enable_voiceover=True,
        voice_provider="gtts",
        voice_lang="en",
        narration="This is narration",
    )
    assert "from manim_voiceover import VoiceoverScene" in script
    assert "from manim_voiceover.services.gtts import GTTSService" in script
    assert "class Scene1(VoiceoverScene):" in script
    assert "self.set_speech_service(GTTSService(lang='en'))" in script
    assert "with self.voiceover(text='This is narration') as tracker:" in script


def test_build_scene_script_with_pyttsx3_voiceover() -> None:
    script = build_scene_script(
        class_name="Scene1",
        construct_body="self.wait(1)",
        enable_voiceover=True,
        voice_provider="pyttsx3",
        narration="voice",
    )
    assert "from manim_voiceover.services.pyttsx3 import PyTTSX3Service" in script
    assert "self.set_speech_service(PyTTSX3Service())" in script
