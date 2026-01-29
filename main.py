"""
Escape Room Calendar Maker - Main Streamlit Application
"""
import streamlit as st
from pathlib import Path
from config import Config
from src.parser import parse_reservations, parse_users
from src.travel import NaverMapsClient
from src.claude_agent import ClaudeScheduler, ScenarioDisplay
from src.sheets import GoogleSheetsExporter, SheetsHelper


def main():
    """Main application entry point."""

    st.set_page_config(
        page_title="Escape Room Calendar Maker",
        page_icon="🔐",
        layout="wide"
    )

    st.title("🔐 Escape Room Calendar Maker")
    st.markdown("""
    방탈출 모임을 위한 자동 일정 생성 도구입니다.
    예약 정보와 참여자 정보를 업로드하면, Claude AI가 최적의 일정을 만들어드립니다.
    """)

    # Validate configuration
    with st.sidebar:
        st.header("⚙️ 설정")

        missing_config = Config.validate()
        if missing_config:
            st.error("❌ API 키가 설정되지 않았습니다")
            st.markdown("다음 항목을 환경 변수로 설정해주세요:")
            for item in missing_config:
                st.code(f"export {item}=...", language="bash")
            st.info(
                "💡 Shell 설정 파일 (예: ~/.bashrc, ~/.zshrc)에 추가 후 `source` 명령으로 적용"
            )
            st.stop()
        else:
            st.success("✅ API 키 설정 완료")

        # Google Sheets status
        st.divider()
        st.subheader("📊 Google Sheets")
        if Config.is_google_sheets_configured():
            st.success("✅ 설정 완료")
        else:
            st.warning("⚠️ 미설정 (선택사항)")
            with st.expander("설정 방법 보기"):
                st.markdown(SheetsHelper.get_setup_instructions())

    # File upload section
    st.header("📁 1. 데이터 업로드")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("예약 정보")
        reservations_file = st.file_uploader(
            "예약 CSV 파일을 업로드하세요",
            type=["csv"],
            key="reservations_file",
            help="방이름, 시작시간, 종료시간, 주소, 테마, 최소인원, 적정인원, 최대인원 컬럼이 필요합니다"
        )

        # Download example
        example_reservations = Path("data/example_reservations.csv")
        if example_reservations.exists():
            with open(example_reservations, "rb") as f:
                st.download_button(
                    "📥 예시 파일 다운로드",
                    f,
                    file_name="example_reservations.csv",
                    mime="text/csv"
                )

    with col2:
        st.subheader("참여자 정보")
        users_file = st.file_uploader(
            "참여자 CSV 파일을 업로드하세요",
            type=["csv"],
            key="users_file",
            help="이름, 참여시작시간, 참여종료시간, 공포포지션 컬럼이 필요합니다"
        )

        # Download example
        example_users = Path("data/example_users.csv")
        if example_users.exists():
            with open(example_users, "rb") as f:
                st.download_button(
                    "📥 예시 파일 다운로드",
                    f,
                    file_name="example_users.csv",
                    mime="text/csv"
                )

    # Parse uploaded files
    if reservations_file and users_file:
        try:
            import pandas as pd

            with st.spinner("📊 데이터 파싱 중..."):
                # Parse to validate format
                reservations = parse_reservations(reservations_file)
                users = parse_users(users_file)

            st.success(f"✅ 예약 {len(reservations)}건, 참여자 {len(users)}명 확인")

            # Display and edit data
            st.header("📊 2. 데이터 확인 및 편집")
            st.info("💡 표를 직접 클릭해서 수정할 수 있습니다. 날짜/시간 컬럼을 클릭하면 선택창이 열립니다. 하단 ➕ 버튼으로 행 추가, 행 선택 후 🗑️ 버튼으로 삭제할 수 있습니다.")

            tab1, tab2 = st.tabs(["예약 정보", "참여자 정보"])

            with tab1:
                # Create editable DataFrame for reservations
                reservations_df = pd.DataFrame([
                    {
                        "방이름": r.room_name,
                        "시작시간": r.start_time,
                        "종료시간": r.end_time,
                        "주소": r.address,
                        "테마": r.theme,
                        "최소인원": r.min_capacity,
                        "적정인원": r.optimal_capacity,
                        "최대인원": r.max_capacity
                    }
                    for r in reservations
                ])

                edited_reservations_df = st.data_editor(
                    reservations_df,
                    num_rows="dynamic",  # Allow adding/removing rows
                    use_container_width=True,
                    key="reservations_editor",
                    column_config={
                        "방이름": st.column_config.TextColumn("방이름", required=True),
                        "시작시간": st.column_config.DatetimeColumn(
                            "시작시간",
                            required=True,
                            format="YYYY-MM-DD HH:mm",
                            help="날짜와 시간을 선택하세요"
                        ),
                        "종료시간": st.column_config.DatetimeColumn(
                            "종료시간",
                            required=True,
                            format="YYYY-MM-DD HH:mm",
                            help="날짜와 시간을 선택하세요"
                        ),
                        "주소": st.column_config.TextColumn("주소", required=True),
                        "테마": st.column_config.TextColumn("테마", required=True),
                        "최소인원": st.column_config.NumberColumn("최소인원", min_value=1, max_value=20, required=True),
                        "적정인원": st.column_config.NumberColumn("적정인원", min_value=1, max_value=20, required=True),
                        "최대인원": st.column_config.NumberColumn("최대인원", min_value=1, max_value=20, required=True),
                    }
                )

                # Store edited data in session state
                st.session_state.edited_reservations_df = edited_reservations_df

            with tab2:
                # Create editable DataFrame for users
                users_df = pd.DataFrame([
                    {
                        "이름": u.name,
                        "참여시작시간": u.available_from,
                        "참여종료시간": u.available_until,
                        "공포포지션": u.horror_position
                    }
                    for u in users
                ])

                edited_users_df = st.data_editor(
                    users_df,
                    num_rows="dynamic",  # Allow adding/removing rows
                    use_container_width=True,
                    key="users_editor",
                    column_config={
                        "이름": st.column_config.TextColumn("이름", required=True),
                        "참여시작시간": st.column_config.DatetimeColumn(
                            "참여시작시간",
                            required=True,
                            format="YYYY-MM-DD HH:mm",
                            help="날짜와 시간을 선택하세요"
                        ),
                        "참여종료시간": st.column_config.DatetimeColumn(
                            "참여종료시간",
                            required=True,
                            format="YYYY-MM-DD HH:mm",
                            help="날짜와 시간을 선택하세요"
                        ),
                        "공포포지션": st.column_config.SelectboxColumn(
                            "공포포지션",
                            options=["탱커", "평민", "쫄"],
                            required=True
                        ),
                    }
                )

                # Store edited data in session state
                st.session_state.edited_users_df = edited_users_df

            # Generate schedule button
            st.header("🤖 3. 일정 생성")

            if st.button("🚀 일정 생성하기", type="primary", use_container_width=True):
                # Parse edited data from DataFrames
                try:
                    from io import StringIO

                    # Convert datetime columns to string format for CSV parsing
                    reservations_csv_df = edited_reservations_df.copy()
                    if "시작시간" in reservations_csv_df.columns:
                        reservations_csv_df["시작시간"] = pd.to_datetime(reservations_csv_df["시작시간"]).dt.strftime("%Y-%m-%d %H:%M")
                    if "종료시간" in reservations_csv_df.columns:
                        reservations_csv_df["종료시간"] = pd.to_datetime(reservations_csv_df["종료시간"]).dt.strftime("%Y-%m-%d %H:%M")

                    users_csv_df = edited_users_df.copy()
                    if "참여시작시간" in users_csv_df.columns:
                        users_csv_df["참여시작시간"] = pd.to_datetime(users_csv_df["참여시작시간"]).dt.strftime("%Y-%m-%d %H:%M")
                    if "참여종료시간" in users_csv_df.columns:
                        users_csv_df["참여종료시간"] = pd.to_datetime(users_csv_df["참여종료시간"]).dt.strftime("%Y-%m-%d %H:%M")

                    # Convert edited DataFrames back to CSV format for parsing
                    reservations_csv = StringIO()
                    reservations_csv_df.to_csv(reservations_csv, index=False)
                    reservations_csv.seek(0)

                    users_csv = StringIO()
                    users_csv_df.to_csv(users_csv, index=False)
                    users_csv.seek(0)

                    # Parse edited data
                    edited_reservations = parse_reservations(reservations_csv)
                    edited_users = parse_users(users_csv)

                    # Store data in session state for generation
                    st.session_state.parsed_reservations_data = edited_reservations
                    st.session_state.parsed_users_data = edited_users
                    st.session_state.should_generate_schedule = True

                except Exception as e:
                    st.error(f"❌ 편집된 데이터 파싱 오류: {str(e)}")
                    st.info("💡 데이터 형식을 확인해주세요. 시간 형식: YYYY-MM-DD HH:MM")

        except ValueError as e:
            st.error(f"❌ 데이터 파싱 오류: {str(e)}")
        except Exception as e:
            st.error(f"❌ 예상치 못한 오류: {str(e)}")

    else:
        st.info("👆 예약 정보와 참여자 정보를 업로드해주세요")

    # Handle schedule generation
    if st.session_state.get("should_generate_schedule", False):
        st.session_state.should_generate_schedule = False  # Reset flag

        reservations = st.session_state.get("parsed_reservations_data", [])
        users = st.session_state.get("parsed_users_data", [])

        if not reservations or not users:
            st.error("데이터를 먼저 업로드해주세요")
        else:
            try:
                st.header("🔄 4. 일정 생성 중...")

                # Progress container
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Step 1: Calculate travel times
                status_text.text("🗺️ 이동 시간 계산 중...")
                progress_bar.progress(10)

                try:
                    travel_client = NaverMapsClient()
                    addresses = list(set([r.address for r in reservations]))

                    # Progress callback for travel time calculation
                    def update_progress(current, total):
                        progress = 10 + int((current / total) * 40)
                        progress_bar.progress(progress)
                        status_text.text(
                            f"🗺️ 이동 시간 계산 중... ({current}/{total})"
                        )

                    travel_matrix = travel_client.get_travel_time_matrix(
                        addresses, progress_callback=update_progress
                    )

                    progress_bar.progress(50)
                    status_text.text(f"✅ {len(addresses)}개 장소 간 이동 시간 계산 완료")

                except Exception as e:
                    st.error(f"❌ 이동 시간 계산 실패: {str(e)}")
                    st.info(
                        "💡 Naver Maps API 연결에 문제가 있을 수 있습니다. API 키를 확인해주세요."
                    )
                    raise

                # Step 2: Generate scenarios with Claude
                status_text.text("🤖 Claude AI가 최적 시나리오를 생성하고 있습니다...")
                progress_bar.progress(60)

                try:
                    claude = ClaudeScheduler()
                    scenarios = claude.generate_scenarios(
                        reservations, users, travel_matrix, num_scenarios=3
                    )
                    progress_bar.progress(100)
                    status_text.text(f"✅ {len(scenarios)}개 시나리오 생성 완료")

                    # Store scenarios in session state to persist across reruns
                    st.session_state.generated_scenarios = scenarios

                except Exception as e:
                    st.error(f"❌ 시나리오 생성 실패: {str(e)}")
                    st.info(
                        "💡 Claude API 연결에 문제가 있을 수 있습니다. API 키를 확인해주세요."
                    )
                    raise

            except Exception as e:
                st.error(f"❌ 일정 생성 오류: {str(e)}")
                import traceback

                st.code(traceback.format_exc())

    # Display scenarios if they exist in session state
    if st.session_state.get("generated_scenarios"):
        scenarios = st.session_state.generated_scenarios

        # Header with clear button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.header("📋 생성된 시나리오")
        with col2:
            st.write("")  # Spacing
            if st.button("🗑️ 일정 초기화", use_container_width=True, help="생성된 일정을 삭제하고 처음부터 다시 시작합니다"):
                st.session_state.generated_scenarios = None
                st.rerun()

        if scenarios:
                    # Create tabs for each scenario
                    tab_names = [
                        f"{s.get('name', f'시나리오 {i+1}')}"
                        for i, s in enumerate(scenarios)
                    ]
                    tabs = st.tabs(tab_names)

                    for tab, scenario in zip(tabs, scenarios):
                        with tab:
                            # Display scenario
                            scenario_text = ScenarioDisplay.format_scenario_summary(
                                scenario
                            )
                            st.markdown(scenario_text)

                            # Export section
                            st.divider()
                            st.subheader("📤 내보내기")

                            # Google Sheets export with URL input
                            sheets_available = Config.is_google_sheets_configured()

                            if sheets_available:
                                st.markdown("**📊 Google Sheets로 내보내기**")
                                # Get Service Account email
                                try:
                                    from src.sheets import GoogleSheetsExporter
                                    exporter_temp = GoogleSheetsExporter()
                                    if exporter_temp.enabled:
                                        service_email = exporter_temp.client.auth.service_account_email
                                    else:
                                        service_email = "N/A"
                                except:
                                    service_email = "N/A"

                                st.info(
                                    f"💡 **사용 방법:**\n"
                                    f"1. 본인 Google Sheets를 열고 '공유' 클릭\n"
                                    f"2. 다음 이메일 추가 (편집자 권한): `{service_email}`\n"
                                    f"3. 스프레드시트 URL을 아래에 붙여넣기\n"
                                    f"4. '시트에 탭 추가' 버튼 클릭\n\n"
                                    f"✨ Service Account 용량 제한 없음!"
                                )

                                spreadsheet_url = st.text_input(
                                    "스프레드시트 URL",
                                    key=f"spreadsheet_url_{scenario.get('scenario_id')}",
                                    placeholder="https://docs.google.com/spreadsheets/d/...",
                                    help="본인이 소유한 Google Sheets URL을 입력하세요"
                                )

                                col1, col2 = st.columns(2)

                                with col1:
                                    if st.button(
                                        "📊 시트에 탭 추가",
                                        key=f"export_sheets_{scenario.get('scenario_id')}",
                                        disabled=not spreadsheet_url,
                                        use_container_width=True,
                                    ):
                                        with st.spinner("📊 시트 탭 추가 중..."):
                                            try:
                                                exporter = GoogleSheetsExporter()
                                                sheet_url = exporter.add_sheet_to_existing_spreadsheet(
                                                    spreadsheet_url, scenario
                                                )

                                                if sheet_url:
                                                    st.success("✅ 시트 탭 추가 완료!")
                                                    st.markdown(
                                                        f"[📊 시트 열기]({sheet_url})",
                                                        unsafe_allow_html=True,
                                                    )
                                                else:
                                                    st.error("시트 추가에 실패했습니다")

                                            except Exception as e:
                                                st.error(f"{str(e)}")

                                with col2:
                                    # CSV download button (moved inside col2)
                                    st.markdown("**📥 CSV 다운로드**")
                                    import pandas as pd

                                    # Convert scenario to CSV format
                                    rows = []
                                    for team_id, assignments in scenario.get("teams", {}).items():
                                        for assignment in assignments:
                                            rows.append({
                                                "팀": f"팀 {team_id}",
                                                "시작시간": assignment.get("start_time", ""),
                                                "종료시간": assignment.get("end_time", ""),
                                                "방이름": assignment.get("room_name", ""),
                                                "테마": assignment.get("theme", ""),
                                                "참여자": ", ".join(assignment.get("members", [])),
                                                "인원": assignment.get("member_count", 0),
                                                "이동시간(분)": assignment.get("travel_time_from_previous", 0),
                                                "메모": assignment.get("notes", "")
                                            })

                                    if rows:
                                        csv_df = pd.DataFrame(rows)
                                        csv_data = csv_df.to_csv(index=False, encoding="utf-8-sig")

                                        st.download_button(
                                            label="다운로드",
                                            data=csv_data,
                                            file_name=f"escape_room_schedule_{scenario.get('scenario_id', 1)}.csv",
                                            mime="text/csv",
                                            key=f"export_csv_{scenario.get('scenario_id')}",
                                            use_container_width=True,
                                        )
                            else:
                                st.warning("⚠️ Google Sheets API가 설정되지 않았습니다. (사이드바 참고)")

                                # CSV download only
                                st.markdown("**📥 CSV 다운로드**")
                                import pandas as pd

                                rows = []
                                for team_id, assignments in scenario.get("teams", {}).items():
                                    for assignment in assignments:
                                        rows.append({
                                            "팀": f"팀 {team_id}",
                                            "시작시간": assignment.get("start_time", ""),
                                            "종료시간": assignment.get("end_time", ""),
                                            "방이름": assignment.get("room_name", ""),
                                            "테마": assignment.get("theme", ""),
                                            "참여자": ", ".join(assignment.get("members", [])),
                                            "인원": assignment.get("member_count", 0),
                                            "이동시간(분)": assignment.get("travel_time_from_previous", 0),
                                            "메모": assignment.get("notes", "")
                                        })

                                if rows:
                                    csv_df = pd.DataFrame(rows)
                                    csv_data = csv_df.to_csv(index=False, encoding="utf-8-sig")

                                    st.download_button(
                                        label="📥 CSV 다운로드",
                                        data=csv_data,
                                        file_name=f"escape_room_schedule_{scenario.get('scenario_id', 1)}.csv",
                                        mime="text/csv",
                                        key=f"export_csv_only_{scenario.get('scenario_id')}",
                                        use_container_width=True,
                                    )
        else:
            st.info("일정을 생성하면 여기에 시나리오가 표시됩니다.")


if __name__ == "__main__":
    main()
