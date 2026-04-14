"""
Tests for batch-planner batch_manager.py
"""

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import util  # noqa: E402 — must come after sys.path insert
import batch_manager  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def patch_sessions_dir(tmp_path, monkeypatch):
    """Redirect SESSIONS_DIR to a temp directory for all tests."""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    monkeypatch.setattr(util, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(batch_manager, "SESSIONS_DIR", sessions_dir, raising=False)
    return sessions_dir


@pytest.fixture()
def sample_items_file():
    return str(FIXTURES_DIR / "sample_items.json")


@pytest.fixture()
def planned_session(sample_items_file):
    """Run `plan` and return the session_id."""

    class Args:
        session = "test-session-001"
        items = sample_items_file
        batch_size = 3

    batch_manager.cmd_plan(Args())
    return "test-session-001"


# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------


class TestPlan:
    def test_plan_creates_session_file(self, sample_items_file, patch_sessions_dir):
        class Args:
            session = "plan-test"
            items = sample_items_file
            batch_size = 5

        batch_manager.cmd_plan(Args())
        assert (patch_sessions_dir / "plan-test.json").exists()

    def test_plan_correct_batch_count(
        self, sample_items_file, patch_sessions_dir, capsys
    ):
        class Args:
            session = "plan-batch"
            items = sample_items_file
            batch_size = 3  # 7 items / 3 = 3 batches

        batch_manager.cmd_plan(Args())
        out = json.loads(capsys.readouterr().out)
        assert out["total_items"] == 7
        assert out["total_batches"] == 3
        assert out["batch_size"] == 3

    def test_plan_empty_items_errors(self, tmp_path, capsys):
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("[]")

        class Args:
            session = "plan-empty"
            items = str(empty_file)
            batch_size = 5

        with pytest.raises(SystemExit) as exc:
            batch_manager.cmd_plan(Args())
        assert exc.value.code == 1
        out = json.loads(capsys.readouterr().out)
        assert "error" in out

    def test_plan_missing_id_errors(self, tmp_path, capsys):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text('[{"name": "no-id"}]')

        class Args:
            session = "plan-bad"
            items = str(bad_file)
            batch_size = 5

        with pytest.raises(SystemExit) as exc:
            batch_manager.cmd_plan(Args())
        assert exc.value.code == 1

    def test_plan_duplicate_session_errors(self, sample_items_file, capsys):
        class Args:
            session = "plan-dup"
            items = sample_items_file
            batch_size = 5

        batch_manager.cmd_plan(Args())
        capsys.readouterr()  # flush

        with pytest.raises(SystemExit) as exc:
            batch_manager.cmd_plan(Args())
        assert exc.value.code == 1
        out = json.loads(capsys.readouterr().out)
        assert "error" in out


# ---------------------------------------------------------------------------
# next
# ---------------------------------------------------------------------------


class TestNext:
    def test_next_returns_first_batch(self, planned_session, capsys):
        class Args:
            session = planned_session

        batch_manager.cmd_next(Args())
        out = json.loads(capsys.readouterr().out)
        assert out["batch_num"] == 1
        assert len(out["items"]) == 3  # batch_size=3

    def test_next_is_idempotent(self, planned_session, capsys):
        """Calling next twice without completing should return same batch."""

        class Args:
            session = planned_session

        batch_manager.cmd_next(Args())
        first = json.loads(capsys.readouterr().out)

        batch_manager.cmd_next(Args())
        second = json.loads(capsys.readouterr().out)

        assert first["batch_num"] == second["batch_num"]
        assert [i["id"] for i in first["items"]] == [i["id"] for i in second["items"]]

    def test_next_advances_after_completion(self, planned_session, capsys):
        """After completing all items in batch 1, next should return batch 2."""

        class NextArgs:
            session = planned_session

        batch_manager.cmd_next(NextArgs())
        batch1 = json.loads(capsys.readouterr().out)

        for item in batch1["items"]:
            item_id = item["id"]

            class CompleteArgs:
                session = planned_session
                item = item_id

            batch_manager.cmd_complete(CompleteArgs())
            capsys.readouterr()

        # Now next should return batch 2
        batch_manager.cmd_next(NextArgs())
        batch2 = json.loads(capsys.readouterr().out)
        assert batch2["batch_num"] == 2

    def test_next_exits_2_when_no_batches(self, planned_session, capsys):
        """When all batches are done, exit with code 2."""
        state = util.load_state(planned_session)
        # Mark all items done
        for item in state["items"]:
            item["status"] = "done"
            item["completed_at"] = util._now()
        for batch in state["batches"]:
            batch["status"] = "done"
        util.save_state(state)
        capsys.readouterr()

        class Args:
            session = planned_session

        with pytest.raises(SystemExit) as exc:
            batch_manager.cmd_next(Args())
        assert exc.value.code == 2


# ---------------------------------------------------------------------------
# complete / fail
# ---------------------------------------------------------------------------


class TestCompleteAndFail:
    def _start_batch(self, session_id):
        class Args:
            session = session_id

        batch_manager.cmd_next(Args())

    def test_complete_marks_item_done(self, planned_session, capsys):
        self._start_batch(planned_session)
        capsys.readouterr()

        class Args:
            session = planned_session
            item = "item-alpha"

        batch_manager.cmd_complete(Args())
        out = json.loads(capsys.readouterr().out)
        assert "done" in out["message"]

        state = util.load_state(planned_session)
        item = next(i for i in state["items"] if i["id"] == "item-alpha")
        assert item["status"] == "done"
        assert item["completed_at"] is not None

    def test_complete_idempotent(self, planned_session, capsys):
        self._start_batch(planned_session)
        capsys.readouterr()

        class Args:
            session = planned_session
            item = "item-alpha"

        batch_manager.cmd_complete(Args())
        capsys.readouterr()
        batch_manager.cmd_complete(Args())
        out = json.loads(capsys.readouterr().out)
        assert "already" in out["message"]

    def test_fail_marks_item_failed(self, planned_session, capsys):
        self._start_batch(planned_session)
        capsys.readouterr()

        class Args:
            session = planned_session
            item = "item-beta"
            error = "Timeout error"

        batch_manager.cmd_fail(Args())
        out = json.loads(capsys.readouterr().out)
        assert "failed" in out["message"]

        state = util.load_state(planned_session)
        item = next(i for i in state["items"] if i["id"] == "item-beta")
        assert item["status"] == "failed"
        assert item["error"] == "Timeout error"

    def test_fail_unknown_item_errors(self, planned_session, capsys):
        class Args:
            session = planned_session
            item = "nonexistent-item"
            error = None

        with pytest.raises(SystemExit) as exc:
            batch_manager.cmd_fail(Args())
        assert exc.value.code == 1

    def test_batch_auto_closes_when_all_settled(self, planned_session, capsys):
        self._start_batch(planned_session)
        capsys.readouterr()

        # Complete all 3 items in batch 1
        for item_id in ["item-alpha", "item-beta", "item-gamma"]:

            class Args:
                session = planned_session
                item = item_id

            batch_manager.cmd_complete(Args())
            capsys.readouterr()

        state = util.load_state(planned_session)
        batch1 = next(b for b in state["batches"] if b["batch_num"] == 1)
        assert batch1["status"] == "done"


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


class TestStatus:
    def test_status_output_shape(self, planned_session, capsys):
        class Args:
            session = planned_session

        batch_manager.cmd_status(Args())
        out = json.loads(capsys.readouterr().out)
        assert out["session_id"] == planned_session
        assert "items" in out
        assert out["items"]["total"] == 7
        assert out["items"]["pending"] == 7
        assert out["items"]["done"] == 0
        assert "batches" in out


# ---------------------------------------------------------------------------
# done
# ---------------------------------------------------------------------------


class TestDone:
    def test_done_exits_1_when_pending(self, planned_session, capsys):
        class Args:
            session = planned_session

        with pytest.raises(SystemExit) as exc:
            batch_manager.cmd_done(Args())
        assert exc.value.code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["done"] is False

    def test_done_exits_0_when_all_complete(self, planned_session, capsys):
        state = util.load_state(planned_session)
        for item in state["items"]:
            item["status"] = "done"
            item["completed_at"] = util._now()
        for batch in state["batches"]:
            batch["status"] = "done"
        util.save_state(state)
        capsys.readouterr()

        class Args:
            session = planned_session

        with pytest.raises(SystemExit) as exc:
            batch_manager.cmd_done(Args())
        assert exc.value.code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["done"] is True


# ---------------------------------------------------------------------------
# resume
# ---------------------------------------------------------------------------


class TestResume:
    def test_resume_read_only(self, planned_session, capsys):
        class Args:
            session = planned_session

        batch_manager.cmd_resume(Args())
        out = json.loads(capsys.readouterr().out)

        # Should list all 7 pending items
        assert out["total_pending"] == 7
        assert len(out["pending_items"]) == 7

        # State should not have changed
        state = util.load_state(planned_session)
        assert all(i["status"] == "pending" for i in state["items"])


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestList:
    def test_list_empty(self, capsys):
        batch_manager.cmd_list(None)
        out = json.loads(capsys.readouterr().out)
        assert out["total"] == 0
        assert out["sessions"] == []

    def test_list_shows_sessions(self, planned_session, capsys):
        batch_manager.cmd_list(None)
        out = json.loads(capsys.readouterr().out)
        assert out["total"] == 1
        assert out["sessions"][0]["session_id"] == planned_session


# ---------------------------------------------------------------------------
# cleanup
# ---------------------------------------------------------------------------


class TestCleanup:
    def test_cleanup_removes_old_sessions(self, planned_session, capsys):
        # Force the session to appear old by backdating updated_at
        from datetime import timedelta

        state = util.load_state(planned_session)
        old_time = (
            __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            - timedelta(days=10)
        ).isoformat()
        state["updated_at"] = old_time
        state["created_at"] = old_time
        util.save_state(state)
        # Undo the auto-update from save_state
        path = util.session_path(planned_session)
        raw = json.loads(path.read_text())
        raw["updated_at"] = old_time
        path.write_text(json.dumps(raw))
        capsys.readouterr()

        class Args:
            older_than = 7

        batch_manager.cmd_cleanup(Args())
        out = json.loads(capsys.readouterr().out)
        assert out["count"] == 1
        assert planned_session in out["removed"]

    def test_cleanup_keeps_recent_sessions(self, planned_session, capsys):
        class Args:
            older_than = 7

        batch_manager.cmd_cleanup(Args())
        out = json.loads(capsys.readouterr().out)
        assert out["count"] == 0
