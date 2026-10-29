# SMARTWASTE — BROKEN DIAGNOSIS REPORT

**Generated:** 2026-10-29  
**Scope:** Static code analysis only (no rebuild, no DB changes, no ML model changes)

---

## 🔴 CRITICAL ISSUES (Blockers - App Won't Start/Work)

| # | Error | File Affected | Root Cause | Recommended Fix |
|---|-------|---------------|------------|-----------------|
| 1 | **ML Model files missing** — `FileNotFoundError` on startup | `backend/app/core/config.py:12-16`<br>`backend/app/ml/predictor.py:19-26`<br>`backend/app/services/ml_predictor.py:23-28` | Config points to `MLproject/ml/models` and `MLproject/data/features` but only `MLproject_old/` exists (empty, no models, no feature files) | Create `MLproject/ml/models/` and `MLproject/data/features/` with required model files, OR update config paths to point to actual model locations |
| 2 | **No `.env` file** — Secrets/config not loaded | `backend/.env.example` exists but `backend/.env` missing | App reads from `.env` (config.py:34) but file doesn't exist; falls back to defaults | Copy `.env.example` to `.env` and fill in `SECRET_KEY`, `OPENWEATHER_API_KEY` |
| 3 | **Frontend → Backend API mismatch: `/collector/login`** (404) | `frontend/src/context/AuthContext.jsx:46`<br>`backend/app/routers/auth.py` (missing) | Frontend calls `/collector/login` for collector role; backend has no such endpoint in `auth.py` or `collector.py` | Add `@router.post("/collector/login")` to `collector.py` router OR change frontend to use `/auth/login` with role parameter |
| 4 | **Frontend → Backend API mismatch: `/auth/admin-login`** (404) | `frontend/src/context/AuthContext.jsx:48`<br>`backend/app/routers/auth.py` (missing) | Frontend calls `/auth/admin-login` for admin role; backend has no such endpoint | Add `@router.post("/admin-login")` to `auth.py` OR change frontend to use `/auth/login` with `role: admin` |
| 5 | **Frontend register calls `/auth/register` → returns 501** | `frontend/src/context/AuthContext.jsx:86`<br>`backend/app/routers/auth.py:14-25` | Backend `/auth/register` explicitly returns `501 Not Implemented` with message "Use /auth/register-with-password endpoint" | Change frontend to call `/auth/register-with-password` with proper payload, OR implement `/auth/register` properly in backend |
| 6 | **Missing `timedelta` import** — `NameError` | `backend/app/services/waste.py:73-74` | Uses `timedelta(days=1)` but `timedelta` not imported (only `date`, `datetime` imported) | Add `from datetime import date, datetime, timedelta` at top of file |
| 7 | **Syntax error in `predictor.py`** — `SyntaxError` | `backend/app/ml/predictor.py:303` | Stray `)` on line 303 followed by duplicate logging block (lines 304-306) | Remove stray `)` and duplicate lines 304-306 |
| 8 | **Duplicate method definitions** — runtime confusion | `backend/app/services/ml_predictor.py`<br>Lines 90-130 AND 147-187 (`_get_user_history`)<br>Lines 132-140 AND 189-197 (`_get_season`)<br>Lines 142-145 AND 199-202 (`_get_day_type`)<br>Lines 262-290 AND 291-339 (duplicate code in `_construct_features`) | Copy-paste error created duplicate methods; second definition overwrites first | Remove duplicate blocks (keep first occurrence of each method) |

---

## 🟠 HIGH SEVERITY (Functional Breakage)

| # | Error | File Affected | Root Cause | Recommended Fix |
|---|-------|---------------|------------|-----------------|
| 9 | **Duplicate imports** — maintenance burden | `backend/app/routers/admin.py:29-49` | Lines 29-39 and 40-49 are identical imports from `ml_monitoring` | Remove duplicate block (lines 40-49) |
| 10 | **Duplicate `TwoStageModel` class** | `backend/app/services/ml_compat.py:11-48`<br>`backend/app/services/ml_shared.py:11-52` | Same class defined in two files; `ml_predictor.py:34` imports from `ml_shared` but pickle may reference `ml_compat` | Keep only `ml_shared.py`; update `ml_compat.py` to re-export from `ml_shared` OR delete `ml_compat.py` |
| 11 | **Config paths point to non-existent `MLproject`** | `backend/app/core/config.py:12-16` | `Path(__file__).parent.parent.parent.parent.parent / "MLproject"` resolves to `backend/MLproject` which doesn't exist (only `MLproject_old`) | Change to `MLproject_old` OR create `MLproject` at correct location with proper structure |
| 12 | **Missing `__all__` exports** — import failures | `backend/app/models/__init__.py:6-18` | Imports `TrainingReferenceStats` and `ActualCollection` but doesn't include them in `__all__` list | Add `"TrainingReferenceStats", "ActualCollection"` to `__all__` |
| 13 | **SQLite database path invalid** | `backend/app/core/config.py:12` | `DATABASE_URL` points to `backend/MLproject/database/smartwaste.db` but `MLproject/database/` doesn't exist | Create directory or change path to `backend/database/smartwaste.db` |
| 14 | **Empty folders** — dead code | `backend/app/utils/`<br>`frontend/src/hooks/`<br>`frontend/src/utils/` | Folders exist but contain no files | Remove empty folders OR add intended utilities |

---

## 🟡 MEDIUM SEVERITY (Degraded Functionality)

