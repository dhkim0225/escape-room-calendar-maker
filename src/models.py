"""
Data models for escape room scheduling.
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class Reservation(BaseModel):
    """Model for an escape room reservation."""

    room_name: str = Field(alias="방이름")
    start_time: datetime = Field(alias="시작시간")
    end_time: datetime = Field(alias="종료시간")
    address: str = Field(alias="주소")
    theme: str = Field(alias="테마")
    min_capacity: int = Field(alias="최소인원")
    optimal_capacity: int = Field(alias="적정인원")
    max_capacity: int = Field(alias="최대인원")

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        """Parse datetime from string if needed."""
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d %H:%M")
        return value

    @field_validator("min_capacity", "optimal_capacity", "max_capacity")
    @classmethod
    def validate_capacity(cls, value):
        """Ensure capacity is positive."""
        if value <= 0:
            raise ValueError("Capacity must be positive")
        return value

    class Config:
        populate_by_name = True


class User(BaseModel):
    """Model for a user/participant."""

    name: str = Field(alias="이름")
    available_from: datetime = Field(alias="참여시작시간")
    available_until: datetime = Field(alias="참여종료시간")
    horror_position: Literal["탱커", "평민", "쫄"] = Field(alias="공포포지션")

    @field_validator("available_from", "available_until", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        """Parse datetime from string if needed."""
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d %H:%M")
        return value

    @field_validator("horror_position")
    @classmethod
    def validate_position(cls, value):
        """Validate horror position."""
        valid_positions = ["탱커", "평민", "쫄"]
        if value not in valid_positions:
            raise ValueError(f"공포포지션은 {', '.join(valid_positions)} 중 하나여야 합니다")
        return value

    class Config:
        populate_by_name = True


class TeamAssignment(BaseModel):
    """Model for a team assignment to a specific escape room."""

    team_id: int
    reservation: Reservation
    members: list[User]
    travel_time_from_previous: int = 0  # minutes


class Schedule(BaseModel):
    """Model for a complete schedule scenario."""

    scenario_id: int
    teams: dict[int, list[TeamAssignment]]  # team_id -> list of assignments
    score: dict[str, float]  # balance, efficiency, etc.
    notes: str = ""
