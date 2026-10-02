"""Structural sanity for the feedstock template and its render-context schema."""

from pathlib import Path

import jinja2
import pytest
import yaml
from jinja2 import Environment, StrictUndefined

ASSETS = Path(__file__).parent.parent / "src" / "metadata_observer" / "assets" / "feedstock"
TEMPLATE = ASSETS / "anaconda.yaml.j2"
SCHEMA = ASSETS / "anaconda.schema.yaml"
ABS_TEMPLATE = ASSETS / "abs.yaml.j2"
ABS_SCHEMA = ASSETS / "abs.schema.yaml"


@pytest.fixture()
def template() -> "jinja2.Template":
    env = Environment(undefined=StrictUndefined, autoescape=False)  # noqa: S701 — YAML output, not HTML
    return env.from_string(TEMPLATE.read_text())


def _render(template: "jinja2.Template", **ctx: object) -> dict:
    return yaml.safe_load(template.render(pkg_name=ctx.pop("pkg_name", "requests"), **ctx))


def test_schema_file_is_valid_yaml() -> None:
    schema = yaml.safe_load(SCHEMA.read_text())
    assert schema["type"] == "object"
    assert schema["required"] == ["pkg_name"]
    assert schema["additionalProperties"] is False


def test_render_default_is_valid_yaml(template: "jinja2.Template") -> None:
    doc = _render(template)
    assert doc["anaconda_config_version"] == 1
    sources = doc["upstream_sources"]
    assert any("pypi" in s for s in sources)
    assert len([s for s in sources if "pypi" not in s]) == 0


def test_render_github_branch(template: "jinja2.Template") -> None:
    doc = _render(template, github_repo="psf/requests")
    sources = doc["upstream_sources"]
    github = [s for s in sources if "github" in s]
    assert github and github[0]["github"]["identifier"] == "psf/requests"


def test_render_priority_github_beats_webpage(template: "jinja2.Template") -> None:
    doc = _render(template, github_repo="psf/requests", webpage_url="https://x.com/", webpage_regex="v([0-9.]+)")
    sources = doc["upstream_sources"]
    assert any("github" in s for s in sources)
    assert not any("webpage" in s for s in sources)


def test_render_webpage_branch(template: "jinja2.Template") -> None:
    doc = _render(template, webpage_url="https://x.com/r/", webpage_regex="v([0-9.]+)")
    sources = doc["upstream_sources"]
    webpage = [s for s in sources if "webpage" in s]
    assert webpage and webpage[0]["webpage"]["url"] == "https://x.com/r/"


def test_render_requires_pkg_name(template: "jinja2.Template") -> None:
    with pytest.raises((jinja2.UndefinedError, KeyError)):
        template.render()


@pytest.fixture()
def abs_template() -> "jinja2.Template":
    env = Environment(undefined=StrictUndefined, autoescape=False)  # noqa: S701 — YAML output, not HTML
    return env.from_string(ABS_TEMPLATE.read_text())


class _Meta:
    """Attribute-access wrapper for template render context (Jinja resolves meta.package.name via getattr)."""

    def __init__(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            setattr(self, key, _Meta(**value) if isinstance(value, dict) else value)


def test_abs_schema_file_is_valid_yaml() -> None:
    schema = yaml.safe_load(ABS_SCHEMA.read_text())
    assert schema["type"] == "object"
    assert schema["required"] == ["meta"]


def test_abs_render_is_valid_yaml(abs_template: "jinja2.Template") -> None:
    doc = yaml.safe_load(abs_template.render(meta=_Meta(package={"name": "requests"})))
    assert doc["name"] == "requests"
    assert doc["version"] == 1
    assert "defaults" in doc["channels"]
    assert doc["with_sbom"] is True


def test_abs_render_missing_name_raises(abs_template: "jinja2.Template") -> None:
    with pytest.raises((jinja2.UndefinedError, KeyError)):
        abs_template.render(meta=_Meta(package={}))


META_TEMPLATE = ASSETS / "meta.yaml.j2"
META_SCHEMA = ASSETS / "meta.schema.yaml"

META_CTX = {
    "name": "requests",
    "version": "2.32.3",
    "sha256": "a" * 64,
    "noarch": "\n  noarch: python",
    "skip": "",
    "build_deps": "",
    "run_deps": "",
    "import_name": "requests",
    "home_url": "https://requests.readthedocs.io",
    "license_id": "Apache-2.0",
    "license_family": "APACHE",
    "license_file": "LICENSE",
    "summary": "Python HTTP for Humans",
    "description": "",
    "dev_url": "https://github.com/psf/requests",
    "doc_url": "https://requests.readthedocs.io",
    "zendesk_ticket": "12345",
}


def test_meta_schema_file_is_valid_yaml() -> None:
    schema = yaml.safe_load(META_SCHEMA.read_text())
    assert schema["type"] == "object"
    assert "name" in schema["required"]
    assert schema["properties"]["sha256"]["pattern"] == "^[0-9a-f]{64}$"


def _render_meta(**overrides: str) -> str:
    """Two-stage render: Jinja passthrough of conda markers, then string.Template substitution.

    The `{% set %}` header lines are conda-build Jinja, not YAML — excluded from the YAML parse.
    """
    from string import Template

    env = Environment(undefined=StrictUndefined, autoescape=False)  # noqa: S701 — YAML output, not HTML
    stage1 = env.from_string(META_TEMPLATE.read_text()).render()
    ctx = {**META_CTX, **overrides}
    return Template(stage1).safe_substitute(ctx)


def _yaml_after_set_lines(rendered: str) -> dict:
    body = "\n".join(line for line in rendered.splitlines() if not line.startswith("{%"))
    return yaml.safe_load(body)


def test_meta_two_stage_render_produces_valid_yaml() -> None:
    rendered = _render_meta()
    # stage 1 leaves conda-build jinja markers intact
    assert "{{ name }}" in rendered
    assert '{{ name[0] }}' in rendered
    assert rendered.splitlines()[0] == '{% set name = "requests" %}'
    # YAML-body parse skips the set-header lines AND lines containing conda-build
    # markers ({{ }} scalars are invalid YAML pre-resolution by design)
    body = "\n".join(
        line for line in rendered.splitlines() if not line.startswith("{%") and "{{" not in line
    )
    doc = yaml.safe_load(body)
    assert "package" in doc  # children carry {{ }} markers; parsed as None pre-resolution
    assert doc["source"]["sha256"] == "a" * 64
    assert doc["build"]["noarch"] == "python"
    assert doc["build"]["number"] == 0
    assert doc["test"]["imports"] == ["requests"]
    assert doc["about"]["license_family"] == "APACHE"


def test_meta_render_noarch_absent() -> None:
    rendered = _render_meta(noarch="")
    body = "\n".join(
        line for line in rendered.splitlines() if not line.startswith("{%") and "{{" not in line
    )
    doc = yaml.safe_load(body)
    assert "noarch" not in doc["build"]
