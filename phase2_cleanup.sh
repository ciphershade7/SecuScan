#!/bin/bash
set -e

echo "Phase 2: Config cleanup"

# Delete unused config fields
sed -i '' '/parser_hash_algorithm: str = "sha256"/d' backend/secuscan/config.py
sed -i '' '/network_audit_retention_days: int = 90/d' backend/secuscan/config.py
sed -i '' '/sandbox_allow_network: bool = True/d' backend/secuscan/config.py

echo "✓ Deleted 3 unused config fields"
