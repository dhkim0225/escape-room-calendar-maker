"""
Scheduling logic and constraint validation.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from src.models import Reservation, User, TeamAssignment, Schedule


class ScheduleConstraints:
    """Constraints for schedule generation."""

    # Meal times
    LUNCH_START = 11  # 11:00
    LUNCH_END = 14  # 14:00
    LUNCH_DURATION_MIN = 60  # 1 hour
    LUNCH_DURATION_MAX = 90  # 1.5 hours

    DINNER_START = 17  # 17:00
    DINNER_END = 20  # 20:00
    DINNER_DURATION = 120  # 2 hours

    # Team balance
    MAX_GATHERING_TIME_DIFF = 30  # 30 minutes difference is acceptable


class ScheduleValidator:
    """Validate scheduling constraints."""

    @staticmethod
    def is_user_available(user: User, start_time: datetime, end_time: datetime) -> bool:
        """Check if user is available during the given time period."""
        return user.available_from <= start_time and user.available_until >= end_time

    @staticmethod
    def is_capacity_valid(
        reservation: Reservation, num_members: int, flexible: bool = True
    ) -> bool:
        """
        Check if the number of members fits the room capacity.

        Args:
            reservation: The escape room reservation
            num_members: Number of team members
            flexible: If True, allow slight over/under capacity (±1-2 people)
        """
        if flexible:
            # Allow 1-2 people flexibility
            return (
                reservation.min_capacity - 1
                <= num_members
                <= reservation.max_capacity + 1
            )
        else:
            return (
                reservation.min_capacity <= num_members <= reservation.max_capacity
            )

    @staticmethod
    def is_travel_time_feasible(
        prev_reservation: Reservation,
        next_reservation: Reservation,
        travel_time_minutes: int,
    ) -> bool:
        """
        Check if there's enough time to travel between two reservations.

        Args:
            prev_reservation: Previous escape room
            next_reservation: Next escape room
            travel_time_minutes: Travel time in minutes

        Returns:
            True if feasible, False otherwise
        """
        time_gap = (
            next_reservation.start_time - prev_reservation.end_time
        ).total_seconds() / 60

        # Need at least travel_time minutes between rooms
        return time_gap >= travel_time_minutes

    @staticmethod
    def needs_horror_tank(reservation: Reservation) -> bool:
        """Check if this reservation is a horror theme that needs a tank."""
        return "공포" in reservation.theme.lower()


class ScheduleFormatter:
    """Format schedule data for Claude API and display."""

    @staticmethod
    def format_reservations_for_claude(reservations: List[Reservation]) -> str:
        """Format reservations as text for Claude."""
        lines = ["예약 정보:"]
        for i, r in enumerate(reservations, 1):
            lines.append(
                f"{i}. {r.room_name}"
                f" | {r.start_time.strftime('%H:%M')}-{r.end_time.strftime('%H:%M')}"
                f" | {r.address}"
                f" | {r.theme}"
                f" | 인원: {r.min_capacity}-{r.optimal_capacity}-{r.max_capacity}명"
            )
        return "\n".join(lines)

    @staticmethod
    def format_users_for_claude(users: List[User]) -> str:
        """Format users as text for Claude."""
        lines = ["참여자 정보:"]

        # Group by horror position
        tanks = [u for u in users if u.horror_position == "탱커"]
        civilians = [u for u in users if u.horror_position == "평민"]
        scaredy_cats = [u for u in users if u.horror_position == "쫄"]

        lines.append(f"- 탱커 ({len(tanks)}명): {', '.join(u.name for u in tanks)}")
        lines.append(
            f"- 평민 ({len(civilians)}명): {', '.join(u.name for u in civilians)}"
        )
        lines.append(
            f"- 쫄 ({len(scaredy_cats)}명): {', '.join(u.name for u in scaredy_cats)}"
        )

        return "\n".join(lines)

    @staticmethod
    def format_travel_times_for_claude(
        travel_matrix: Dict[Tuple[str, str], int]
    ) -> str:
        """Format travel time matrix for Claude."""
        lines = ["이동 시간 (분):"]

        # Get unique addresses
        addresses = list(set([addr for pair in travel_matrix.keys() for addr in pair]))

        for i, start in enumerate(addresses):
            for end in addresses[i + 1 :]:  # Only show one direction
                time = travel_matrix.get((start, end), 0)
                if time > 0:
                    lines.append(f"- {start} → {end}: {time}분")

        return "\n".join(lines)

    @staticmethod
    def format_constraints_for_claude() -> str:
        """Format scheduling constraints for Claude."""
        return f"""
제약 조건:
1. 식사 시간:
   - 점심: {ScheduleConstraints.LUNCH_START}:00-{ScheduleConstraints.LUNCH_END}:00 사이 {ScheduleConstraints.LUNCH_DURATION_MIN}-{ScheduleConstraints.LUNCH_DURATION_MAX}분
   - 저녁: {ScheduleConstraints.DINNER_START}:00-{ScheduleConstraints.DINNER_END}:00 사이 {ScheduleConstraints.DINNER_DURATION}분
   - 팀별로 식사 시간이 달라도 됨

2. 공포 테마 포지션:
   - 공포 테마가 여러 개 있으면 탱커를 분산 배치
   - 쫄은 탱커와 같은 팀에 배정하는 것이 바람직

3. 팀 인원:
   - 각 방의 적정 인원을 기준으로 하되, ±1-2명 유연하게 허용

4. 이동 시간:
   - 이동 시간을 고려하여 물리적으로 불가능한 스케줄 제외

5. 팀 균등 분배:
   - 모든 팀이 비슷한 수의 방탈출 경험 (최우선)
   - 테마 다양성 고려

6. 회포 시간:
   - 마지막 방탈출 종료 시간 차이 {ScheduleConstraints.MAX_GATHERING_TIME_DIFF}분 이내 (선택적)
"""


class ScheduleAnalyzer:
    """Analyze and score schedules."""

    @staticmethod
    def calculate_balance_score(schedule: Schedule) -> float:
        """
        Calculate how balanced the schedule is across teams.

        Returns:
            Score from 0.0 to 1.0 (1.0 = perfectly balanced)
        """
        if not schedule.teams:
            return 0.0

        # Count number of assignments per team
        assignment_counts = [len(assignments) for assignments in schedule.teams.values()]

        if not assignment_counts:
            return 0.0

        # Calculate variance
        mean_count = sum(assignment_counts) / len(assignment_counts)
        variance = sum((c - mean_count) ** 2 for c in assignment_counts) / len(
            assignment_counts
        )

        # Convert to score (lower variance = higher score)
        # Max expected variance is (mean_count)^2, so normalize
        if mean_count == 0:
            return 1.0

        normalized_variance = variance / (mean_count**2)
        score = max(0.0, 1.0 - normalized_variance)

        return score

    @staticmethod
    def calculate_efficiency_score(schedule: Schedule) -> float:
        """
        Calculate efficiency of the schedule (minimal idle time).

        Returns:
            Score from 0.0 to 1.0 (1.0 = most efficient)
        """
        # TODO: Implement based on actual schedule data
        # For now, return a placeholder
        return 0.8
