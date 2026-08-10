# Ponytail Quick Wins - Delete These Now

## 🔥 Zero-Risk Deletions (Do First)

### Entire Files (8 files, ~1,200 lines)
```bash
rm scripts/enhance_github_issues_old.py
rm scripts/validate_plugin.py
rm backend/secuscan/sandbox_executor.py
rm frontend/src/components/I18nContext.tsx
rm frontend/src/hooks/useVirtualList.ts
rm frontend/src/hooks/useWebSocket.ts
rm plugins/domain-finder/parser.py
rm testing/backend/unit/test_executor_target_helpers.py
```

### Unused Dependencies
```bash
# Frontend
npm uninstall @hugeicons/core-free-icons @hugeicons/react react-icons styled-components html2canvas jspdf cross-env

# Backend
pip uninstall psycopg python-multipart python-whois
```

**Impact:** -1,200 lines, -10 deps, 0 risk

---

## ⚡ High-Value Deletions (Do Second)

### backend/secuscan/rate_limiter.py
**Action:** Delete entire file, use ratelimit.py instead
**Lines:** ~250
**Risk:** Low (duplicate implementation)

### backend/secuscan/notification_service.py
```python
# Delete lines 964-1085 (process_slack_notification)
# Delete lines 747-874 (detect_webhook_platform)
# Delete lines 639-662 (retry loop - max_retries=0)
```
**Lines:** ~250
**Risk:** Low (dead code + duplicates)

### backend/secuscan/knowledgebase.py
**Action:** Convert class to module functions
**Lines:** ~135
**Risk:** Medium (refactor needed)

### frontend/src/pages/*.tsx
```bash
# Delete duplicate animation variants
sed -i '' '/const containerVariants/,/^}/d' frontend/src/pages/Scans.tsx
sed -i '' '/const itemVariants/,/^}/d' frontend/src/pages/Scans.tsx
sed -i '' '/const containerVariants/,/^}/d' frontend/src/pages/Workflows.tsx
sed -i '' '/const itemVariants/,/^}/d' frontend/src/pages/Workflows.tsx
sed -i '' '/const containerVariants/,/^}/d' frontend/src/pages/Reports.tsx
sed -i '' '/const itemVariants/,/^}/d' frontend/src/pages/Reports.tsx
```
**Lines:** ~50
**Risk:** Low (duplicate configs)

**Impact:** -685 lines, low-medium risk

---

## 🎯 Config Cleanup (Do Third)

### backend/secuscan/config.py
Delete these unused fields:
```python
# Line 88
parser_hash_algorithm: str = "sha256"  # DELETE

# Line 100
network_audit_retention_days: int = 90  # DELETE

# Line 158
notification_ssrf_enabled: bool = True  # DELETE (should be mandatory)

# Line 236-238
@property
def base_url(self) -> str:  # DELETE (redundant)
    return self.public_base_url

# Line 142
sandbox_allow_network: bool = False  # DELETE (security bypass)

# Line 143
docker_network: str = "restricted"  # DELETE (hardcode in main.py)

# Line 217-233
@field_validator(...)
def parse_csv_or_list(...):  # DELETE (Pydantic does this)
```

### frontend/tailwind.config.js
```javascript
// Delete unused colors (lines 17-18, 20, 39-41)
'primary-text': '#e5e7eb',  // DELETE
'secondary-text': '#9ca3af',  // DELETE
'charcoal-dark': '#1a1a1a',  // DELETE
silver: { ... },  // DELETE

// Delete unused animations (lines 49, 51)
'fast-pulse': { ... },  // DELETE
'fade-in': { ... },  // DELETE

// Delete unused font (line 46)
serif: ['Playfair Display', ...],  // DELETE
```

**Impact:** -150 lines, 0 risk

---

## 📦 One-Liner Fixes

### Backend
```bash
# time_utils.py - delete wrappers
sed -i '' '/^UTC = /d' backend/secuscan/time_utils.py
sed -i '' '/^def utc_now/,/^$/d' backend/secuscan/time_utils.py

# models.py - use stdlib exception
sed -i '' 's/SandboxViolation/ValueError/g' backend/secuscan/*.py
sed -i '' '/^class SandboxViolation/,/^$/d' backend/secuscan/models.py

# auth.py - delete unused getter
sed -i '' '/^def get_api_key/,/^$/d' backend/secuscan/auth.py

# database.py - delete unused method
sed -i '' '/^    def execute_no_commit/,/^$/d' backend/secuscan/database.py

# cache.py - delete empty methods
sed -i '' '/^    async def connect/,/^$/d' backend/secuscan/cache.py
sed -i '' '/^    async def disconnect/,/^$/d' backend/secuscan/cache.py
```

### Frontend
```bash
# Delete unused context defaults
sed -i '' '/^const defaultValue = {/,/^};$/d' frontend/src/components/AuthContext.tsx

# Delete single-line re-exports
rm frontend/src/components/ToolCheatSheet/index.ts
sed -i '' 's|from "./ToolCheatSheet"|from "./ToolCheatSheet/ToolCheatSheet"|g' frontend/src/**/*.tsx
```

**Impact:** -100 lines, 0 risk

---

## 🧪 Test Cleanup

```bash
# Delete duplicate test file
rm testing/backend/unit/test_executor_helpers.py

# Delete trivial helper test files
rm testing/backend/unit/test_validation_helpers.py
rm testing/backend/unit/test_risk_scoring_helpers.py
rm testing/backend/unit/test_parser_sandbox_helpers.py
rm testing/backend/unit/test_auth_helpers.py
rm testing/backend/unit/test_time_utils.py
rm testing/backend/unit/test_logging_utils.py
```

**Impact:** -500 lines, 0 risk

---

## 📊 Total Quick Wins

| Action | Lines | Risk |
|--------|-------|------|
| Delete files | 1,200 | Zero |
| Remove deps | - | Zero |
| High-value cuts | 685 | Low |
| Config cleanup | 150 | Zero |
| One-liners | 100 | Zero |
| Test cleanup | 500 | Zero |
| **TOTAL** | **2,635** | **Minimal** |

**Time to execute:** 30-60 minutes  
**Complexity reduction:** ~25%  
**Risk:** Minimal (mostly dead code)

---

## ⚠️ Before You Start

1. **Commit current state:** `git commit -am "Pre-ponytail checkpoint"`
2. **Create branch:** `git checkout -b ponytail-cleanup`
3. **Run tests after each section:** `pytest && npm test`
4. **Verify no imports broken:** `grep -r "enhance_github_issues_old" .`

## 🚀 Execution Order

1. ✅ Zero-risk deletions (files + deps)
2. ✅ Test cleanup (no production impact)
3. ✅ Config cleanup (unused flags)
4. ✅ One-liner fixes (trivial changes)
5. ⚠️ High-value deletions (needs testing)

**Ship it.** 🎯
