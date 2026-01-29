"""
Integration test for the full pipeline.
"""
import sys
from io import StringIO
from src.parser import parse_reservations, parse_users
from src.travel import NaverMapsClient
from src.claude_agent import ClaudeScheduler

# Test data
reservations_csv = """방이름,시작시간,종료시간,주소,테마,최소인원,적정인원,최대인원
미스터리 하우스,2026-02-15 14:00,2026-02-15 16:00,서울 강남구 테헤란로 123,추리,2,4,5
공포의 지하실,2026-02-15 16:30,2026-02-15 18:30,서울 마포구 홍익로 456,공포,2,3,4"""

users_csv = """이름,참여시작시간,참여종료시간,공포포지션
홍길동,2026-02-15 13:00,2026-02-15 22:00,탱커
김철수,2026-02-15 14:00,2026-02-15 20:00,평민
이영희,2026-02-15 13:00,2026-02-15 22:00,쫄
박민수,2026-02-15 13:30,2026-02-15 21:30,평민"""

def main():
    print("=" * 60)
    print("🧪 Integration Test")
    print("=" * 60)

    # Step 1: Parse CSV
    print("\n1️⃣ Parsing CSV...")
    try:
        reservations = parse_reservations(StringIO(reservations_csv))
        users = parse_users(StringIO(users_csv))
        print(f"✅ Parsed: {len(reservations)} reservations, {len(users)} users")
    except Exception as e:
        print(f"❌ CSV parsing failed: {e}")
        return 1

    # Step 2: Calculate travel times
    print("\n2️⃣ Calculating travel times...")
    try:
        travel_client = NaverMapsClient()
        addresses = list(set([r.address for r in reservations]))
        print(f"   Addresses: {addresses}")

        travel_matrix = travel_client.get_travel_time_matrix(addresses)
        print(f"✅ Travel matrix calculated: {len(travel_matrix)} pairs")
        for (start, end), time in travel_matrix.items():
            if start != end:
                print(f"   {start[:20]}... → {end[:20]}...: {time}분")
    except Exception as e:
        print(f"❌ Travel time calculation failed: {e}")
        print("   Continuing with mock data...")
        travel_matrix = {}
        for i, start in enumerate(addresses):
            for j, end in enumerate(addresses):
                travel_matrix[(start, end)] = 0 if i == j else 30

    # Step 3: Generate scenarios with Claude
    print("\n3️⃣ Generating scenarios with Claude...")
    try:
        claude = ClaudeScheduler()
        scenarios = claude.generate_scenarios(
            reservations, users, travel_matrix, num_scenarios=2
        )
        print(f"✅ Generated {len(scenarios)} scenarios")

        # Display scenarios
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{'='*60}")
            print(f"Scenario {i}: {scenario.get('name', 'N/A')}")
            print(f"{'='*60}")
            print(f"Description: {scenario.get('description', 'N/A')}")

            teams = scenario.get("teams", {})
            print(f"Teams: {len(teams)}")
            for team_id, assignments in teams.items():
                print(f"\n  Team {team_id}: {len(assignments)} assignments")
                for j, assignment in enumerate(assignments, 1):
                    print(f"    {j}. {assignment.get('room_name', 'N/A')}")
                    print(f"       Time: {assignment.get('start_time', 'N/A')} - {assignment.get('end_time', 'N/A')}")
                    print(f"       Members: {', '.join(assignment.get('members', []))}")

            print(f"\nPros: {scenario.get('pros', 'N/A')[:100]}...")
            print(f"Cons: {scenario.get('cons', 'N/A')[:100]}...")

        return 0

    except Exception as e:
        print(f"❌ Claude scenario generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
