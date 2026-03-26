"""
Functional tests for PatternAnalyzer: threshold logic, all analysis methods,
and compiled report output.

Run from src/intelligence/:
    python tests/test_pattern_analyzer.py
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import Database
from pattern_analysis import PatternAnalyzer, MIN_SESSIONS_FOR_ML, MAX_PAUSE_SECONDS

TEST_DB = os.path.join(os.path.dirname(__file__), "test_pattern.db")

passed = 0
failed = 0


def assert_eq(actual, expected, msg=""):
    global passed, failed
    if actual == expected:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL: {msg} — expected {expected!r}, got {actual!r}")


def assert_true(condition, msg=""):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL: {msg}")


def assert_raises(fn, msg=""):
    global passed, failed
    try:
        fn()
        failed += 1
        print(f"  FAIL: {msg} — expected exception, none raised")
    except Exception:
        passed += 1


def fresh_analyzer():
    """Returns a PatternAnalyzer backed by a clean test DB."""
    db = Database(db_path=TEST_DB)
    conn = db._get_connection()
    analyzer = PatternAnalyzer(db_conn=conn)
    return analyzer, db


def cleanup():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def seed_sessions(conn, sessions):
    """
    Insert raw session rows. Each tuple matches the sessions table column order:
    (id, start_time, end_time, duration, focused_time, events, time_away,
     look_away_time, distraction_time, phone, look_away, left_desk, app, idle,
     focus_pct, score, points, coins)
    """
    conn.executemany(
        "INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        sessions
    )
    conn.commit()


def seed_achievements(conn, achievements):
    """
    Insert achievement rows:
    (id, name, description, criteria, emoji, unlocked, unlocked_at, progress, target)
    """
    conn.executemany(
        "INSERT INTO achievements VALUES (?,?,?,?,?,?,?,?,?)",
        achievements
    )
    conn.commit()


def make_session(id, start_hour, duration_min, score, phone=0, look_away=0,
                 app=0, left_desk=0, idle=0, look_away_time=0, time_away=0,
                 date_offset_days=0):
    """Helper to build a session tuple with sensible defaults."""
    base = datetime(2026, 3, 10) - timedelta(days=date_offset_days)
    start = base.replace(hour=start_hour, minute=0, second=0)
    duration_s = duration_min * 60
    end = start + timedelta(seconds=duration_s)
    distraction_time = look_away_time + time_away
    focused_time = max(0, duration_s - distraction_time)
    focus_pct = round(focused_time / duration_s * 100, 1) if duration_s > 0 else 0
    events = phone + look_away + app + left_desk + idle
    return (
        id,
        start.strftime("%Y-%m-%dT%H:%M:%S"),
        end.strftime("%Y-%m-%dT%H:%M:%S"),
        duration_s, focused_time, events, time_away, look_away_time,
        distraction_time, phone, look_away, left_desk, app, idle,
        focus_pct, score, score, round(score * 0.1),
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_should_refresh():
    print("Test: should_refresh")
    analyzer, db = fresh_analyzer()

    # Below threshold → never refresh
    assert_eq(analyzer.should_refresh(0),  False, "0 sessions")
    assert_eq(analyzer.should_refresh(9),  False, "9 sessions")

    # Exactly at threshold
    assert_eq(analyzer.should_refresh(10), True,  "10 sessions (threshold)")

    # Every 3 after threshold: 13, 16, 19
    assert_eq(analyzer.should_refresh(11), False, "11 sessions")
    assert_eq(analyzer.should_refresh(12), False, "12 sessions")
    assert_eq(analyzer.should_refresh(13), True,  "13 sessions")
    assert_eq(analyzer.should_refresh(16), True,  "16 sessions")
    assert_eq(analyzer.should_refresh(14), False, "14 sessions")

    db.close()
    cleanup()


def test_compile_report_below_threshold():
    print("Test: compile_report below threshold")
    analyzer, db = fresh_analyzer()

    # 0 sessions
    report = analyzer.compile_report()
    assert_true("10 more sessions" in report["paragraph"], "0 sessions message")
    assert_eq(report["optimal_time"], None, "no optimal_time below threshold")

    # 7 sessions
    sessions = [make_session(i, 9, 60, 80, date_offset_days=i) for i in range(1, 8)]
    seed_sessions(db._get_connection(), sessions)
    report = analyzer.compile_report()
    assert_true("3 more sessions" in report["paragraph"], "7 sessions → need 3 more")

    db.close()
    cleanup()


def test_score_trend_improving():
    print("Test: score_trend improving")
    analyzer, db = fresh_analyzer()

    # First 5 sessions (oldest) score ~50, last 5 (newest) score ~90.
    # Delta between halves is ~40, well above the ±5 threshold → improving.
    older = [make_session(i,     9, 60, 50, date_offset_days=11 - i) for i in range(1, 6)]
    newer = [make_session(i + 5, 9, 60, 90, date_offset_days=6  - i) for i in range(1, 6)]
    sessions = older + newer
    seed_sessions(db._get_connection(), sessions)

    result = analyzer.score_trend()
    assert_true(result is not None, "score_trend returns result with 10 sessions")
    assert_eq(result["trend"], "improving", "trend is improving")
    assert_true(result["delta"] > 0, "delta is positive")

    db.close()
    cleanup()


def test_score_trend_stable():
    print("Test: score_trend stable")
    analyzer, db = fresh_analyzer()

    # All scores identical → no trend
    sessions = [make_session(i, 9, 60, 75, date_offset_days=10 - i) for i in range(1, 11)]
    seed_sessions(db._get_connection(), sessions)

    result = analyzer.score_trend()
    assert_true(result is not None, "score_trend returns result")
    assert_eq(result["trend"], "stable", "trend is stable for constant scores")

    db.close()
    cleanup()


def test_score_trend_insufficient():
    print("Test: score_trend returns None below threshold")
    analyzer, db = fresh_analyzer()

    sessions = [make_session(i, 9, 60, 80, date_offset_days=i) for i in range(1, 8)]
    seed_sessions(db._get_connection(), sessions)

    result = analyzer.score_trend()
    assert_eq(result, None, "None with < 10 sessions")

    db.close()
    cleanup()


def test_best_time_of_day():
    print("Test: best_time_of_day returns morning cluster")
    analyzer, db = fresh_analyzer()

    # 5 morning sessions (score 90) + 5 evening sessions (score 60)
    sessions = (
        [make_session(i,      9,  60, 90, date_offset_days=i) for i in range(1, 6)] +
        [make_session(i + 5, 20,  60, 60, date_offset_days=i) for i in range(1, 6)]
    )
    seed_sessions(db._get_connection(), sessions)

    result = analyzer.best_time_of_day()
    assert_true(result is not None, "best_time_of_day returns result")
    assert_eq(result["slot"], "morning", "morning cluster wins with score 90")

    db.close()
    cleanup()


def test_optimal_session_length_polynomial():
    print("Test: optimal_session_length polynomial peak")
    analyzer, db = fresh_analyzer()

    # Score peaks at ~60 min: short (20 min→50), mid (60 min→90), long (100 min→55)
    data = (
        [make_session(i,      9, 20,  50, date_offset_days=i)      for i in range(1, 5)] +
        [make_session(i + 4,  9, 60,  90, date_offset_days=i)      for i in range(1, 5)] +
        [make_session(i + 8,  9, 100, 55, date_offset_days=i)      for i in range(1, 3)]
    )
    seed_sessions(db._get_connection(), data)

    result = analyzer.optimal_session_length()
    assert_true(result is not None, "optimal_session_length returns result")
    assert_true(40 <= result["optimal_minutes"] <= 80, f"peak near 60 min, got {result['optimal_minutes']}")

    db.close()
    cleanup()


def test_distraction_correlations_phone_worst():
    print("Test: distraction_correlations identifies phone as worst")
    analyzer, db = fresh_analyzer()

    # Higher phone count → lower score; look_away constant
    sessions = [
        make_session(i, 9, 60, 90 - i * 5, phone=i, date_offset_days=i)
        for i in range(1, 11)
    ]
    seed_sessions(db._get_connection(), sessions)

    result = analyzer.distraction_correlations()
    assert_true(result is not None, "distraction_correlations returns result")
    assert_true(result["correlation"] < 0, "top distraction has negative correlation")

    db.close()
    cleanup()


def test_phone_free_streak():
    print("Test: phone_free_streak")
    analyzer, db = fresh_analyzer()

    # 3 most recent: no phone. Then 1 with phone.
    sessions = (
        [make_session(i, 9, 60, 80, phone=0, date_offset_days=i - 1) for i in range(1, 4)] +
        [make_session(4, 9, 60, 70, phone=2, date_offset_days=4)]
    )
    seed_sessions(db._get_connection(), sessions)

    result = analyzer.phone_free_streak()
    assert_eq(result["streak"], 3, "phone-free streak is 3")

    db.close()
    cleanup()


def test_achievement_proximity_ordering():
    print("Test: achievement_proximity ordering")
    analyzer, db = fresh_analyzer()

    achievements = [
        (1, "A", "desc", "crit", "🏆", 0, None, 9,  10),  # 10% remaining
        (2, "B", "desc", "crit", "🏆", 0, None, 5,  10),  # 50% remaining
        (3, "C", "desc", "crit", "🏆", 0, None, 1,  10),  # 90% remaining
        (4, "D", "desc", "crit", "🏆", 1, None, 10, 10),  # already unlocked
    ]
    seed_achievements(db._get_connection(), achievements)

    result = analyzer.achievement_proximity()
    assert_eq(len(result), 3, "top 3 achievements returned")
    assert_eq(result[0]["name"], "A", "closest achievement is A (10% remaining)")
    assert_eq(result[1]["name"], "B", "second is B (50% remaining)")
    assert_eq(result[2]["name"], "C", "third is C (90% remaining)")

    db.close()
    cleanup()


def test_pause_analysis():
    print("Test: pause_analysis detects long pauses")
    analyzer, db = fresh_analyzer()

    # Sessions 1-5: no pause (wall_clock ≈ duration)
    # Sessions 6-10: long pause (wall_clock = duration + 3600s)
    normal_sessions = [
        make_session(i, 9, 60, 85, date_offset_days=i) for i in range(1, 6)
    ]
    # Manually build long-pause sessions: set end_time 1h further than duration would suggest
    long_pause_sessions = []
    for i in range(6, 11):
        s = list(make_session(i, 9, 60, 65, date_offset_days=i))
        # Extend end_time by MAX_PAUSE_SECONDS + 600 to simulate a long pause
        end_dt = datetime.fromisoformat(s[2]) + timedelta(seconds=MAX_PAUSE_SECONDS + 600)
        s[2] = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
        long_pause_sessions.append(tuple(s))

    seed_sessions(db._get_connection(), normal_sessions + long_pause_sessions)

    result = analyzer.pause_analysis()
    assert_true(result is not None, "pause_analysis returns result")
    assert_eq(result["long_pause_sessions"], 5, "5 long-pause sessions detected")
    assert_true(
        result["avg_score_with_long_pause"] < result["avg_score_without"],
        "long-pause sessions score lower"
    )

    db.close()
    cleanup()


def test_compile_report_full_paragraph():
    print("Test: compile_report full paragraph with 10+ sessions")
    analyzer, db = fresh_analyzer()

    # 10 sessions with variety
    sessions = (
        [make_session(i,      9,  60, 85, phone=0,        date_offset_days=i) for i in range(1, 6)] +
        [make_session(i + 5, 20,  40, 60, phone=i - 4,    date_offset_days=i) for i in range(1, 6)]
    )
    seed_sessions(db._get_connection(), sessions)

    report = analyzer.compile_report()
    assert_true(isinstance(report["paragraph"], str), "paragraph is a string")
    assert_true(len(report["paragraph"]) > 20,        "paragraph is non-trivial")
    assert_true("Complete" not in report["paragraph"], "no threshold message in full report")

    db.close()
    cleanup()


def test_compile_report_always_keys():
    print("Test: compile_report always returns consistency, phone_streak, achievements")
    analyzer, db = fresh_analyzer()

    report = analyzer.compile_report()
    assert_true("consistency"  in report, "consistency always present")
    assert_true("phone_streak" in report, "phone_streak always present")
    assert_true("achievements" in report, "achievements always present")

    db.close()
    cleanup()


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cleanup()

    test_should_refresh()
    test_compile_report_below_threshold()
    test_score_trend_improving()
    test_score_trend_stable()
    test_score_trend_insufficient()
    test_best_time_of_day()
    test_optimal_session_length_polynomial()
    test_distraction_correlations_phone_worst()
    test_phone_free_streak()
    test_achievement_proximity_ordering()
    test_pause_analysis()
    test_compile_report_full_paragraph()
    test_compile_report_always_keys()

    cleanup()

    print()
    print(f"Results: {passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)
    else:
        print("All tests passed!")
