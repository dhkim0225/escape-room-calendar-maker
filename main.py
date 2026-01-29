"""
Escape Room Calendar Maker - Main Streamlit Application
"""
import streamlit as st
from pathlib import Path
from config import Config
from src.parser import parse_reservations, parse_users


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
                with st.spinner("🤖 Claude AI가 일정을 생성하고 있습니다..."):
                    # TODO: Implement scheduling logic
                    st.info("⚠️ 일정 생성 기능은 아직 구현되지 않았습니다")

        except ValueError as e:
            st.error(f"❌ 데이터 파싱 오류: {str(e)}")
        except Exception as e:
            st.error(f"❌ 예상치 못한 오류: {str(e)}")

    else:
        st.info("👆 예약 정보와 참여자 정보를 업로드해주세요")


if __name__ == "__main__":
    main()
