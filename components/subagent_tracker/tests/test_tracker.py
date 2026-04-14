"""
Tests for subagent_tracker tracker.py
"""

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import util  # noqa: E402
import tracker  # noqa: E402

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def patch_sessions_dir(tmp_path, monkeypatch):
    """Redirect SESSIONS_DIR to a temp directory for all tests."""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    monkeypatch.setattr(util, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(tracker, "SESSIONS_DIR", sessions_dir, raising=False)
    return sessions_dir


@pytest.fixture()
def tasks_file():
    return str(FIXTURES_DIR / "sample_tasks.json")


@pytest.fixture()
def context_file(tmp_path):
    ctx = {"project": "test-project", "repo": "https://github.com/test/test"}
    f = tmp_path / "ctx.json"
    f.write_text(json.dumps(ctx))
    return str(f)


@pytest.fixture()
def initialized_session(tasks_file):
    """Run `init` and return the session_id."""

    class Args:
        session = "test-dispatch-001"
        tasks = tasks_file
        context = None

    tracker.cmd_init(Args())
    return "test-dispatch-001"


@pytest.fixture()
def initialized_session_with_ctx(tasks_file, context_file):
    """Run `init` with global context and return the session_id."""

    class Args:
        session = "test-dispatch-ctx"
        tasks = tasks_file
        context = context_file

    tracker.cmd_init(Args())
    return "test-dispatch-ctx"


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


class TestInit:
    def test_init_creates_session_file(self, tasks_file, patch_sessions_dir):
        class Args:
            session = "init-test"
            tasks = tasks_file
            context = None

        tracker.cmd_init(Args())
        assert (patch_sessions_dir / "init-test.json").exists()

    def test_init_correct_task_count(self, tasks_file, capsys):
        class Args:
            session = "init-count"
            tasks = tasks_file
            context = None

        tracker.cmd_init(Args())
        out = json.loads(capsys.readouterr().out)
        assert out["total_tasks"] == 3
        assert out["session_id"] == "init-count"

    def test_init_with_global_context(self, tasks_file, context_file, capsys):
        class Args:
            session = "init-ctx"
            tasks = tasks_file
            context = context_file

        tracker.cmd_init(Args())
        out = json.loads(capsys.readouterr().out)
        assert "project" in out["global_context_keys"]
        assert "repo" in out["global_context_keys"]

    def test_init_stores_global_context_in_state(
        self, tasks_file, context_file, patch_sessions_dir
    ):
        class Args:
            session = "init-ctx-check"
            tasks = tasks_file
            context = context_file

        tracker.cmd_init(Args())
        state = util.load_state("init-ctx-check")
        assert state["global_context"]["project"] == "test-project"

    def test_init_duplicate_session_errors(self, tasks_file, capsys):
        class Args:
            session = "init-dup"
            tasks = tasks_file
            context = None

        tracker.cmd_init(Args())
        capsys.readouterr()

        with pytest.raises(SystemExit) as exc:
            tracker.cmd_init(Args())
        assert exc.value.code == 1
        out = json.loads(capsys.readouterr().out)
        assert "error" in out

    def test_init_missing_id_field_errors(self, tmp_path, capsys):
        bad = tmp_path / "bad.json"
        bad.write_text('[{"description": "no id here"}]')

        class Args:
            session = "init-bad-id"
            tasks = str(bad)
            context = None

        with pytest.raises(SystemExit) as exc:
            tracker.cmd_init(Args())
        assert exc.value.code == 1
        out = json.loads(capsys.readouterr().out)
        assert "error" in out

    def test_init_missing_description_field_errors(self, tmp_path, capsys):
        bad = tmp_path / "bad.json"
        bad.write_text('[{"id": "x"}]')

        class Args:
            session = "init-bad-desc"
            tasks = str(bad)
            context = None

        with pytest.raises(SystemExit) as exc:
            tracker.cmd_init(Args())
        assert exc.value.code == 1

    def test_init_empty_tasks_errors(self, tmp_path, capsys):
        empty = tmp_path / "empty.json"
        empty.write_text("[]")

        class Args:
            session = "init-empty"
            tasks = str(empty)
            context = None

        with pytest.raises(SystemExit) as exc:
            tracker.cmd_init(Args())
        assert exc.value.code == 1


# ---------------------------------------------------------------------------
# next
# ---------------------------------------------------------------------------


class TestNext:
    def test_next_returns_first_task(self, initialized_session, capsys):
        class Args:
            session = initialized_session

        tracker.cmd_next(Args())
        out = json.loads(capsys.readouterr().out)
        assert out["task_id"] == "task-alpha"
        assert "todos" in out
        assert "context" in out
        assert "global" in out["context"]
        assert "task" in out["context"]

    def test_next_is_idempotent(self, initialized_session, capsys):
        """Calling next twice without reporting should return the same task."""

        class Args:
            session = initialized_session

        tracker.cmd_next(Args())
        first = json.loads(capsys.readouterr().out)

        tracker.cmd_next(Args())
        second = json.loads(capsys.readouterr().out)

        assert first["task_id"] == second["task_id"]

    def test_next_advances_after_report(self, initialized_session, capsys):
        """After reporting task 1, next should return task 2."""

        class NextArgs:
            session = initialized_session

        tracker.cmd_next(NextArgs())
        first = json.loads(capsys.readouterr().out)
        task_id = first["task_id"]

        class ReportArgs:
            session = initialized_session
            task = task_id
            result = None

        tracker.cmd_report(ReportArgs())
        capsys.readouterr()

        tracker.cmd_next(NextArgs())
        second = json.loads(capsys.readouterr().out)
        assert second["task_id"] != task_id

    def test_next_includes_global_context(
        self, initialized_session_with_ctx, capsys
    ):
        class Args:
            session = initialized_session_with_ctx

        tracker.cmd_next(Args())
        out = json.loads(capsys.readouterr().out)
        assert out["context"]["global"]["project"] == "test-project"

    def test_next_includes_task_context(self, initialized_session, capsys):
        class Args:
            session = initialized_session

        tracker.cmd_next(Args())
        out = json.loads(capsys.readouterr().out)
        assert out["context"]["task"]["module"] == "alpha"

    def test_next_exits_2_when_all_done(self, initialized_session, capsys):
        state = util.load_state(initialized_session)
        for t in state["tasks"]:
            t["status"] = "done"
            t["completed_at"] = util._now()
        util.save_state(state)
        capsys.readouterr()

        class Args:
            session = initialized_session

        with pytest.raises(SystemExit) as exc:
            tracker.cmd_next(Args())
        assert exc.value.code == 2

    def test_next_task_without_todos(self, tmp_path, patch_sessions_dir, capsys):
        """Tasks without todos field should dispatch with empty todos list."""
        tasks_no_todos = tmp_path / "simple.json"
        tasks_no_todos.write_text(
            json.dumps([{"id": "t1", "description": "simple task"}])
        )

        class InitArgs:
            session = "no-todos"
            tasks = str(tasks_no_todos)
            context = None

        tracker.cmd_init(InitArgs())
        capsys.readouterr()

        class NextArgs:
            session = "no-todos"

        tracker.cmd_next(NextArgs())
        out = json.loads(capsys.readouterr().out)
        assert out["todos"] == []
        assert out["agent"] is None


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


class TestReport:
    def test_report_marks_task_done(self, initialized_session, capsys):
        # Dispatch first
        class NextArgs:
            session = initialized_session

        tracker.cmd_next(NextArgs())
        task_id = json.loads(capsys.readouterr().out)["task_id"]

        class ReportArgs:
            session = initialized_session
            task = task_id
            result = None

        tracker.cmd_report(ReportArgs())
        capsys.readouterr()

        state = util.load_state(initialized_session)
        task = next(t for t in state["tasks"] if t["id"] == task_id)
        assert task["status"] == "done"
        assert task["completed_at"] is not None

    def test_report_stores_json_result(self, initialized_session, capsys):
        class NextArgs:
            session = initialized_session

        tracker.cmd_next(NextArgs())
        task_id = json.loads(capsys.readouterr().out)["task_id"]

        class ReportArgs:
            session = initialized_session
            task = task_id
            result = '{"files": ["foo.py"]}'

        tracker.cmd_report(ReportArgs())
        capsys.readouterr()

        state = util.load_state(initialized_session)
        task = next(t for t in state["tasks"] if t["id"] == task_id)
        assert task["result"] == {"files": ["foo.py"]}

    def test_report_idempotent_for_done_task(self, initialized_session, capsys):
        class NextArgs:
            session = initialized_session

        tracker.cmd_next(NextArgs())
        task_id = json.loads(capsys.readouterr().out)["task_id"]

        class ReportArgs:
            session = initialized_session
            task = task_id
            result = None

        tracker.cmd_report(ReportArgs())
        capsys.readouterr()
        tracker.cmd_report(ReportArgs())
        out = json.loads(capsys.readouterr().out)
        assert "already" in out["message"]

    def test_report_unknown_task_errors(self, initialized_session, capsys):
        class ReportArgs:
            session = initialized_session
            task = "nonexistent"
            result = None

        with pytest.raises(SystemExit) as exc:
            tracker.cmd_report(ReportArgs())
        assert exc.value.code == 1


# ---------------------------------------------------------------------------
# fail
# ---------------------------------------------------------------------------


class TestFail:
    def test_fail_marks_task_failed(self, initialized_session, capsys):
        class Args:
            session = initialized_session
            task = "task-alpha"
            error = "something went wrong"

        tracker.cmd_fail(Args())
        capsys.readouterr()

        state = util.load_state(initialized_session)
        task = next(t for t in state["tasks"] if t["id"] == "task-alpha")
        assert task["status"] == "failed"
        assert task["error"] == "something went wrong"

    def test_fail_unknown_task_errors(self, initialized_session, capsys):
        class Args:
            session = initialized_session
            task = "nope"
            error = None

        with pytest.raises(SystemExit) as exc:
            tracker.cmd_fail(Args())
        assert exc.value.code == 1


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


class TestStatus:
    def test_status_reflects_initial_state(self, initialized_session, capsys):
        class Args:
            session = initialized_session

        tracker.cmd_status(Args())
        out = json.loads(capsys.readouterr().out)
        assert out["tasks"]["total"] == 3
        assert out["tasks"]["pending"] == 3
        assert out["tasks"]["done"] == 0

    def test_status_after_dispatch_and_report(self, initialized_session, capsys):
        class NextArgs:
            session = initialized_session

        tracker.cmd_next(NextArgs())
        task_id = json.loads(capsys.readouterr().out)["task_id"]

        class ReportArgs:
            session = initialized_session
            task = task_id
            result = None

        tracker.cmd_report(ReportArgs())
        capsys.readouterr()

        class StatusArgs:
            session = initialized_session

        tracker.cmd_status(StatusArgs())
        out = json.loads(capsys.readouterr().out)
        assert out["tasks"]["done"] == 1
        assert out["tasks"]["pending"] == 2


# ---------------------------------------------------------------------------
# done
# ---------------------------------------------------------------------------


class TestDone:
    def test_done_returns_false_when_pending(self, initialized_session, capsys):
        class Args:
            session = initialized_session

        with pytest.raises(SystemExit) as exc:
            tracker.cmd_done(Args())
        assert exc.value.code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["done"] is False

    def test_done_returns_true_when_all_settled(self, initialized_session, capsys):
        state = util.load_state(initialized_session)
        for t in state["tasks"]:
            t["status"] = "done"
            t["completed_at"] = util._now()
        util.save_state(state)
        capsys.readouterr()

        class Args:
            session = initialized_session

        with pytest.raises(SystemExit) as exc:
            tracker.cmd_done(Args())
        assert exc.value.code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["done"] is True


# ---------------------------------------------------------------------------
# results
# ---------------------------------------------------------------------------


class TestResults:
    def test_results_structure(self, initialized_session, capsys):
        class Args:
            session = initialized_session

        tracker.cmd_results(Args())
        out = json.loads(capsys.readouterr().out)
        assert out["session_id"] == initialized_session
        assert len(out["results"]) == 3
        keys = out["results"][0].keys()
        for field in ("task_id", "description", "agent", "status", "result", "error"):
            assert field in keys

    def test_results_captures_stored_result(self, initialized_session, capsys):
        class NextArgs:
            session = initialized_session

        tracker.cmd_next(NextArgs())
        task_id = json.loads(capsys.readouterr().out)["task_id"]

        class ReportArgs:
            session = initialized_session
            task = task_id
            result = '{"output": "ok"}'

        tracker.cmd_report(ReportArgs())
        capsys.readouterr()

        class ResultsArgs:
            session = initialized_session

        tracker.cmd_results(ResultsArgs())
        out = json.loads(capsys.readouterr().out)
        done_task = next(r for r in out["results"] if r["task_id"] == task_id)
        assert done_task["result"] == {"output": "ok"}


# ---------------------------------------------------------------------------
# list / cleanup
# ---------------------------------------------------------------------------


class TestList:
    def test_list_returns_dispatcher_sessions(self, initialized_session, capsys):
        class Args:
            pass

        tracker.cmd_list(Args())
        out = json.loads(capsys.readouterr().out)
        assert out["total"] >= 1
        ids = [s["session_id"] for s in out["sessions"]]
        assert initialized_session in ids


class TestCleanup:
    def test_cleanup_removes_old_session(self, initialized_session, capsys):
        # Manually age the session by writing directly (save_state would overwrite updated_at)
        state = util.load_state(initialized_session)
        state["updated_at"] = "2020-01-01T00:00:00+00:00"
        path = util.session_path(initialized_session)
        import json as _json
        path.write_text(_json.dumps(state))
        capsys.readouterr()

        class Args:
            older_than = 7

        tracker.cmd_cleanup(Args())
        out = json.loads(capsys.readouterr().out)
        assert initialized_session in out["removed"]

    def test_cleanup_keeps_recent_session(self, initialized_session, capsys):
        class Args:
            older_than = 7

        tracker.cmd_cleanup(Args())
        out = json.loads(capsys.readouterr().out)
        assert initialized_session not in out["removed"]