| # | Error | File Affected | Root Cause | Recommended Fix |
|---|-------|---------------|------------|-----------------|
| 15 | **Frontend `baseURL: '/api/v1'` assumes proxy** | `frontend/src/services/api.js:4` | Vite dev server needs proxy config to forward `/api/v1` to backend; without it, CORS/404 errors | Add `server.proxy` to `vite.config.js` for `/api/v1` → `http://localhost:8000` |
| 16 | **Auth token payload mismatch** | `frontend/src/context/AuthContext.jsx:31-37`<br>`backend/app/services/auth.py:32-41` | Frontend decodes `sub` as `user_id`; backend `TokenData` expects `user_id` and `role` — matches but fragile | Ensure backend `create_access_token` includes `role` in payload (it does); verify `sub` = user_id |
| 17 | **Collector schema expects `vehicle_capacity_kg` but model has it** | `backend/app/schemas/collector.py:62-68`<br>`backend/app/models/user.py:44` | Model has `vehicle_capacity_kg` but service `get_vehicle_info` uses `collector.vehicle_capacity_kg or 120.0` — OK but default hardcoded | Move default to model or config |
| 18 | **`WasteSubmissionVerify` schema requires `area`, `account_type` but frontend may not send** | `backend/app/schemas/waste.py:72-77`<br>`frontend/src/pages/CollectWaste.jsx` | Schema has extra required fields not in `WasteSubmissionCreate`; verify endpoint may fail | Align schema with frontend payload or make fields optional |

---

## 🟢 LOW SEVERITY (Code Quality / Technical Debt)

| # | Error | File Affected | Root Cause | Recommended Fix |
|---|-------|---------------|------------|-----------------|
| 19 | **Duplicate code in `predictor.py`** (WastePredictor & MultiWastePredictor) | `backend/app/ml/predictor.py:64-162` vs `266-370` | Two predictor classes with nearly identical `_construct_features` logic | Extract shared feature construction to base class or utility module |
| 20 | **Hardcoded defaults in ML predictors** | `backend/app/ml/predictor.py:102-103`<br>`backend/app/services/ml_predictor.py:299-301` | `is_holiday=False`, `is_festival=False`, `festival_intensity=0.0` hardcoded instead of using calendar service | Use `get_calendar_features()` (already imported) consistently |
| 21 | **Print statements instead of logging** | `backend/app/services/waste.py:80`<br>`backend/app/services/prediction.py:219, 257` | Uses `print()` for errors; not suitable for production | Replace with `logging` module |
| 22 | **Unused imports** | `backend/app/routers/collector.py:28`<br>`backend/app/routers/admin.py:52-53` | `CollectorVehicleInfo` imported twice; `User` imported but not used in admin.py | Remove unused imports |
| 23 | **Inconsistent season mapping** | `backend/app/ml/predictor.py:164-172`<br>`backend/app/services/ml_predictor.py:132-140` vs `189-197` | `predictor.py` uses string seasons; `ml_predictor.py` uses int (0-3) — mismatch if shared | Standardize on one representation (string recommended) |

---

## 📋 DEPENDENCY GRAPH (Fix Order)

```
1. Create .env file (Critical #2)
   │
   ├── 2. Fix config paths (Critical #1, High #11, #13)
   │       │
   │       ├── 3. Add ML model files (Critical #1)
   │       │
   │       └── 4. Create database directory (High #13)
   │
   ├── 5. Fix syntax/import errors (Critical #6, #7, #8)
   │       │
   │       ├── 6. Remove duplicate code (Critical #8, High #9, #10)
   │       │
   │       └── 7. Fix __all__ exports (High #12)
   │
   ├── 8. Fix API mismatches (Critical #3, #4, #5)
   │       │
   │       └── 9. Add Vite proxy (Medium #15)
   │
   └── 10. Code quality fixes (Low #19-#23)
```

---

## 📁 FILES THAT MUST BE CREATED/RESTORED

| Path | Description |
|------|-------------|
| `backend/.env` | Environment config (copy from `.env.example`) |
| `backend/MLproject/ml/models/random_forest_model.joblib` | Objective 1 model |
| `backend/MLproject/ml/models/multi_waste_rf_model.joblib` | Multi-output RF model |
| `backend/MLproject/ml/models/multi_waste_xgb_model.joblib` | Multi-output XGB model |
| `backend/MLproject/data/features/feature_metadata.json` | Feature metadata |
| `backend/MLproject/data/features/submissions_features.parquet` | Training features |
| `backend/MLproject/ml/models/improved/RF_Multi.joblib` | Improved multi RF |
| `backend/MLproject/ml/models/improved/XGB_Multi.joblib` | Improved multi XGB |
| `backend/MLproject/ml/models/improved/RF_PerType.joblib` | Per-type RF models |
| `backend/MLproject/ml/models/improved/preprocessor.joblib` | Preprocessor pipeline |
| `backend/database/` | Directory for SQLite DB |

---

## ✅ VERIFICATION CHECKLIST (After Fixes)

- [ ] `python -m backend.app.main` starts without import errors
- [ ] `uvicorn backend.app.main:app --reload` serves `/api/v1/docs`
- [ ] `npm run dev` in frontend starts without build errors
- [ ] Frontend `/login` → calls `/api/v1/auth/login` → returns token
- [ ] Frontend `/register` → calls `/api/v1/auth/register-with-password` → returns token
- [ ] Collector login works via `/api/v1/auth/login` with `role: collector`
- [ ] Admin login works via `/api/v1/auth/login` with `role: admin`
- [ ] ML prediction endpoints return valid responses (not 500)
- [ ] No duplicate method definitions in `ml_predictor.py`
- [ ] No syntax errors in `predictor.py`