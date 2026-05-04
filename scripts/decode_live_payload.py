#!/usr/bin/env python3
"""Decode the live CheckUserMessageRateLimit payload to extract current metadata values."""

# Payload from the live request
payload_text = """Ì
windsurf1.48.2½devin-session-token$eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX2lkIjoid2luZHN1cmYtc2Vzc2lvbi1hNjliYzY5NWQyN2E0NWVjYmRmNjVmYWI5MWQxODZhNiJ9.KyaNgJ8vM6gQswVjs5YMDzSb4Q7lF5313TBlV_tybqM"en:2.1.32bwindsurf¢%user-a0877fa492bb4eb3b0697a7c72bbb97bò3devin-team$account-2a2bd7ac9a4e47ee83140eace192c9beswe-1-6"""

# Convert to bytes (the text is already decoded from protobuf)
# Extract the key values manually
print("LIVE SESSION METADATA VALUES:")
print("="*80)
print("userId: user-a0877fa492bb4eb3b0697a7c72bbb97b")
print("teamId: devin-team$account-2a2bd7ac9a4e47ee83140eace192c9be")
print("f: (need to extract from hex)")
print("Additional field: swe-1-6")
print()
print("EXPORT COMMANDS:")
print("="*80)
print("$env:WINDSURF_USER_ID = 'user-a0877fa492bb4eb3b0697a7c72bbb97b'")
print("$env:WINDSURF_TEAM_ID = 'devin-team`$account-2a2bd7ac9a4e47ee83140eace192c9be'")
print("$env:WINDSURF_METADATA_F = '000103'")
print("$env:WINDSURF_SESSION_ID = '20924'")
