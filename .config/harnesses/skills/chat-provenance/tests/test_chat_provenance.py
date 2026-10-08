"""Tests for chat-provenance scripts: log_entry, save_source, session, render, verify, claude-hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
TODAY = datetime.now().strftime("%Y-%m-%d")


def run(
    script: str,
    args: list[str],
    cwd: Path,
    stdin: str | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    env = {**os.environ, "CHAT_PROVENANCE_CREATOR": "test-harness", **(env_extra or {})}
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def daily_path(repo: Path) -> Path:
    return repo / ".harness" / "chat-provenance" / f"{TODAY}.md"


def daily_log(repo: Path) -> str:
    return daily_path(repo).read_text(encoding="utf-8")


def git_commit(repo: Path) -> None:
    (repo / "seed.txt").write_text("seed", encoding="utf-8")
    subprocess.run(["git", "add", "seed.txt"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "seed"],
        cwd=repo,
        check=True,
    )


class TestLogEntry:
    def test_creates_daily_log_with_frontmatter(self, repo: Path) -> None:
        result = run("log_entry.py", ["--role", "user", "--agent", "main"], repo, "hello world")
        assert result.returncode == 0, result.stderr
        text = daily_log(repo)
        assert f"date: {TODAY}" in text
        assert "type: chat-provenance-log" in text
        assert "creator: test-harness" in text
        assert "## user" in text
        assert "agent: main" in text
        assert "hello world" in text

    def test_two_entries_share_minute_heading(self, repo: Path) -> None:
        run("log_entry.py", ["--role", "user", "--agent", "main"], repo, "first")
        run("log_entry.py", ["--role", "assistant", "--agent", "main"], repo, "second")
        text = daily_log(repo)
        headings = [line for line in text.splitlines() if line.startswith("# ") and ":" in line]
        assert len(headings) == 1
        assert text.count("## user") == 1
        assert text.count("## assistant") == 1

    def test_kind_overrides_heading(self, repo: Path) -> None:
        run(
            "log_entry.py",
            ["--role", "assistant", "--kind", "decision", "--agent", "main"],
            repo,
            "chose: flock\nrejected: [none]\nbecause: writers queue",
        )
        assert "## decision" in daily_log(repo)

    def test_session_metadata_recorded(self, repo: Path) -> None:
        run(
            "log_entry.py",
            ["--role", "user", "--agent", "main", "--session", "abc123"],
            repo,
            "scoped",
        )
        assert "agent: main | session: abc123" in daily_log(repo)

    def test_task_metadata_recorded(self, repo: Path) -> None:
        run(
            "log_entry.py",
            ["--role", "assistant", "--agent", "bug", "--task", "t1"],
            repo,
            "subagent result",
        )
        assert "agent: bug | task: t1" in daily_log(repo)

    def test_empty_stdin_exits_2(self, repo: Path) -> None:
        result = run("log_entry.py", ["--role", "user", "--agent", "main"], repo, "   ")
        assert result.returncode == 2
        assert not daily_path(repo).exists()

    def test_outside_repo_exits_1(self, tmp_path: Path) -> None:
        result = run("log_entry.py", ["--role", "user", "--agent", "main"], tmp_path, "x")
        assert result.returncode == 1

    def test_redaction(self, repo: Path) -> None:
        secret = "sk-" + "a" * 24
        run("log_entry.py", ["--role", "user", "--agent", "main"], repo, f"key is {secret}")
        text = daily_log(repo)
        assert secret not in text
        assert "[REDACTED:openai-key]" in text

    def test_redaction_emits_action_entry(self, repo: Path) -> None:
        secret = "AKIA" + "B" * 16
        run("log_entry.py", ["--role", "user", "--agent", "main"], repo, f"aws {secret}")
        text = daily_log(repo)
        assert "## action" in text
        assert "redaction: aws-access-key pattern matched in the preceding user entry" in text

    def test_seq_and_prev_chain_present(self, repo: Path) -> None:
        run("log_entry.py", ["--role", "user", "--agent", "main"], repo, "one")
        run("log_entry.py", ["--role", "user", "--agent", "main"], repo, "two")
        run("log_entry.py", ["--role", "user", "--agent", "main"], repo, "three")
        text = daily_log(repo)
        assert "seq: 1" in text
        assert "seq: 2" in text
        assert "seq: 3" in text
        assert text.count("prev: sha256:") == 3

    def test_attr_model_repo_state_metadata(self, repo: Path) -> None:
        git_commit(repo)
        run(
            "log_entry.py",
            ["--role", "user", "--agent", "main"],
            repo,
            "context check",
            env_extra={"CHAT_PROVENANCE_USER": "testuser", "CHAT_PROVENANCE_MODEL": "test/model"},
        )
        text = daily_log(repo)
        assert "attr: testuser" in text
        assert "model: test/model" in text
        assert "at: master@" in text or "at: main@" in text

    def test_append_only_growth(self, repo: Path) -> None:
        run("log_entry.py", ["--role", "user", "--agent", "main"], repo, "first")
        snapshot = daily_log(repo)
        run("log_entry.py", ["--role", "user", "--agent", "main"], repo, "second")
        after = daily_log(repo)
        assert after.startswith(snapshot)
        assert len(after) > len(snapshot)

    def test_concurrent_writers_lose_nothing(self, repo: Path) -> None:
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(
                pool.map(
                    lambda i: run("log_entry.py", ["--role", "user", "--agent", "main"], repo, f"entry-{i}"),
                    range(12),
                )
            )
        assert all(r.returncode == 0 for r in results)
        text = daily_log(repo)
        for i in range(12):
            assert f"entry-{i}" in text


class TestVerify:
    def test_clean_log_verifies(self, repo: Path) -> None:
        run("log_entry.py", ["--role", "user", "--agent", "main"], repo, "one")
        run("log_entry.py", ["--role", "assistant", "--agent", "main"], repo, "two")
        result = run("verify.py", [], repo)
        assert result.returncode == 0, result.stdout
        assert "0 problems" in result.stdout

    def test_tamper_detected(self, repo: Path) -> None:
        run("log_entry.py", ["--role", "user", "--agent", "main"], repo, "one")
        run("log_entry.py", ["--role", "user", "--agent", "main"], repo, "two")
        path = daily_path(repo)
        path.write_text(path.read_text(encoding="utf-8").replace("one", "ONE"), encoding="utf-8")
        result = run("verify.py", [], repo)
        assert result.returncode == 1
        assert "chain break" in result.stdout

    def test_missing_day_exits_1(self, repo: Path) -> None:
        assert run("verify.py", ["1999-01-01"], repo).returncode == 1


class TestSaveSource:
    def test_stdin_capture_writes_capture_log_and_index(self, repo: Path) -> None:
        result = run(
            "save_source.py",
            ["--source-url", "https://example.com/doc", "--type", "documentation"],
            repo,
            "# Doc Title\n\nbody text",
        )
        assert result.returncode == 0, result.stderr
        capture = repo / ".harness" / "research" / TODAY / "doc-title.md"
        assert capture.exists()
        capture_text = capture.read_text(encoding="utf-8")
        assert "title: Doc Title" in capture_text
        assert "source: https://example.com/doc" in capture_text
        assert "type: documentation" in capture_text
        assert "digest: sha256:" in capture_text
        log = daily_log(repo)
        assert "## source" in log
        assert f"capture: research/{TODAY}/doc-title.md" in log
        assert "digest: sha256:" in log
        index = (repo / ".harness" / "research" / "index.md").read_text(encoding="utf-8")
        assert "| Doc Title |" in index
        assert "https://example.com/doc" in index

    def test_identical_capture_is_cached(self, repo: Path) -> None:
        args = ["--source-url", "https://example.com/a"]
        first = run("save_source.py", args, repo, "# A\n\nsame body")
        second = run("save_source.py", args, repo, "# A\n\nsame body")
        assert first.stdout.startswith("saved:")
        assert second.stdout.startswith("cached:")
        day_dir = repo / ".harness" / "research" / TODAY
        assert len(list(day_dir.glob("a*.md"))) == 1

    def test_differing_capture_gets_suffix(self, repo: Path) -> None:
        args = ["--source-url", "https://example.com/a"]
        run("save_source.py", args, repo, "# A\n\nbody one")
        run("save_source.py", args, repo, "# A\n\nbody two")
        day_dir = repo / ".harness" / "research" / TODAY
        assert (day_dir / "a.md").exists()
        assert (day_dir / "a-2.md").exists()

    def test_title_override(self, repo: Path) -> None:
        run(
            "save_source.py",
            ["--source-url", "https://example.com/x", "--title", "My Custom Title"],
            repo,
            "no heading here",
        )
        assert (repo / ".harness" / "research" / TODAY / "my-custom-title.md").exists()

    def test_title_fallback_is_domain_path(self, repo: Path) -> None:
        run("save_source.py", ["--source-url", "https://example.com/some/page"], repo, "no heading")
        assert (repo / ".harness" / "research" / TODAY / "example-com-some-page.md").exists()

    def test_mutually_exclusive_urls_exit_2(self, repo: Path) -> None:
        result = run(
            "save_source.py",
            ["--url", "https://a.com", "--source-url", "https://b.com"],
            repo,
            "x",
        )
        assert result.returncode == 2

    def test_outside_repo_exits_1(self, tmp_path: Path) -> None:
        result = run("save_source.py", ["--source-url", "https://a.com"], tmp_path, "x")
        assert result.returncode == 1


class TestSession:
    def test_start_creates_marker_manifest_and_index(self, repo: Path) -> None:
        result = run("session.py", ["start", "--goal", "close gaps", "--id", "s1"], repo)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "session: s1"
        manifest = repo / ".harness" / "chat-provenance" / "sessions" / f"{TODAY}-s1.md"
        assert manifest.exists()
        text = manifest.read_text(encoding="utf-8")
        assert '"status": "open"' in text
        assert '"title": "close gaps"' in text
        assert '"level": "file"' in text
        log = daily_log(repo)
        assert "## session" in log
        assert "session: s1" in log
        index = (repo / ".harness" / "chat-provenance" / "index.md").read_text(encoding="utf-8")
        assert "| s1 |" in index
        assert "(open)" in index

    def test_end_appends_summary_record_and_closes(self, repo: Path) -> None:
        run("session.py", ["start", "--goal", "close gaps", "--id", "s1"], repo)
        result = run(
            "session.py",
            ["end", "s1", "--outcome", "all gaps closed", "--summary", "did the work"],
            repo,
        )
        assert result.returncode == 0, result.stderr
        log = daily_log(repo)
        assert "## summary" in log
        assert "basis: context-window" in log
        assert f"derived_from: {TODAY} seq" in log
        assert "did the work" in log
        manifest = (repo / ".harness" / "chat-provenance" / "sessions" / f"{TODAY}-s1.md").read_text(encoding="utf-8")
        assert '"status": "closed"' in manifest
        assert "all gaps closed" in manifest
        assert "did the work" in manifest
        index = (repo / ".harness" / "chat-provenance" / "index.md").read_text(encoding="utf-8")
        assert "all gaps closed" in index
        assert index.count("| s1 |") == 1

    def test_end_unknown_session_exits_1(self, repo: Path) -> None:
        assert run("session.py", ["end", "nope"], repo).returncode == 1

    def test_random_id_generated(self, repo: Path) -> None:
        result = run("session.py", ["start"], repo)
        session_id = result.stdout.strip().removeprefix("session: ")
        assert len(session_id) == 6
        assert (repo / ".harness" / "chat-provenance" / "sessions" / f"{TODAY}-{session_id}.md").exists()

    def test_rebuild_is_deterministic(self, repo: Path) -> None:
        run("session.py", ["start", "--goal", "g", "--id", "s1"], repo)
        run("session.py", ["end", "s1", "--outcome", "done", "--summary", "wrapped"], repo)
        sessions_dir = repo / ".harness" / "chat-provenance" / "sessions"
        index = repo / ".harness" / "chat-provenance" / "index.md"
        before = {p.name: p.read_bytes() for p in sessions_dir.glob("*.md")}
        before_index = index.read_bytes()
        result = run("session.py", ["rebuild"], repo)
        assert result.returncode == 0, result.stderr
        after = {p.name: p.read_bytes() for p in sessions_dir.glob("*.md")}
        assert before == after
        assert index.read_bytes() == before_index

    def test_replay_summary_basis(self, repo: Path) -> None:
        run("session.py", ["start", "--goal", "g", "--id", "s1"], repo)
        run(
            "log_entry.py",
            ["--role", "user", "--agent", "main", "--session", "s1"],
            repo,
            "do something",
        )
        result = run("session.py", ["summarize", "s1", "--replay"], repo)
        assert result.returncode == 0, result.stderr
        log = daily_log(repo)
        assert "basis: log-replay" in log
        assert "goal: g" in log


class TestRender:
    def test_narrative_structure(self, repo: Path) -> None:
        run("session.py", ["start", "--goal", "close gaps", "--id", "s1"], repo)
        run(
            "log_entry.py",
            ["--role", "user", "--agent", "main", "--session", "s1"],
            repo,
            "please do the thing",
        )
        run(
            "log_entry.py",
            ["--role", "assistant", "--agent", "main", "--session", "s1"],
            repo,
            "line\n" * 20,
        )
        run(
            "log_entry.py",
            ["--role", "assistant", "--kind", "decision", "--agent", "main", "--session", "s1"],
            repo,
            "chose: flock\nrejected: [none]\nbecause: queueing",
        )
        run(
            "log_entry.py",
            ["--role", "assistant", "--kind", "action", "--agent", "main", "--session", "s1"],
            repo,
            "tool: edit\ntitle: scripts/log_entry.py",
        )
        result = run("render.py", [], repo)
        assert result.returncode == 0, result.stderr
        out = result.stdout
        assert "## Session s1" in out
        assert "**goal:** close gaps" in out
        assert "> please do the thing" in out
        assert "more lines" in out
        assert "### Decisions" in out
        assert "flock" in out
        assert "### Actions" in out
        assert "tool: edit" in out

    def test_missing_day_exits_1(self, repo: Path) -> None:
        assert run("render.py", ["1999-01-01"], repo).returncode == 1

    def test_session_filter(self, repo: Path) -> None:
        run("session.py", ["start", "--goal", "g1", "--id", "s1"], repo)
        run("session.py", ["start", "--goal", "g2", "--id", "s2"], repo)
        result = run("render.py", ["--session", "s1"], repo)
        assert "## Session s1" in result.stdout
        assert "## Session s2" not in result.stdout


class TestClaudeHook:
    def test_user_event_logs_prompt(self, repo: Path) -> None:
        payload = json.dumps({"session_id": "cs1", "cwd": str(repo), "prompt": "hello claude"})
        result = run("claude-hook.py", ["--event", "user"], repo, payload)
        assert result.returncode == 0
        text = daily_log(repo)
        assert "## user" in text
        assert "hello claude" in text
        assert "session: cs1" in text

    def test_stop_event_logs_last_assistant_text_with_model(self, repo: Path) -> None:
        transcript = repo / "transcript.jsonl"
        records = [
            {"type": "user", "message": {"role": "user", "content": "q"}},
            {
                "type": "assistant",
                "message": {
                    "id": "msg_1",
                    "role": "assistant",
                    "model": "claude-opus",
                    "content": [{"type": "text", "text": "answer one"}],
                },
            },
            {
                "type": "assistant",
                "message": {
                    "id": "msg_2",
                    "role": "assistant",
                    "content": [{"type": "tool_use", "name": "bash", "input": {}}],
                },
            },
            {
                "type": "assistant",
                "message": {
                    "id": "msg_3",
                    "role": "assistant",
                    "model": "claude-opus",
                    "content": [{"type": "text", "text": "final answer"}],
                },
            },
        ]
        transcript.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
        payload = json.dumps({"session_id": "cs1", "cwd": str(repo), "transcript_path": str(transcript)})
        result = run("claude-hook.py", ["--event", "stop"], repo, payload)
        assert result.returncode == 0
        text = daily_log(repo)
        assert "final answer" in text
        assert "answer one" not in text
        assert "model: claude-opus" in text

    def test_stop_event_dedupes_repeated_fires(self, repo: Path) -> None:
        transcript = repo / "transcript.jsonl"
        record = {
            "type": "assistant",
            "message": {
                "id": "msg_1",
                "role": "assistant",
                "content": [{"type": "text", "text": "only once"}],
            },
        }
        transcript.write_text(json.dumps(record), encoding="utf-8")
        payload = json.dumps({"session_id": "cs1", "cwd": str(repo), "transcript_path": str(transcript)})
        run("claude-hook.py", ["--event", "stop"], repo, payload)
        run("claude-hook.py", ["--event", "stop"], repo, payload)
        assert daily_log(repo).count("only once") == 1

    def test_bad_json_exits_0(self, repo: Path) -> None:
        result = run("claude-hook.py", ["--event", "user"], repo, "not json")
        assert result.returncode == 0

    def test_outside_repo_exits_0(self, tmp_path: Path) -> None:
        payload = json.dumps({"session_id": "cs1", "cwd": str(tmp_path), "prompt": "x"})
        result = run("claude-hook.py", ["--event", "user"], tmp_path, payload)
        assert result.returncode == 0

    def test_subagent_event_uses_subagent_agent(self, repo: Path) -> None:
        transcript = repo / "sub.jsonl"
        record = {
            "type": "assistant",
            "message": {
                "id": "msg_9",
                "role": "assistant",
                "content": [{"type": "text", "text": "subagent done"}],
            },
        }
        transcript.write_text(json.dumps(record), encoding="utf-8")
        payload = json.dumps({"session_id": "cs1", "cwd": str(repo), "transcript_path": str(transcript)})
        run("claude-hook.py", ["--event", "subagent"], repo, payload)
        assert "agent: subagent" in daily_log(repo)
