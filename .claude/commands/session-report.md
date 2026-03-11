Generate a session report for the current coding session. Create the report as a markdown file in `.session-reports/` named with today's date and time: `YYYY-MM-DD-HHMM.md`.

## Report Structure

### 1. Session Summary
Write 2-3 sentences describing the overall focus and outcome of this session.

### 2. Session Metrics

#### Intent Completion

At the top of this section, state what the session set out to accomplish. Infer this from the user's first message(s) and any stated goals. Then assess:

| Intent | Status |
|---|---|
| _(goal 1)_ | Done / Partial / Carried / Abandoned |
| _(goal 2)_ | Done / Partial / Carried / Abandoned |

**Completion rate: X/Y intents completed.** If goals shifted mid-session (scope changed, new priority emerged), note that — a pivot isn't a failure.

#### Raw Metrics

Collect these numbers for trend analysis across sessions. Use exact values where available, best estimates where not.

| Metric | Value |
|---|---|
| Tokens in (prompt) | _estimate from conversation length_ |
| Tokens out (completion) | _estimate from response length_ |
| Files created | |
| Files modified | |
| Files deleted | |
| Net lines changed | _(+added / -removed from git diff --stat)_ |
| Tests added / removed | _(net delta)_ |
| Commits made | |
| Retries / failed attempts | _(times something was tried, failed, and redone)_ |
| Failures in Github Actions CI  | |
| Open items carried forward | |
| Open items closed | |

Note: Token counts are estimates since exact values aren't available within a session. Use conversation length as a proxy. The numbers don't need to be precise — directional trends across reports are what matter.

### 3. What Was Built / Modified
List every file created, modified, or deleted this session with a one-line description of each change. Group by feature or area if applicable.

### 4. Key Decisions Made
Document any architectural decisions, tradeoffs, or approach changes that happened during this session. Future sessions need this context.

### 5. Lessons Learned
Capture technical insights, gotchas, patterns discovered, or things that took longer than expected and why. Be specific — "the X library doesn't support Y" is better than "ran into issues."

### 6. Stale Document Review
Check `docs/plans/` and `docs/research/` for any documents that are now:
- **Completed**: The plan was fully implemented this session
- **Superseded**: A newer approach replaced this plan
- **Outdated**: References architecture or files that no longer exist

For each stale document found, add its relative path to `.archive-queue` (one path per line). Explain in the report why each is being archived.

### 7. CLAUDE.md Suggestions
Review the session for anything that should be added to or changed in CLAUDE.md:
- New patterns or conventions established
- Outdated instructions that caused confusion
- Missing context that would help future sessions
- Commands or workflows that should be documented

**Format each suggestion as a concrete diff** — show exactly what to add, remove, or change. Do NOT auto-apply these changes.

### 8. Open Items
List any unfinished work, known bugs, or next steps. Be specific enough that the next session can pick up without re-discovery.

---

$ARGUMENTS
