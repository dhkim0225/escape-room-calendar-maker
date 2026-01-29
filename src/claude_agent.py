"""
Claude API integration for schedule generation.
"""
import json
import time
from typing import List, Dict, Any
from anthropic import Anthropic
from config import Config
from src.models import Reservation, User, Schedule
from src.scheduler import ScheduleFormatter


class ClaudeScheduler:
    """Use Claude API to generate optimized schedules."""

    def __init__(self):
        """Initialize Claude client."""
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not set")

        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    def generate_scenarios(
        self,
        reservations: List[Reservation],
        users: List[User],
        travel_matrix: Dict[tuple, int],
        num_scenarios: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple schedule scenarios using Claude.

        Args:
            reservations: List of escape room reservations
            users: List of participants
            travel_matrix: Travel time matrix between addresses
            num_scenarios: Number of different scenarios to generate

        Returns:
            List of scenario dictionaries
        """
        # Format data for Claude
        reservations_text = ScheduleFormatter.format_reservations_for_claude(
            reservations
        )
        users_text = ScheduleFormatter.format_users_for_claude(users)
        travel_text = ScheduleFormatter.format_travel_times_for_claude(travel_matrix)
        constraints_text = ScheduleFormatter.format_constraints_for_claude()

        # Build prompt
        prompt = self._build_prompt(
            reservations_text, users_text, travel_text, constraints_text, num_scenarios
        )

        # Call Claude API with retry logic
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Parse response
                # Get text from first content block
                first_block = response.content[0]
                if hasattr(first_block, "text"):
                    response_text = first_block.text
                else:
                    raise ValueError("Unexpected response format from Claude")

                # Extract JSON from response
                scenarios = self._parse_scenarios(response_text)

                if scenarios:
                    return scenarios
                else:
                    print("⚠️ Claude response text:")
                    print(response_text[:1000])  # First 1000 chars for debugging
                    raise ValueError("No scenarios returned from Claude")

            except Exception as e:
                if attempt < max_retries - 1:
                    print(
                        f"Claude API error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"Claude API error (final attempt): {str(e)}")
                    raise

        # Should never reach here due to raise in except block
        return []

    def _build_prompt(
        self,
        reservations_text: str,
        users_text: str,
        travel_text: str,
        constraints_text: str,
        num_scenarios: int,
    ) -> str:
        """Build the prompt for Claude."""
        return f"""당신은 방탈출 모임을 위한 일정 생성 전문가입니다.

주어진 예약 정보와 참여자 정보를 바탕으로 {num_scenarios}가지 최적의 스케줄 시나리오를 생성해주세요.

{reservations_text}

{users_text}

{travel_text}

{constraints_text}

목표:
1. **팀 균등 분배 (최우선)**: 모든 팀이 비슷한 수의 방탈출을 경험하도록
2. **테마 다양성**: 한 팀이 같은 테마만 하지 않도록
3. **공포 포지션 고려**: 공포 테마는 탱커 분산 배치
4. **식사 시간 확보**: 점심/저녁 시간대 고려
5. **이동 효율성**: 불필요한 이동 최소화

각 시나리오는 다른 최적화 목표를 강조해야 합니다:
- 시나리오 1: 팀 균형 최우선
- 시나리오 2: 이동 거리/시간 최소화
- 시나리오 3: 식사 시간 여유 확보

반드시 다음 JSON 형식으로 응답해주세요:

```json
{{
  "scenarios": [
    {{
      "scenario_id": 1,
      "name": "팀 균형 우선",
      "description": "모든 팀이 동일한 수의 방탈출을 경험하도록 최적화",
      "teams": {{
        "1": [
          {{
            "room_name": "방이름",
            "start_time": "14:00",
            "end_time": "16:00",
            "address": "주소",
            "theme": "테마",
            "members": ["참여자1", "참여자2"],
            "member_count": 2,
            "travel_time_from_previous": 0,
            "notes": "특이사항 (예: 점심시간, 공포테마 등)"
          }}
        ],
        "2": [...]
      }},
      "pros": "장점 설명",
      "cons": "단점 설명"
    }}
  ]
}}
```

JSON만 출력하고 다른 설명은 포함하지 마세요."""

    def _parse_scenarios(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse scenarios from Claude's response.

        Args:
            response_text: Raw text response from Claude

        Returns:
            List of parsed scenario dictionaries
        """
        # Find JSON in response (between ``` markers or directly)
        text = response_text.strip()

        # Remove markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
            return data.get("scenarios", [])
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Response text: {text}")
            raise ValueError("Failed to parse Claude's response as JSON")


class ScenarioDisplay:
    """Format scenarios for display in Streamlit."""

    @staticmethod
    def format_scenario_summary(scenario: Dict[str, Any]) -> str:
        """
        Format a scenario as a readable summary.

        Args:
            scenario: Scenario dictionary from Claude

        Returns:
            Formatted text summary
        """
        lines = []
        lines.append(f"## {scenario.get('name', '시나리오')}")
        lines.append(f"*{scenario.get('description', '')}*\n")

        # Team summaries
        teams = scenario.get("teams", {})
        if not teams:
            lines.append("⚠️ 팀 정보가 없습니다.")
            return "\n".join(lines)

        for team_id, assignments in teams.items():
            lines.append(f"### 🎯 팀 {team_id}")

            if not assignments:
                lines.append("   - 배정된 일정 없음\n")
                continue

            for i, assignment in enumerate(assignments, 1):
                # Safely get values with defaults
                start_time = assignment.get("start_time", "시간 미정")
                end_time = assignment.get("end_time", "시간 미정")
                room_name = assignment.get("room_name", "방 이름 없음")
                theme = assignment.get("theme", "테마 없음")
                members = assignment.get("members", [])
                member_count = assignment.get("member_count", len(members))

                time_str = f"{start_time}-{end_time}"
                members_str = ", ".join(members) if members else "참여자 없음"

                # Theme emoji
                theme_emoji = "🔪" if "공포" in theme else "🧩"

                lines.append(
                    f"**{i}. {time_str}** {theme_emoji} **{room_name}** ({theme})"
                )
                lines.append(f"   - 👥 참여자 ({member_count}명): {members_str}")

                travel_time = assignment.get("travel_time_from_previous", 0)
                if travel_time > 0:
                    lines.append(f"   - 🚗 이동 시간: {travel_time}분")

                notes = assignment.get("notes", "")
                if notes:
                    lines.append(f"   - 📝 {notes}")

                lines.append("")

        # Pros and cons
        lines.append("---")
        lines.append("### ✅ 장점")
        lines.append(scenario.get("pros", "정보 없음"))
        lines.append("\n### ⚠️ 단점")
        lines.append(scenario.get("cons", "정보 없음"))

        return "\n".join(lines)
