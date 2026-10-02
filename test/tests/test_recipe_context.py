"""Tests for deriving the meta.yaml.j2 render context from harvested metadata."""

from metadata_observer.metadata import PackageMetadata, recipe_render_context


def _pypi_payload(**overrides: object) -> dict:
    info = {
        "name": "requests",
        "version": "2.32.3",
        "home_page": "https://requests.readthedocs.io",
        "license": "Apache-2.0",
        "summary": "Python HTTP for Humans",
        "description": "Requests is an elegant HTTP library.",
        "project_urls": {
            "Source": "https://github.com/psf/requests",
            "Documentation": "https://requests.readthedocs.io",
        },
    }
    info.update(overrides)
    sdist = {"filename": "requests-2.32.3.tar.gz", "digests": {"sha256": "a" * 64}, "packagetype": "sdist"}
    return {"info": info, "urls": [sdist]}


def test_context_from_pypi_only() -> None:
    meta = PackageMetadata(name="requests", pypi=_pypi_payload())
    ctx = recipe_render_context(meta)

    assert ctx["name"] == "requests"
    assert ctx["version"] == "2.32.3"
    assert ctx["sha256"] == "a" * 64
    assert ctx["summary"] == "Python HTTP for Humans"
    assert ctx["home_url"] == "https://requests.readthedocs.io"
    assert ctx["dev_url"] == "https://github.com/psf/requests"
    assert ctx["import_name"] == "requests"


def test_import_name_hyphen_to_underscore() -> None:
    payload = _pypi_payload()
    payload["info"]["name"] = "my-package"
    meta = PackageMetadata(name="my-package", pypi=payload)
    ctx = recipe_render_context(meta)

    assert ctx["import_name"] == "my_package"


def test_missing_pypi_raises() -> None:
    meta = PackageMetadata(name="requests")
    try:
        recipe_render_context(meta)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "pypi" in str(exc).lower()


def test_optional_fields_default_empty() -> None:
    payload = _pypi_payload()
    payload["info"]["project_urls"] = {}
    payload["info"]["home_page"] = None
    meta = PackageMetadata(name="requests", pypi=payload)
    ctx = recipe_render_context(meta)

    assert ctx["home_url"] == ""
    assert ctx["dev_url"] == ""
    assert ctx["doc_url"] == ""
    assert ctx["noarch"] == ""
    assert ctx["run_deps"] == ""
    assert ctx["build_deps"] == ""


def test_sdist_selected_over_wheel() -> None:
    payload = _pypi_payload()
    wheel = {
        "filename": "requests-2.32.3-py3-none-any.whl",
        "digests": {"sha256": "b" * 64},
        "packagetype": "bdist_wheel",
    }
    payload["urls"].insert(0, wheel)
    meta = PackageMetadata(name="requests", pypi=payload)
    ctx = recipe_render_context(meta)

    assert ctx["sha256"] == "a" * 64
