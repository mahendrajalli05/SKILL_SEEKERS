# Search Text V1 report

Date: 2026-09-10  
Slice: Project Search text-search correction only  
Frozen elsewhere: Cost V1.1, Time V1, Overlap V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, Relationship Graph V1, REAL/HYBRID data architecture, Andhra Pradesh pilot scope, State → Constituency cascade

This slice fixes the officer Text Search field so Scheme ID, `internal_project_id`, work description, and MP name are actually searchable with case-insensitive partial matching. It does **not** change intelligence engines, Passport, Investigation Workspace, REAL/HYBRID separation, or the AP pilot geographic rules.

---

## 1. Problem

The Search page advertised four text targets, but behaviour was unreliable:

- Scheme ID is computed (`SVK-{STATE}-{NNNNNN}`) and is **not** stored on `project` rows. Partial values such as `000139` never matched SQL `LIKE` on stored columns.
- The UI updated `q` on every keystroke, so each character triggered an API request.
- There was no Search button. Enter only reset the page number.
- A non-empty query with zero matches could be confused with the unfiltered list. The empty state did not say **No matching projects found**.
- Search state was not preserved in the URL (except data mode).

---

## 2. Files changed

Created:

- `backend/tests/test_search_text.py`
- `frontend/src/lib/highlight.tsx`
- `frontend/src/lib/searchUrl.ts`
- `frontend/src/lib/__tests__/highlight.test.tsx`
- `frontend/src/lib/__tests__/searchUrl.test.ts`
- `frontend/src/components/__tests__/SearchFilters.search.test.tsx`
- `frontend/src/app/search/__tests__/page.test.tsx`
- `SEARCH_TEXT_V1_REPORT.md`

Changed:

- `backend/app/search/service.py` — normalised, case-insensitive, server-side partial `q`
- `backend/app/identity/scheme_id.py` — substring match over the existing Scheme ID map
- `backend/app/identity/__init__.py` — export the helper
- `backend/tests/test_search_api.py` — `q` also matches `internal_project_id`
- `frontend/src/app/search/page.tsx` — Enter / Search button, URL state, loading, no-results
- `frontend/src/components/SearchFilters.tsx` — Search and Clear search
- `ROADMAP.md` — Search line only

Not changed: `data/raw/`, real `project` rows, intelligence engines, database indexes, REAL/HYBRID architecture, AP default scope, State → Constituency options.

---

## 3. Backend search

`GET /api/v1/projects?q=` still performs search. No duplicate search API was added.

Query normalisation:

- trim
- collapse internal whitespace (`" road "` → `road`)
- cap length at 200 characters
- empty / whitespace-only → no text filter (normal AP-scoped list)

Case-insensitive partial match uses parameterised SQL:

```
lower(internal_project_id) LIKE ?
OR lower(work_description) LIKE ?
OR lower(mp_name) LIKE ?
```

