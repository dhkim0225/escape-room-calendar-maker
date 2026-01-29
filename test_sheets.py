"""
Test Google Sheets functionality.
"""
from config import Config
from src.sheets import GoogleSheetsExporter

print("=" * 60)
print("🧪 Google Sheets Test")
print("=" * 60)

# Check configuration
print("\n1️⃣ Configuration check:")
print(f"   GOOGLE_SHEETS_CREDENTIALS_PATH: {Config.GOOGLE_SHEETS_CREDENTIALS_PATH}")
print(f"   is_google_sheets_configured(): {Config.is_google_sheets_configured()}")

import os
print(f"   File exists: {os.path.exists(Config.GOOGLE_SHEETS_CREDENTIALS_PATH)}")

if os.path.exists(Config.GOOGLE_SHEETS_CREDENTIALS_PATH):
    print(f"   File size: {os.path.getsize(Config.GOOGLE_SHEETS_CREDENTIALS_PATH)} bytes")

# Try to initialize exporter
print("\n2️⃣ Initializing GoogleSheetsExporter:")
try:
    exporter = GoogleSheetsExporter()
    print(f"   ✅ Initialized successfully")
    print(f"   Enabled: {exporter.enabled}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()

# Test scenario data
test_scenario = {
    "scenario_id": 1,
    "name": "테스트 시나리오",
    "description": "테스트용 시나리오입니다",
    "teams": {
        "1": [
            {
                "room_name": "테스트 방탈출",
                "start_time": "14:00",
                "end_time": "16:00",
                "theme": "추리",
                "members": ["홍길동", "김철수"],
                "member_count": 2
            }
        ]
    },
    "pros": "테스트 장점",
    "cons": "테스트 단점"
}

print("\n3️⃣ Creating test sheet:")
try:
    exporter = GoogleSheetsExporter()
    if exporter.enabled:
        sheet_url = exporter.create_schedule_sheet(test_scenario, "TEST - Escape Room Schedule")
        if sheet_url:
            print(f"   ✅ Sheet created!")
            print(f"   URL: {sheet_url}")
        else:
            print(f"   ❌ Sheet creation returned None")
    else:
        print(f"   ⚠️ Exporter not enabled")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()
