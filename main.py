"""
Escape Room Calendar Maker - Main Streamlit Application
"""
import streamlit as st
from pathlib import Path
from config import Config
from src.parser import parse_reservations, parse_users
from src.travel import NaverMapsClient
from src.claude_agent import ClaudeScheduler, ScenarioDisplay


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
            st.markdown("다음 항목을 `.env` 파일에 설정해주세요:")
            for item in missing_config:
                st.code(item, language=None)
            st.stop()
        else:
            st.success("✅ API 키 설정 완료")

    # File upload section
    st.header("📁 1. 데이터 업로드")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("예약 정보")
        reservations_file = st.file_uploader(
            "예약 CSV 파일을 업로드하세요",
            type=["csv"],
            key="reservations",
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
            key="users",
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
            with st.spinner("📊 데이터 파싱 중..."):
                reservations = parse_reservations(reservations_file)
                users = parse_users(users_file)

            st.success(f"✅ 예약 {len(reservations)}건, 참여자 {len(users)}명 확인")

            # Display parsed data
            st.header("📊 2. 데이터 확인")

            tab1, tab2 = st.tabs(["예약 정보", "참여자 정보"])

            with tab1:
                st.dataframe(
                    [
                        {
                            "방이름": r.room_name,
                            "시작시간": r.start_time.strftime("%m/%d %H:%M"),
                            "종료시간": r.end_time.strftime("%m/%d %H:%M"),
                            "주소": r.address,
                            "테마": r.theme,
                            "인원": f"{r.min_capacity}-{r.optimal_capacity}-{r.max_capacity}명"
                        }
                        for r in reservations
                    ],
                    use_container_width=True
                )

            with tab2:
                st.dataframe(
                    [
                        {
                            "이름": u.name,
                            "참여시작": u.available_from.strftime("%m/%d %H:%M"),
                            "참여종료": u.available_until.strftime("%m/%d %H:%M"),
                            "공포포지션": u.horror_position
                        }
                        for u in users
                    ],
                    use_container_width=True
                )

            # Generate schedule button
            st.header("🤖 3. 일정 생성")

            if st.button("🚀 일정 생성하기", type="primary", use_container_width=True):
                # Store data in session state for generation
                st.session_state.reservations = reservations
                st.session_state.users = users
                st.session_state.generate_schedule = True

        except ValueError as e:
            st.error(f"❌ 데이터 파싱 오류: {str(e)}")
        except Exception as e:
            st.error(f"❌ 예상치 못한 오류: {str(e)}")

    else:
        st.info("👆 예약 정보와 참여자 정보를 업로드해주세요")

    # Handle schedule generation
    if st.session_state.get("generate_schedule", False):
        st.session_state.generate_schedule = False  # Reset flag

        reservations = st.session_state.get("reservations", [])
        users = st.session_state.get("users", [])

        if not reservations or not users:
            st.error("데이터를 먼저 업로드해주세요")
        else:
            try:
                st.header("🔄 4. 일정 생성 중...")

                # Step 1: Calculate travel times
                with st.spinner("🗺️ 이동 시간 계산 중..."):
                    travel_client = NaverMapsClient()
                    addresses = list(set([r.address for r in reservations]))
                    travel_matrix = travel_client.get_travel_time_matrix(addresses)
                    st.success(f"✅ {len(addresses)}개 장소 간 이동 시간 계산 완료")

                # Step 2: Generate scenarios with Claude
                with st.spinner("🤖 Claude AI가 최적 시나리오를 생성하고 있습니다..."):
                    claude = ClaudeScheduler()
                    scenarios = claude.generate_scenarios(
                        reservations, users, travel_matrix, num_scenarios=3
                    )
                    st.success(f"✅ {len(scenarios)}개 시나리오 생성 완료")

                # Step 3: Display scenarios
                st.header("📋 5. 생성된 시나리오")

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

                            # Export button (placeholder for Phase 3)
                            st.button(
                                "📊 Google Sheets로 내보내기",
                                key=f"export_{scenario.get('scenario_id')}",
                                disabled=True,
                                help="Phase 3에서 구현 예정",
                            )
                else:
                    st.warning("시나리오 생성에 실패했습니다")

            except Exception as e:
                st.error(f"❌ 일정 생성 오류: {str(e)}")
                import traceback

                st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