`%`, `_`, and `\` in the user query are escaped. The query is bound as a parameter.

Scheme ID is not a database column. Matching uses the existing in-memory identifier map already used for display (internal ID → `SVK-AP-NNNNNN`). That scan is restricted to the effective state (Andhra Pradesh in normal pilot mode) so a query such as `SVK` does not build a 56,138-wide `IN` list. Matching internal IDs are then applied with chunked `IN` clauses (400 ids). Full project rows are never loaded into the browser for filtering.

AP pilot scope remains applied for text search. Identifier lookup no longer bypasses the pilot state filter. Direct `GET /api/v1/projects/{id}` for a non-AP work is unchanged.

Pagination remains server-side (`page`, `page_size`).

---

## 4. Indexes

No schema indexes were added.

`LIKE '%term%'` cannot use a normal B-tree prefix index. A new FTS table would be a schema change and is not required for the current AP-scoped set (3,640 works). Existing indexes remain:

- `ix_project_internal_project_id`
- `ix_project_state` (pilot / state filter)
- `ix_project_constituency`
- `ix_project_category`
- `ix_project_status`
- `ix_project_mp_name`
- `ix_project_recommended_date`

Scheme ID matching does not require a stored column and does not write onto real project rows.

---

## 5. Frontend

Text search runs when the officer:

1. presses Enter, or
2. clicks **Search**

Typing updates a draft field only. It does not send an API request per keystroke.

**Clear search** empties the text query, keeps State / Constituency / Category / Status, and reloads the normal AP-scoped list.

URL query parameters preserved where practical:

- `q`
- `state`
- `constituency`
- `category`
- `status`
- `page`
- `mode`

Changing State still clears Constituency. Text search does not reset the other filters.

Results still show Scheme ID, work description, constituency, category, status, allocation, recommendation date, and data mode. Matching text is highlighted with `<mark>` when the match is a simple substring.

Loading: `Loading search results…`  
Zero matches for a non-empty query: **No matching projects found** (not the unfiltered list).

---

## 6. Tests

Backend (new `test_search_text.py` plus existing search tests):

1. exact Scheme ID  
2. partial Scheme ID  
3. `internal_project_id`  
4. partial `internal:`  
5. work description phrase  
6. partial work description (`school`)  
7. MP name  
8. case-insensitive  
9. whitespace trimming  
10. empty query  
11. zero-result query (empty list, not the full AP set)  
12–16. search + state / constituency / category / status / all together  
17. pagination with search  
18. clearing search  
19. non-AP excluded in AP pilot  
20. Scheme ID displayed  
21–22. frontend loading and no-results  

Frontend: typing vs Search/Enter, Clear search, filter combination, result rendering, highlight, URL parse/build.

---

## 7. Verification

- Complete backend pytest: passed (396 tests).
- Complete frontend Vitest: passed (35 tests).
- `next build`: succeeded.

Live checks on `data/processed/sarvsakshi.db` (56,138 rows; AP default 3,640):

| Check | Result |
| --- | --- |
| Exact Scheme ID `SVK-AP-002021` | 1 work, ANAKAPALLE |
| Partial rank `002021` | same work |
| Exact Scheme ID `SVK-AP-000139` | 1 work, HINDUPUR, roads |
| Partial `000139` | 1 AP work, id 232 |
| Partial internal id `internal:8c7c6d729` | 1 work |
| `internal:` | 3,640 AP works (all AP internal IDs start with `internal:`) |
| `school` | 77 AP works |
| `  SCHOOL  ` | same 77 |
| `construction of roads` | 1,232 AP works, including `SVK-AP-000139` |
| MP name `Satyavathi` | 74 AP works |
| Combined Andhra Pradesh + ONGOLE + Normal/Others + Unsanctioned + `road` | 111 works, all ONGOLE |
| `zzzz-no-such-project-xyz` | total 0, empty items |
| Empty query | 3,640 AP works |
| Pagination `school` page 1 vs 2 | disjoint ids, total 77 |
| AP-only | school page states = `{Andhra Pradesh}` |
| Full database retained | 56,138 with `apply_pilot_scope=false` |
| Maharashtra `school` when that state is selected | 14 works, state Maharashtra |

`JALLI` is not an MP name in the current Andhra Pradesh extract (0 results). Unit tests cover `JALLI` on synthetic rows. Live MP search was demonstrated with `Satyavathi`.

---

## 8. Limitations

- Scheme IDs remain computed, not stored on `project`. Reloading a different extract membership can change ranks (unchanged from AP Pilot V1).
- `internal:` matches every AP work because every surrogate starts with that prefix. That is correct partial matching, not a bug.
- Highlighting is simple case-insensitive substring wrapping. It is not a full search-result snippet engine.
- No FTS5 / trigram index. If search later covers all 56,138 rows without a state filter as the common path, consider SQLite FTS then — as a separate, approved schema change.

Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, and Relationship Graph V1 remain frozen.
