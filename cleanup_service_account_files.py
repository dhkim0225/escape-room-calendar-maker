"""
List and delete files created by Service Account.
"""
from src.sheets import GoogleSheetsExporter
import gspread

print("=" * 60)
print("🧹 Service Account File Cleanup")
print("=" * 60)

try:
    exporter = GoogleSheetsExporter()

    if not exporter.enabled:
        print("❌ Google Sheets not configured")
        exit(1)

    # List all files
    print("\n📋 Files created by Service Account:")
    print("-" * 60)

    files = exporter.client.openall()

    if not files:
        print("✅ No files found - Service Account Drive is clean!")
    else:
        print(f"Found {len(files)} file(s):\n")

        for i, file in enumerate(files, 1):
            print(f"{i}. {file.title}")
            print(f"   ID: {file.id}")
            print(f"   URL: {file.url}")
            print()

        # Ask for confirmation
        print("=" * 60)
        print("⚠️  Do you want to DELETE these files?")
        print("   This will free up space in Service Account Drive.")
        print("=" * 60)
        response = input("Type 'yes' to delete, anything else to cancel: ")

        if response.lower() == 'yes':
            print("\n🗑️  Deleting files...")
            for file in files:
                try:
                    exporter.client.del_spreadsheet(file.id)
                    print(f"✅ Deleted: {file.title}")
                except Exception as e:
                    print(f"❌ Failed to delete {file.title}: {e}")

            print("\n✅ Cleanup complete!")
        else:
            print("\n❌ Cancelled - no files deleted")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
