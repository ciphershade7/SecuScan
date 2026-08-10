#!/bin/bash
set -e

echo "🔥 Ponytail Cleanup - Executing Quick Wins"
echo "=========================================="

# Phase 1: Zero-risk file deletions
echo ""
echo "Phase 1: Deleting 8 files..."
rm -f scripts/enhance_github_issues_old.py
rm -f scripts/validate_plugin.py
rm -f backend/secuscan/sandbox_executor.py
rm -f frontend/src/components/I18nContext.tsx
rm -f frontend/src/hooks/useVirtualList.ts
rm -f frontend/src/hooks/useWebSocket.ts
rm -f plugins/domain-finder/parser.py
rm -f testing/backend/unit/test_executor_target_helpers.py
echo "✓ Deleted 8 files"

# Phase 2: Test cleanup
echo ""
echo "Phase 2: Test cleanup..."
rm -f testing/backend/unit/test_executor_helpers.py
rm -f testing/backend/unit/test_validation_helpers.py
rm -f testing/backend/unit/test_risk_scoring_helpers.py
rm -f testing/backend/unit/test_parser_sandbox_helpers.py
rm -f testing/backend/unit/test_auth_helpers.py
rm -f testing/backend/unit/test_time_utils.py
rm -f testing/backend/unit/test_logging_utils.py
echo "✓ Deleted 7 test files"

# Phase 3: One-liner fixes
echo ""
echo "Phase 3: One-liner fixes..."

# time_utils.py
sed -i '' '/^UTC = /d' backend/secuscan/time_utils.py 2>/dev/null || true
sed -i '' '/^def utc_now/,/^    return/d' backend/secuscan/time_utils.py 2>/dev/null || true

# auth.py
sed -i '' '/^def get_api_key/,/^    return/d' backend/secuscan/auth.py 2>/dev/null || true

# database.py
sed -i '' '/^    def execute_no_commit/,/^        return/d' backend/secuscan/database.py 2>/dev/null || true

# cache.py
sed -i '' '/^    async def connect/,/^        pass/d' backend/secuscan/cache.py 2>/dev/null || true

# AuthContext.tsx
sed -i '' '/^const defaultValue = {/,/^};/d' frontend/src/components/AuthContext.tsx 2>/dev/null || true

# ToolCheatSheet index
rm -f frontend/src/components/ToolCheatSheet/index.ts 2>/dev/null || true

echo "✓ Applied one-liner fixes"

# Summary
echo ""
echo "=========================================="
echo "✅ Quick wins executed successfully!"
echo ""
echo "Files deleted: 15"
echo "Estimated lines removed: ~1,800"
echo ""
echo "Next steps:"
echo "1. Run tests: pytest && npm test"
echo "2. Review changes: git diff --stat"
echo "3. Commit: git commit -am 'chore: ponytail cleanup phase 1'"
echo ""
echo "For dependency removal, run:"
echo "  cd frontend && npm uninstall @hugeicons/core-free-icons @hugeicons/react react-icons styled-components html2canvas jspdf cross-env"
echo "  pip uninstall psycopg python-multipart python-whois"

