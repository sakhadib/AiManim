import pytest

from math2manim.core.codegen.manim_codegen import normalize_construct_body, validate_construct_body


def _canonical(code: str) -> str:
    return "\n".join(line.strip() for line in code.strip().splitlines())


def test_validate_construct_body_rejects_plain_english() -> None:
    with pytest.raises(ValueError, match="valid Python"):
        validate_construct_body("This cannot be fixed by changing the code.")


def test_validate_construct_body_accepts_manim_statements() -> None:
    validate_construct_body('title = Text("Circle")\nself.play(Write(title))')


def test_validate_construct_body_allows_from_inside_text() -> None:
    validate_construct_body('label = Text("distance from center")\nself.add(label)')


def test_normalize_construct_body_extracts_full_scene_script() -> None:
    response = '''
    from manim import *

    class Scene1(Scene):
        def construct(self):
            title = Text("Regression")
            self.play(Write(title))
    '''

    normalized = normalize_construct_body(response)
    assert _canonical(normalized) in {
        'title = Text("Regression")\nself.play(Write(title))',
        "title = Text('Regression')\nself.play(Write(title))",
    }


def test_normalize_construct_body_drops_accidental_imports() -> None:
    response = '''
    from manim import *
    title = Text("Regression")
    self.play(Write(title))
    '''

    normalized = normalize_construct_body(response)
    assert _canonical(normalized) in {
        'title = Text("Regression")\nself.play(Write(title))',
        "title = Text('Regression')\nself.play(Write(title))",
    }


def test_validate_construct_body_rejects_import_nodes() -> None:
    with pytest.raises(ValueError, match="imports"):
        validate_construct_body("from manim import *\ntitle = Text('x')")


@pytest.mark.parametrize(
    "body",
    [
        'label = MathTex("y = mx + b")',
        'label = Tex("slope")',
        "axes = Axes().add_coordinates()",
        'labels = axes.get_axis_labels(x_label="x", y_label="y")',
    ],
)
def test_validate_construct_body_rejects_latex_dependent_helpers(body: str) -> None:
    with pytest.raises(ValueError):
        validate_construct_body(body)
