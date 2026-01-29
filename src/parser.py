"""
CSV parsing module for reservations and users.
"""
import pandas as pd
from typing import BinaryIO
from .models import Reservation, User


def parse_reservations(file: BinaryIO) -> list[Reservation]:
    """
    Parse reservations CSV file.

    Args:
        file: Binary file object (from Streamlit file uploader)

    Returns:
        List of Reservation objects

    Raises:
        ValueError: If CSV format is invalid
    """
    try:
        df = pd.read_csv(file)

        # Validate required columns
        required_columns = ["방이름", "시작시간", "종료시간", "주소", "테마", "최소인원", "적정인원", "최대인원"]
        missing_columns = set(required_columns) - set(df.columns)

        if missing_columns:
            raise ValueError(f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}")

        # Parse each row into Reservation model
        reservations = []
        errors = []

        for line_num, (_, row) in enumerate(df.iterrows(), start=2):
            try:
                reservation = Reservation(**row.to_dict())
                reservations.append(reservation)
            except Exception as e:
                errors.append(f"행 {line_num}: {str(e)}")

        if errors:
            raise ValueError("\n".join(["예약 데이터 파싱 오류:"] + errors))

        return reservations

    except pd.errors.EmptyDataError:
        raise ValueError("CSV 파일이 비어있습니다")
    except Exception as e:
        raise ValueError(f"CSV 파일을 읽을 수 없습니다: {str(e)}")


def parse_users(file: BinaryIO) -> list[User]:
    """
    Parse users CSV file.

    Args:
        file: Binary file object (from Streamlit file uploader)

    Returns:
        List of User objects

    Raises:
        ValueError: If CSV format is invalid
    """
    try:
        df = pd.read_csv(file)

        # Validate required columns
        required_columns = ["이름", "참여시작시간", "참여종료시간", "공포포지션"]
        missing_columns = set(required_columns) - set(df.columns)

        if missing_columns:
            raise ValueError(f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}")

        # Parse each row into User model
        users = []
        errors = []

        for line_num, (_, row) in enumerate(df.iterrows(), start=2):
            try:
                user = User(**row.to_dict())
                users.append(user)
            except Exception as e:
                errors.append(f"행 {line_num}: {str(e)}")

        if errors:
            raise ValueError("\n".join(["유저 데이터 파싱 오류:"] + errors))

        return users

    except pd.errors.EmptyDataError:
        raise ValueError("CSV 파일이 비어있습니다")
    except Exception as e:
        raise ValueError(f"CSV 파일을 읽을 수 없습니다: {str(e)}")
