"""
Pattern analysis for study sessions.
Analyzes historical session data to identify optimal study times,
session lengths, distraction patterns, and score trends.

Requires >= 10 completed sessions before ML feedback is generated.
Refreshes every 3 sessions after the threshold is reached.

Run from src/intelligence/:
    from pattern_analysis import PatternAnalyzer
"""

from datetime import datetime, date, timedelta

import numpy as np                              # array math, moving average, correlation
from sklearn.cluster import KMeans              # groups sessions by study hour
from sklearn.ensemble import RandomForestRegressor  # ranks which factors affect score most

from database import get_database               # shared DB connection singleton
from session_manager import DistractionType     # enum of all distraction types

# ── Constants ────────────────────────────────────────────────────────────────

MIN_SESSION_SECONDS = 300    # sessions shorter than 5 min are excluded from all analysis
MAX_PAUSE_SECONDS   = 1800   # pauses longer than 30 min are flagged in pause_analysis()
MIN_SESSIONS_FOR_ML = 10     # minimum sessions before ML feedback is shown to the user
REFRESH_EVERY       = 3      # after the threshold, feedback only recomputes every N sessions

# Human-readable time slot labels used when building the feedback paragraph
_TIME_SLOT_LABELS = {
    "morning":   "morning (6am–12pm)",
    "afternoon": "afternoon (12–5pm)",
    "evening":   "evening (5–9pm)",
    "night":     "night (9pm–6am)",
}

# Maps internal RandomForest feature names to user-friendly strings for the paragraph
_FEATURE_READABLE = {
    "hour_of_day":      "time of day",
    "duration_minutes": "session length",
    "day_of_week":      "day of week",
    "phone_count":      "phone usage",
    "look_away_count":  "looking away",
    "app_count":        "app switching",
    "left_desk_count":  "leaving your desk",
    "idle_count":       "idle time",
}


# ── Module-level helpers ──────────────────────────────────────────────────────

def _hour_to_slot(hour: int) -> str:
    """Maps a 0–23 hour to one of four named time slots."""
    if 6 <= hour < 12:      # 06:00 – 11:59
        return "morning"
    elif 12 <= hour < 17:   # 12:00 – 16:59
        return "afternoon"
    elif 17 <= hour < 21:   # 17:00 – 20:59
        return "evening"
    else:                   # 21:00 – 05:59
        return "night"


def _distraction_label(dtype: DistractionType) -> str:
    """Converts a DistractionType enum to a plain word. e.g. PHONE_DISTRACTION → 'phone'"""
    return dtype.value.replace("_distraction", "").replace("_", " ")


# ── PatternAnalyzer ───────────────────────────────────────────────────────────

