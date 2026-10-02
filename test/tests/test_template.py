"""Structural sanity for the feedstock template and its render-context schema."""

from pathlib import Path

import pytest
import yaml
from jinja2 import Environment, StrictUndefined

ASSETS = Path(__file__).parent.parent / "src" / "metadata_observer" / "assets" / "feedstock"
TEMPLATE = ASSETS / "anaconda.yaml.j2"
SCHEMA = ASSETS / "anaconda.schema.yaml"


@pytest.fixture()
def template():
    env = Environment(undefined=StrictUndefined)
    return env.from_string(TEMPLATE.read_text())


def _render(template, **ctx) -> dict:
    return yaml.safe_load(template.render(pkg_name=ctx.pop("pkg_name", "requests"), **ctx))


def test_schema_file_is_valid_yaml() -> None:
    schema = yaml.safe_load(SCHEMA.read_text())
    assert schema["type"] == "object"
    assert schema["required"] == ["pkg_name"]
    assert schema["additionalProperties"] is False


def test_render_default_is_valid_yaml(template) -> None:
    doc = _render(template)
    assert doc["anaconda_config_version"] == 1
    sources = doc["upstream_sources"]
    assert any("pypi" in s for s in sources)
    assert len([s for s in sources if "pypi" not in s]) == 0


def test_render_github_branch(template) -> None:
    doc = _render(template, github_repo="psf/requests")
    sources = doc["upstream_sources"]
    github = [s for s in sources if "github" in s]
    assert github and github[0]["github"]["identifier"] == "psf/requests"


def test_render_priority_github_beats_webpage(template) -> None:
    doc = _render(template, github_repo="psf/requests", webpage_url="https://x.com/", webpage_regex="v([0-9.]+)")
    sources = doc["upstream_sources"]
    assert any("github" in s for s in sources)
    assert not any("webpage" in s for s in sources)


def test_render_webpage_branch(template) -> None:
    doc = _render(template, webpage_url="https://x.com/r/", webpage_regex="v([0-9.]+)")
    sources = doc["upstream_sources"]
    webpage = [s for s in sources if "webpage" in s]
    assert webpage and webpage[0]["webpage"]["url"] == "https://x.com/r/"


def test_render_requires_pkg_name(template) -> None:
    with pytest.raises(Exception):
        template.render()
