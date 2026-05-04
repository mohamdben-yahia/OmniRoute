#!/bin/bash
# Test whether complete metadata envelope (userId, teamId, f) unlocks StartCascade
# Run this after a fresh Windsurf session is active

# Values from accepted HAR StartCascade request (fiddler/new.har)
export WINDSURF_USER_ID="user-47ba71096f0b498daaf30bd1b11a9b6b"
export WINDSURF_TEAM_ID="devin-team\$account-ae790c86db964e3f9c0296307fcf4691"
export WINDSURF_METADATA_F=$'\x00\x01\x03'

# Session ID must be updated to match the current live runtime
# Check tmp_windsurf_runtime_ls_binding.json for the current session_id
export WINDSURF_SESSION_ID="${WINDSURF_SESSION_ID:-UPDATE_ME}"

# CSRF token and LS URL are read from windsurf-live-bootstrap.json by the probe
# Make sure that file has fresh values for the current session before running

echo "Testing StartCascade with complete metadata envelope..."
echo "  userId: $WINDSURF_USER_ID"
echo "  teamId: $WINDSURF_TEAM_ID"
echo "  f: (3 bytes)"
echo "  sessionId: $WINDSURF_SESSION_ID"
echo ""

if [ "$WINDSURF_SESSION_ID" = "UPDATE_ME" ]; then
  echo "ERROR: Update WINDSURF_SESSION_ID first"
  echo "Check tmp_windsurf_runtime_ls_binding.json for current session_id"
  exit 1
fi

python scripts/windsurf_direct_probe.py