class PatternAnalyzer:
    """
    Analyzes completed session data to generate study pattern insights.

    All analysis methods return None when there is insufficient data
    (below MIN_SESSIONS_FOR_ML). compile_report() skips None results
    gracefully and always returns a usable paragraph.
    """

    def __init__(self, db_conn=None):
        # Accept an optional connection so tests can inject a test DB
        # without affecting real data.db (same injection pattern as SessionManager)
        self.db = db_conn or get_database()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_completed_sessions(self, limit=None):
        """Returns completed sessions as a list of sqlite3.Row objects, newest first."""
        cursor = self.db.cursor()
        query = """
            SELECT * FROM sessions
            WHERE end_time IS NOT NULL      -- only finished sessions
              AND duration >= ?             -- exclude sessions shorter than MIN_SESSION_SECONDS
            ORDER BY start_time DESC        -- newest first so callers can slice the most recent N
        """
        if limit:
            query += f" LIMIT {int(limit)}"    # int() cast prevents SQL injection via f-string
        cursor.execute(query, (MIN_SESSION_SECONDS,))   # parameterised to avoid SQL injection
        return cursor.fetchall()                        # returns list of sqlite3.Row (dict-like)

    def _session_count(self) -> int:
        """Returns the number of valid completed sessions (same filter as _get_completed_sessions)."""
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS n FROM sessions WHERE end_time IS NOT NULL AND duration >= ?",
            (MIN_SESSION_SECONDS,)
        )
        return cursor.fetchone()["n"]   # sqlite3.Row supports column access by name

    # ── Threshold / refresh logic ─────────────────────────────────────────────

    def should_refresh(self, total_sessions: int) -> bool:
        """
        Returns True when the report should be recomputed.
        Fires at session 10 (first unlock) and every 3 sessions after (13, 16, 19…).
        Avoids retraining the RandomForest on every single session end.
        """
        if total_sessions < MIN_SESSIONS_FOR_ML:
            return False    # not enough data yet — never refresh
        sessions_past_threshold = total_sessions - MIN_SESSIONS_FOR_ML  # how many past the unlock point
        return sessions_past_threshold % REFRESH_EVERY == 0             # True on multiples of 3

    # ── Analysis methods ──────────────────────────────────────────────────────

    def score_trend(self):
        """
        Smooths the score time series with a moving average (window=5) to remove
        session-to-session noise, then compares the smoothed recent 5 vs previous 5.
        Returns None if fewer than MIN_SESSIONS_FOR_ML sessions exist.
        """
        sessions = self._get_completed_sessions(limit=MIN_SESSIONS_FOR_ML)  # only need last N
        if len(sessions) < MIN_SESSIONS_FOR_ML:
            return None     # not enough data to detect a trend

        scores   = np.array([s["score"] for s in sessions], dtype=float)  # extract score column
        scores   = scores[::-1]     # reverse from newest-first to chronological order for the time series

        window   = 5                # average each score with its 4 neighbours to smooth noise
        smoothed = np.convolve(scores, np.ones(window) / window, mode="valid")
        # np.convolve with mode="valid" only returns points where the window fully overlaps
        # result length = len(scores) - window + 1

        recent_avg   = float(np.mean(smoothed[-5:]))    # average of the 5 most recent smoothed scores
        previous_avg = float(np.mean(smoothed[:5]))     # average of the 5 earliest smoothed scores
        delta        = round(recent_avg - previous_avg, 1)  # positive = improving, negative = declining

        if delta > 5:       # more than 5 points up = meaningful improvement
            trend = "improving"
        elif delta < -5:    # more than 5 points down = meaningful decline
            trend = "declining"
        else:               # within ±5 = normal variation, not a real trend
            trend = "stable"

        return {"trend": trend, "recent_avg": round(recent_avg, 1), "delta": delta}

    def best_time_of_day(self):
        """
        Clusters sessions by start hour using KMeans (k=4), then returns the cluster
        with the highest average score. Uses KMeans instead of fixed hour bins so
        clusters adapt to when the user actually studies.
        Returns None if fewer than MIN_SESSIONS_FOR_ML sessions exist.
        """
        sessions = self._get_completed_sessions()       # use all sessions for clustering
        if len(sessions) < MIN_SESSIONS_FOR_ML:
            return None

        # Extract the hour each session started (0–23) and the score
        hours  = np.array([datetime.fromisoformat(s["start_time"]).hour for s in sessions])
        scores = np.array([s["score"] for s in sessions], dtype=float)

        n_clusters = min(4, len(sessions))  # cap at session count to prevent KMeans convergence warning

        km     = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        labels = km.fit_predict(hours.reshape(-1, 1))   # reshape to (n, 1) — KMeans expects 2D input
        # labels is an array of cluster IDs (0 to n_clusters-1), one per session

        best_cluster, best_avg = None, -1
        for cluster_id in range(n_clusters):
            mask = labels == cluster_id             # boolean mask selecting only sessions in this cluster
            if not mask.any():                      # skip clusters with no members (can happen if capped)
                continue
            avg_score    = float(np.mean(scores[mask]))                         # avg score for this cluster
            cluster_hour = int(round(km.cluster_centers_[cluster_id][0]))       # centroid hour (0–23)
            if avg_score > best_avg:    # keep track of the best-scoring cluster
                best_avg     = avg_score
                best_cluster = {
                    "slot":          _hour_to_slot(cluster_hour),   # "morning", "afternoon", etc.
                    "centroid_hour": cluster_hour,                  # e.g. 10 for a morning cluster
                    "avg_score":     round(avg_score, 1),
                    "session_count": int(mask.sum()),               # number of sessions in this cluster
                }

        return best_cluster

    def optimal_session_length(self):
        """
        Fits a degree-2 polynomial (parabola) to duration vs score.
        The vertex of a downward-opening parabola is the predicted peak duration.
        Falls back to the best observed session if the curve opens upward (no peak exists).
        Returns None if fewer than MIN_SESSIONS_FOR_ML sessions exist.
        """
        sessions = self._get_completed_sessions()
        if len(sessions) < MIN_SESSIONS_FOR_ML:
            return None

        durations = np.array([s["duration"] / 60.0 for s in sessions])     # convert seconds → minutes
        scores    = np.array([s["score"] for s in sessions], dtype=float)

        a, b, c = np.polyfit(durations, scores, deg=2)  # fit ax² + bx + c to the data
        # a: curvature (negative = peak exists, positive = no peak)
        # b: slope at x=0
        # c: y-intercept

        if a >= 0:
            # Parabola opens upward — no maximum, just use the session with the best actual score
            best_idx = int(np.argmax(scores))   # index of the highest-scoring session
            return {
                "optimal_minutes": round(float(durations[best_idx])),   # that session's duration
                "predicted_score": round(float(scores[best_idx]), 1),
                "method":          "observed",  # flag so tests know which code path ran
            }

        # Vertex formula for ax² + bx + c: x_peak = -b / (2a)
        optimal_minutes = round(-b / (2 * a))                                       # peak duration in minutes
        predicted_score = float(a * optimal_minutes**2 + b * optimal_minutes + c)  # plug back into polynomial
        return {
            "optimal_minutes": optimal_minutes,
            "predicted_score": round(min(100.0, max(0.0, predicted_score)), 1),  # clamp to 0–100
            "method":          "polynomial",
        }

    def distraction_correlations(self):
        """
        Computes Pearson correlation between each distraction metric and session score.
        The most negative correlation is the distraction that most consistently drags score down.
        Returns None if fewer than MIN_SESSIONS_FOR_ML sessions exist or all columns are constant.
        """
        sessions = self._get_completed_sessions()
        if len(sessions) < MIN_SESSIONS_FOR_ML:
            return None

        scores = np.array([s["score"] for s in sessions], dtype=float)

        # Prefer time-based columns (seconds distracted) over counts where available —
        # a single 10-minute phone call is more impactful than ten 1-second glances
        column_map = {
            DistractionType.PHONE_DISTRACTION:     "phone_distractions",    # no time column; use count
            DistractionType.LOOK_AWAY_DISTRACTION: "look_away_time",        # total seconds looking away
            DistractionType.LEFT_DESK_DISTRACTION: "time_away",             # total seconds away from desk
            DistractionType.APP_DISTRACTION:       "app_distractions",      # no time column; use count
            DistractionType.IDLE_DISTRACTION:      "idle_distractions",     # no time column; use count
        }

        results = {}
        for dtype, col in column_map.items():
            values = np.array([s[col] for s in sessions], dtype=float)  # extract column as array
            if values.std() == 0:
                continue    # skip constant columns (user never had this distraction) — corrcoef would be NaN
            corr = float(np.corrcoef(values, scores)[0, 1])
            # np.corrcoef returns a 2×2 matrix; [0,1] is the correlation between the two arrays
            results[dtype] = round(corr, 3)

        if not results:
            return None     # all distraction columns were constant — no correlation possible

        worst = min(results, key=results.get)   # most negative correlation = biggest score drain
        return {
            "type":        worst,
            "label":       _distraction_label(worst),   # plain English label for the paragraph
            "correlation": results[worst],              # e.g. -0.82
            "all":         {_distraction_label(k): v for k, v in results.items()},  # full breakdown for UI
        }

    def score_feature_importance(self):
        """
        Trains a RandomForestRegressor on session features to rank which factors
        (time of day, duration, distraction types) best explain score variance.
        Returns the top 2 features by importance.
        Returns None if fewer than MIN_SESSIONS_FOR_ML sessions exist.
        """
        sessions = self._get_completed_sessions()
        if len(sessions) < MIN_SESSIONS_FOR_ML:
            return None

        # One entry per feature — order here must match the column order in rows.append() below
        feature_names = [
            "hour_of_day", "duration_minutes", "day_of_week",
            "phone_count", "look_away_count", "app_count",
            "left_desk_count", "idle_count",
        ]

        rows, targets = [], []
        for s in sessions:
            dt = datetime.fromisoformat(s["start_time"])    # parse ISO 8601 string to datetime
            rows.append([
                dt.hour,                        # 0–23: what hour the session started
                s["duration"] / 60.0,           # convert seconds to minutes for scale consistency
                dt.weekday(),                   # 0=Monday … 6=Sunday: day of week pattern
                s["phone_distractions"],        # count of phone distraction events
                s["look_away_distractions"],    # count of look-away events
                s["app_distractions"],          # count of app-switch events
                s["left_desk_distractions"],    # count of left-desk events
                s["idle_distractions"],         # count of idle events
            ])
            targets.append(s["score"])  # what we're trying to explain

        X = np.array(rows)              # 2D feature matrix: (n_sessions × n_features)
        y = np.array(targets, dtype=float)  # 1D target vector: session scores

        # n_estimators=100 balances stable importances with acceptable runtime on small data
        # random_state=42 makes results reproducible across runs
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)    # train the forest — uses all sessions since we only need importances, not predictions

        # rf.feature_importances_ is an array of floats summing to 1.0
        # zip pairs each name with its importance score, then we sort descending
        ranked = sorted(
            zip(feature_names, rf.feature_importances_),
            key=lambda x: x[1],     # sort by importance value
            reverse=True,           # highest importance first
        )
        top2 = [{"feature": name, "importance": round(imp, 3)} for name, imp in ranked[:2]]
        return {"top_features": top2}

    def pause_analysis(self):
        """
        Infers total pause time per session as: wall_clock_duration - active_duration.
        Compares average scores between sessions with long pauses vs without.
        Returns None if fewer than MIN_SESSIONS_FOR_ML sessions exist.
        """
        sessions = self._get_completed_sessions()
        if len(sessions) < MIN_SESSIONS_FOR_ML:
            return None

        long_pause_scores, normal_scores = [], []
        for s in sessions:
            start = datetime.fromisoformat(s["start_time"])     # parse session start timestamp
            end   = datetime.fromisoformat(s["end_time"])       # parse session end timestamp
            wall_clock    = (end - start).total_seconds()       # total elapsed time including pauses
            pause_duration = max(0.0, wall_clock - s["duration"])
            # s["duration"] is already active time (wall clock minus pauses), so subtracting it
            # gives total pause time. max(0) guards against floating-point rounding giving tiny negatives.

            if pause_duration > MAX_PAUSE_SECONDS:  # 30+ minute break = "too long"
                long_pause_scores.append(s["score"])
            else:
                normal_scores.append(s["score"])

        return {
            "long_pause_sessions":       len(long_pause_scores),
            # None when no sessions of that type exist — avoids np.mean([]) crash
            "avg_score_with_long_pause": round(float(np.mean(long_pause_scores)), 1) if long_pause_scores else None,
            "avg_score_without":         round(float(np.mean(normal_scores)), 1)     if normal_scores     else None,
        }

    def session_consistency(self):
        """
        Returns recent session counts and the longest consecutive-day streak.
        Always runs regardless of session count — used by the UI even below the ML threshold.
        """
        sessions = self._get_completed_sessions()
        today    = date.today()

        # Count sessions within each window by computing days since session start
        last_7  = sum(1 for s in sessions
                      if (today - datetime.fromisoformat(s["start_time"]).date()).days < 7)
        last_14 = sum(1 for s in sessions
                      if (today - datetime.fromisoformat(s["start_time"]).date()).days < 14)

        # Build a sorted set of unique calendar dates (deduplicates multiple sessions on same day)
        # Set comprehension {expr for x in iterable} gives unique values
        session_dates = sorted(
            {datetime.fromisoformat(s["start_time"]).date() for s in sessions},
            reverse=True,   # newest first so the loop walks backwards from today
        )

        streak = 0
        check  = today  # the date we expect the next session to be on (starts at today)
        for d in session_dates:
            if d == check or d == check - timedelta(days=1):
                # Session is on the expected day or the day before — continues the streak
                streak += 1
                check   = d     # advance the expected date back one more day
            elif d < check - timedelta(days=1):
                break           # gap found — streak ends, stop checking older dates

        return {"sessions_last_7_days": last_7, "sessions_last_14_days": last_14, "streak_days": streak}

    def phone_free_streak(self):
        """
        Counts consecutive most-recent sessions with zero phone distractions.
        Stops at the first session where a phone distraction was logged.
        Always runs regardless of session count.
        """
        sessions = self._get_completed_sessions()   # newest first
        streak   = 0
        for s in sessions:
            if s["phone_distractions"] == 0:
                streak += 1     # this session had no phone — extends the streak
            else:
                break           # phone appeared — streak is over, stop counting
        return {"streak": streak}

    def achievement_proximity(self):
        """
        Returns the top 3 in-progress achievements closest to completion,
        ranked by remaining percentage ascending (lowest remaining = closest).
        Always runs regardless of session count.
        """
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT name, progress, target,
                   CAST(target - progress AS REAL) / target AS remaining_pct
                   -- CAST to REAL forces float division instead of integer division
            FROM achievements
            WHERE unlocked = 0      -- only achievements not yet earned
              AND target > 0        -- guard against division by zero
            ORDER BY remaining_pct ASC  -- closest to completion first
            LIMIT 3                 -- top 3 is enough for the UI highlight section
        """)
        return [
            {
                "name":          r["name"],
                "progress":      r["progress"],
                "target":        r["target"],
                "remaining_pct": round(r["remaining_pct"], 2),  # e.g. 0.30 = 30% left to go
            }
            for r in cursor.fetchall()
        ]

    # ── Compiled report ───────────────────────────────────────────────────────

    def compile_report(self) -> dict:
        """
        Runs all analysis methods and compiles a single natural-language paragraph
        plus structured metadata for the UI.

        Each sentence is built independently from its own analysis method — if a
        method returns None, that sentence is simply skipped so the paragraph always
        reads naturally even with partial data.
        """
        n = self._session_count()   # total valid completed sessions

        # Always compute these regardless of session count — UI shows them even below threshold
        consistency  = self.session_consistency()
        phone_streak = self.phone_free_streak()
        achievements = self.achievement_proximity()

        # ── Below threshold: show a progress message instead of ML insights ──────
        if n < MIN_SESSIONS_FOR_ML:
            remaining = MIN_SESSIONS_FOR_ML - n                 # how many more sessions needed
            plural    = "s" if remaining > 1 else ""            # grammatical plural
            msg       = f"Complete {remaining} more session{plural} to unlock your personalized study profile."
            return {
                "paragraph":        msg,
                "optimal_time":     None,   # no data yet
                "optimal_duration": None,
                "top_distraction":  None,
                "trend":            None,
                "recommendation":   None,
                "consistency":      consistency,    # still shown even below threshold
                "phone_streak":     phone_streak,
                "achievements":     achievements,
            }

        # ── Run all ML analyses in sequence ──────────────────────────────────────
        # Each method returns a dict or None; None results are safely skipped below
        trend       = self.score_trend()
        best_time   = self.best_time_of_day()
        opt_length  = self.optimal_session_length()
        distraction = self.distraction_correlations()
        importance  = self.score_feature_importance()
        pauses      = self.pause_analysis()

        # ── Build paragraph sentence by sentence ─────────────────────────────────
        sentences = []          # each item is one sentence; joined at the end
        # Label variables extracted here so they're available both for the paragraph
        # and as separate metadata keys in the return dict
        optimal_time_label     = None
        optimal_duration_label = None
        top_distraction_label  = None
        trend_label            = None

        # Sentence 1 — best time of day (from KMeans clustering)
        if best_time:
            slot = _TIME_SLOT_LABELS.get(best_time["slot"], best_time["slot"])  # human-readable slot name
            sentences.append(
                f"Your best study time is the {slot}, "
                f"averaging a score of {best_time['avg_score']:.0f}."
            )
            optimal_time_label = slot   # saved for the recommendation sentence

        # Sentence 2 — optimal session length (from polynomial regression)
        if opt_length:
            mins = opt_length["optimal_minutes"]    # the predicted peak duration
            sentences.append(
                f"Your scores peak around {mins}-minute sessions — "
                f"both shorter and longer sessions tend to score lower."
            )
            optimal_duration_label = f"{mins} minutes"  # saved for the recommendation sentence

        # Sentence 3 — worst distraction (from Pearson correlation)
        if distraction:
            label = distraction["label"]    # e.g. "phone", "app"
            sentences.append(f"{label.capitalize()} distractions hurt your score the most.")
            top_distraction_label = label   # saved for the recommendation sentence

        # Sentence 4 — top factor from RandomForest feature importances
        if importance:
            top      = importance["top_features"][0]["feature"]             # e.g. "hour_of_day"
            readable = _FEATURE_READABLE.get(top, top.replace("_", " "))   # e.g. "time of day"
            sentences.append(f"{readable.capitalize()} explains the most variation in your scores.")

        # Sentence 5 — score trend (from moving average comparison)
        if trend and trend["trend"] != "stable":    # skip if stable — nothing interesting to say
            direction      = "improving" if trend["trend"] == "improving" else "declining"
            direction_word = "up" if direction == "improving" else "down"   # "up 8 pts" vs "down 8 pts"
            sentences.append(
                f"Your focus has been {direction} — "
                f"{direction_word} {abs(trend['delta']):.0f} points over your last 5 sessions."
            )
            sign        = "+" if trend["delta"] > 0 else ""        # e.g. "+8" or "-3"
            trend_label = f"{trend['trend']} ({sign}{trend['delta']:.0f} pts)"  # e.g. "improving (+8 pts)"

        # Sentence 6 — pause warning (only if long pauses actually occurred)
        if pauses and pauses.get("long_pause_sessions", 0) > 0:
            n_paused = pauses["long_pause_sessions"]    # number of sessions with 30+ min pauses
            sentences.append(
                f"{n_paused} of your recent sessions had breaks over 30 minutes, "
                f"which reduced your focus score."
            )

        # ── Recommendation: one action sentence combining the top findings ────────
        parts = []  # each part is a short action phrase to be joined with commas
        if optimal_time_label:
            parts.append(f"study in the {optimal_time_label}")
        if optimal_duration_label:
            parts.append(f"aim for {optimal_duration_label} sessions")
        if top_distraction_label:
            parts.append(f"reduce {top_distraction_label} distractions")

        recommendation = ("Recommendation: " + ", ".join(parts) + ".") if parts else None
        if recommendation:
            sentences.append(recommendation)   # appended last so it reads as a closing suggestion

        # Join all sentences into one paragraph; show fallback if no sentences were generated
        paragraph = (
            " ".join(sentences)
            if sentences
            else "Not enough variation in your data yet — keep studying!"
        )

        return {
            "paragraph":        paragraph,          # full feedback text for the UI to display
            "optimal_time":     optimal_time_label,     # e.g. "morning (6am–12pm)"
            "optimal_duration": optimal_duration_label, # e.g. "65 minutes"
            "top_distraction":  top_distraction_label,  # e.g. "phone"
            "trend":            trend_label,             # e.g. "improving (+8 pts)"
            "recommendation":   recommendation,          # standalone action sentence
            "consistency":      consistency,             # sessions in last 7/14 days + streak
            "phone_streak":     phone_streak,            # consecutive phone-free sessions
            "achievements":     achievements,            # top 3 closest to unlocking
        }
