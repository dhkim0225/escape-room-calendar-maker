"""
Google Sheets export functionality.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from config import Config


class GoogleSheetsExporter:
    """Export schedules to Google Sheets."""

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(self):
        """Initialize Google Sheets client."""
        try:
            creds = Credentials.from_service_account_file(
                Config.GOOGLE_SHEETS_CREDENTIALS_PATH, scopes=self.SCOPES
            )
            self.client = gspread.authorize(creds)
            self.enabled = True
        except Exception as e:
            print(f"Google Sheets initialization failed: {str(e)}")
            self.enabled = False
            self.client = None

    def add_sheet_to_existing_spreadsheet(
        self, spreadsheet_url: str, scenario: Dict[str, Any], sheet_title: Optional[str] = None
    ) -> Optional[str]:
        """
        Add a new sheet (tab) to an existing spreadsheet.

        Args:
            spreadsheet_url: URL of the target spreadsheet
            scenario: Scenario dictionary from Claude
            sheet_title: Optional title for the new sheet

        Returns:
            URL of the spreadsheet with new sheet, or None if failed
        """
        if not self.enabled:
            raise ValueError(
                "Google Sheets is not enabled. Please configure credentials.json"
            )

        try:
            # Extract spreadsheet ID from URL
            import re
            match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', spreadsheet_url)
            if not match:
                raise ValueError("❌ 올바른 Google Sheets URL이 아닙니다. URL 형식: https://docs.google.com/spreadsheets/d/...")

            spreadsheet_id = match.group(1)

            # Open existing spreadsheet
            try:
                spreadsheet = self.client.open_by_key(spreadsheet_id)
            except PermissionError:
                raise ValueError(
                    f"❌ 스프레드시트 접근 권한이 없습니다.\n\n"
                    f"해결 방법:\n"
                    f"1. 스프레드시트를 열고 '공유' 버튼 클릭\n"
                    f"2. Service Account 이메일 추가: {self.client.auth.service_account_email}\n"
                    f"3. 권한을 '편집자'로 설정\n\n"
                    f"또는 '링크가 있는 모든 사용자'로 설정하고 '편집자' 권한 부여"
                )
            except Exception as e:
                error_msg = str(e)
                if "403" in error_msg or "permission" in error_msg.lower():
                    raise ValueError(
                        f"❌ 스프레드시트 접근 권한이 없습니다.\n\n"
                        f"해결 방법:\n"
                        f"1. 스프레드시트를 열고 '공유' 버튼 클릭\n"
                        f"2. Service Account 이메일 추가: {self.client.auth.service_account_email}\n"
                        f"3. 권한을 '편집자'로 설정\n\n"
                        f"또는 '링크가 있는 모든 사용자'로 설정하고 '편집자' 권한 부여"
                    )
                else:
                    raise ValueError(f"❌ 스프레드시트를 열 수 없습니다: {error_msg if error_msg else type(e).__name__}")

            # Create sheet title
            if not sheet_title:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                sheet_title = f"{scenario.get('name', '시나리오')} - {timestamp}"

            # Add new worksheet
            try:
                worksheet = spreadsheet.add_worksheet(title=sheet_title, rows=100, cols=20)
            except Exception as e:
                if "already exists" in str(e).lower():
                    # Sheet with same name exists, add number suffix
                    import random
                    sheet_title = f"{sheet_title}_{random.randint(1000, 9999)}"
                    worksheet = spreadsheet.add_worksheet(title=sheet_title, rows=100, cols=20)
                else:
                    raise


            # Format the schedule
            data = self._format_timeline(scenario)

            # Write data
            worksheet.update("A1", data)

            # Apply formatting
            self._apply_formatting(worksheet, len(data), len(data[0]) if data else 0)

            return f"{spreadsheet.url}#gid={worksheet.id}"

        except Exception as e:
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"Failed to create Google Sheet: {error_msg}")
            print(f"Full traceback:\n{error_trace}")

            # Check for specific errors
            if "storageQuotaExceeded" in error_msg or "storage quota" in error_msg.lower():
                # This is actually a Service Account limitation
                raise ValueError(
                    "❌ Service Account로 생성된 시트는 공유 드라이브에 저장됩니다.\n"
                    "해결 방법:\n"
                    "1. Service Account 이메일을 Google Drive에서 찾아 파일 삭제\n"
                    "2. 또는 '📥 CSV 다운로드' 버튼을 사용하세요"
                )
            elif "403" in error_msg:
                raise ValueError(f"❌ Google Sheets API 권한 오류: {error_msg}")
            else:
                raise ValueError(f"❌ Google Sheets 생성 실패: {error_msg}")

    def _format_timeline(self, scenario: Dict[str, Any]) -> List[List[str]]:
        """
        Format scenario as a timeline table.

        Returns:
            2D array for Google Sheets
        """
        teams = scenario.get("teams", {})
        if not teams:
            return [["오류: 팀 데이터가 없습니다"]]

        # Build timeline
        data = []

        # Header
        data.append(["시간"] + [f"팀 {team_id}" for team_id in sorted(teams.keys())])

        # Collect all time slots
        all_times = set()
        for assignments in teams.values():
            for assignment in assignments:
                all_times.add(assignment["start_time"])
                all_times.add(assignment["end_time"])

        # Sort times
        sorted_times = sorted(list(all_times))

        # Build timeline rows
        for i in range(len(sorted_times) - 1):
            start = sorted_times[i]
            end = sorted_times[i + 1] if i + 1 < len(sorted_times) else ""

            row = [f"{start}-{end}"]

            # For each team, find what they're doing in this time slot
            for team_id in sorted(teams.keys()):
                cell_content = ""
                for assignment in teams[team_id]:
                    if assignment["start_time"] == start:
                        cell_content = f"{assignment['room_name']}\n({assignment['theme']})\n"
                        member_names = assignment.get("members", [])
                        if len(member_names) <= 3:
                            cell_content += ", ".join(member_names)
                        else:
                            cell_content += f"{', '.join(member_names[:3])} 외 {len(member_names)-3}명"

                        # Add travel time if exists
                        travel = assignment.get("travel_time_from_previous", 0)
                        if travel > 0:
                            cell_content = f"[이동 {travel}분]\n" + cell_content

                        # Add notes if exists
                        notes = assignment.get("notes", "")
                        if notes and "점심" in notes or "저녁" in notes or "식사" in notes:
                            cell_content += f"\n📍 {notes}"

                row.append(cell_content)

            data.append(row)

        # Add summary section
        data.append([])
        data.append(["📊 시나리오 정보"])
        data.append(["이름", scenario.get("name", "")])
        data.append(["설명", scenario.get("description", "")])
        data.append([])
        data.append(["✅ 장점", scenario.get("pros", "")])
        data.append(["⚠️ 단점", scenario.get("cons", "")])

        return data

    def _apply_formatting(self, worksheet, num_rows: int, num_cols: int):
        """Apply basic formatting to the worksheet."""
        try:
            # Format header row (bold, centered)
            worksheet.format(
                "A1:Z1",
                {
                    "textFormat": {"bold": True, "fontSize": 11},
                    "horizontalAlignment": "CENTER",
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                },
            )

            # Auto-resize columns
            worksheet.columns_auto_resize(0, num_cols)

        except Exception as e:
            print(f"Formatting failed (non-critical): {str(e)}")


class SheetsHelper:
    """Helper functions for Google Sheets operations."""

    @staticmethod
    def is_available() -> bool:
        """Check if Google Sheets API is available."""
        from pathlib import Path

        return Path(Config.GOOGLE_SHEETS_CREDENTIALS_PATH).exists()

    @staticmethod
    def get_setup_instructions() -> str:
        """Get instructions for setting up Google Sheets API."""
        return """
### Google Sheets API 설정 방법

1. **Google Cloud Console 접속**
   - https://console.cloud.google.com/

2. **프로젝트 생성**
   - "새 프로젝트" 클릭
   - 프로젝트 이름 입력 (예: escape-room-scheduler)

3. **API 활성화**
   - "API 및 서비스" → "라이브러리"
   - "Google Sheets API" 검색 후 활성화
   - "Google Drive API" 검색 후 활성화

4. **서비스 계정 생성**
   - "API 및 서비스" → "사용자 인증 정보"
   - "사용자 인증 정보 만들기" → "서비스 계정"
   - 서비스 계정 이름 입력 후 생성

5. **JSON 키 다운로드**
   - 생성된 서비스 계정 클릭
   - "키" 탭 → "키 추가" → "새 키 만들기"
   - JSON 형식 선택
   - 다운로드한 파일을 `credentials.json`으로 프로젝트 루트에 저장

6. **완료!**
   - 이제 "Google Sheets로 내보내기" 버튼이 활성화됩니다
"""
