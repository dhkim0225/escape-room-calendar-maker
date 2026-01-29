# 🔐 Escape Room Calendar Maker

방탈출 모임을 위한 AI 기반 자동 일정 생성 도구

## 📋 주요 기능

- 📊 **CSV 파일 입력**: 예약 정보와 참여자 정보를 CSV로 간편하게 업로드
- ✏️ **UI 내 데이터 편집**:
  - 날짜/시간 선택기로 쉬운 시간 입력
  - 행 추가/삭제로 자유로운 데이터 관리
  - 드롭다운으로 공포포지션 선택
- 🤖 **Claude AI 최적 일정 생성**:
  - 3가지 시나리오 자동 제안
  - 각 시나리오의 장단점 분석
  - 세션 유지 중 일정 계속 표시
- 🗺️ **Naver Maps API 이동 시간 계산**: 실제 길찾기 기반 정확한 이동 시간
- 👥 **똑똑한 팀 구성**:
  - 팀 균등 분배
  - 공포 포지션 고려 (탱커/평민/쫄)
  - 방 인원 제한 준수
- 🍽️ **식사 시간 자동 배치**: 점심/저녁 시간대 자동 고려
- 📈 **Google Sheets 내보내기**: 본인 스프레드시트에 탭 추가 방식으로 용량 제한 없음

## 🚀 빠른 시작

### 1️⃣ 필수 API 키 설정

#### 1-1. Anthropic API 키 발급
1. [Anthropic Console](https://console.anthropic.com/) 접속
2. 계정 생성/로그인
3. API Keys 메뉴에서 새 키 생성
4. 발급된 키 복사 (예: `sk-ant-api03-...`)

#### 1-2. Naver Maps API 키 발급
1. [Naver Cloud Platform](https://www.ncloud.com/) 접속
2. 계정 생성/로그인
3. **AI·NAVER API** → **Application 등록**
4. 서비스 선택: **Maps** → **Geocoding**, **Directions 5**
5. Client ID와 Client Secret 복사

#### 1-3. 환경 변수 설정

**Shell 설정 파일에 API 키 추가:**

- **Bash**: `~/.bashrc` 또는 `~/.bash_profile`
- **Zsh**: `~/.zshrc`
- **Fish**: `~/.config/fish/config.fish`

```bash
# Bash/Zsh 사용자
export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"
export NAVER_MAPS_CLIENT_ID="your-client-id-here"
export NAVER_MAPS_CLIENT_SECRET="your-client-secret-here"
```

```fish
# Fish 사용자
set -x ANTHROPIC_API_KEY "sk-ant-your-api-key-here"
set -x NAVER_MAPS_CLIENT_ID "your-client-id-here"
set -x NAVER_MAPS_CLIENT_SECRET "your-client-secret-here"
```

**환경 변수 적용:**
```bash
# Bash/Zsh
source ~/.bashrc  # 또는 ~/.zshrc

# Fish
source ~/.config/fish/config.fish
```

### 2️⃣ Google Sheets 설정 (선택사항)

Google Sheets로 일정을 내보내려면 Service Account 설정이 필요합니다.

#### 2-1. Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 상단의 **"프로젝트 선택"** → **"새 프로젝트"** 클릭
3. 프로젝트 이름 입력 (예: `escape-room-scheduler`)
4. **"만들기"** 클릭

#### 2-2. API 활성화

1. 왼쪽 메뉴: **"API 및 서비스"** → **"라이브러리"**
2. **"Google Sheets API"** 검색 → 클릭 → **"사용"** 버튼
3. **"Google Drive API"** 검색 → 클릭 → **"사용"** 버튼

#### 2-3. Service Account 생성 및 키 다운로드

1. 왼쪽 메뉴: **"API 및 서비스"** → **"사용자 인증 정보"**
2. 상단의 **"사용자 인증 정보 만들기"** → **"서비스 계정"** 선택
3. 서비스 계정 세부정보:
   - 이름: `escape-room-service-account` (원하는 이름)
   - ID는 자동 생성됨
   - **"만들기 및 계속하기"** 클릭
4. 역할 선택 (선택사항): 건너뛰기 가능 → **"계속"** 클릭
5. **"완료"** 클릭
6. 생성된 서비스 계정 클릭
7. 상단 **"키"** 탭 → **"키 추가"** → **"새 키 만들기"**
8. 키 유형: **JSON** 선택 → **"만들기"**
9. JSON 파일 자동 다운로드됨

#### 2-4. JSON 키 파일 배치

다운로드한 JSON 파일을 **프로젝트 루트**에 `credentials.json`으로 저장:

```bash
cd /path/to/escape-room-calendar-maker
mv ~/Downloads/your-project-xxxxx.json ./credentials.json
```

#### 2-5. Google Sheets에 권한 부여 (사용 시 필요)

일정을 내보낼 때마다 다음 작업 필요:

1. **본인의 Google Sheets 열기**
2. 우측 상단 **"공유"** 버튼 클릭
3. **Service Account 이메일 추가**
   - 이메일은 앱 UI에 표시됨 (예: `xxx@xxx.iam.gserviceaccount.com`)
   - **credentials.json** 파일에서도 확인 가능 (`client_email` 필드)
4. 권한: **"편집자"** 선택
5. **"완료"** 클릭

> **💡 팁**: "링크가 있는 모든 사용자"로 설정하고 "편집자" 권한을 주면 매번 이메일을 추가하지 않아도 됩니다.

> **참고**: Google Sheets 설정 없이도 CSV 다운로드로 일정을 저장할 수 있습니다.

### 3️⃣ Docker 서비스 시작

```bash
# Docker 이미지 빌드 및 서비스 시작
make build

# 또는 docker-compose 직접 사용
docker-compose up -d --build
```

브라우저에서 http://localhost:8501 접속

## 📖 사용 방법

### 1단계: 데이터 업로드

1. **예약 정보 CSV 업로드**
   - "📥 예시 파일 다운로드" 버튼으로 템플릿 다운로드
   - 또는 직접 작성 (아래 형식 참고)

2. **참여자 정보 CSV 업로드**
   - 예시 파일 다운로드 또는 직접 작성

### 2단계: 데이터 확인 및 편집

- **날짜/시간 편집**: 시간 컬럼 클릭 → 캘린더 및 시간 선택기 사용
- **셀 수정**: 원하는 셀 클릭 후 직접 입력
- **행 추가**: 표 하단의 ➕ 버튼 클릭
- **행 삭제**: 행 선택 후 🗑️ 버튼 클릭
- **공포포지션**: 드롭다운에서 탱커/평민/쫄 선택

### 3단계: 일정 생성

1. **"🚀 일정 생성하기"** 버튼 클릭
2. 이동 시간 자동 계산 (Naver Maps API)
3. Claude AI가 3가지 최적 시나리오 생성
4. 각 시나리오의 장단점 분석 확인

### 4단계: 시나리오 선택 및 내보내기

**시나리오 비교:**
- 탭을 클릭해서 3가지 시나리오 비교
- 각 시나리오의 장점/단점 확인
- 생성된 일정은 세션 유지 중 계속 표시됨
- 새로 만들려면 **"🗑️ 일정 초기화"** 버튼 클릭

**Google Sheets로 내보내기:**
1. 본인의 Google Sheets 생성/열기
2. 스프레드시트 URL 복사 (예: `https://docs.google.com/spreadsheets/d/1ABC...`)
3. **"공유"** 버튼 클릭 → UI에 표시된 Service Account 이메일 추가 (편집자 권한)
4. 앱에서 스프레드시트 URL 입력
5. **"📊 시트에 탭 추가"** 버튼 클릭
6. 새 탭이 추가되고 일정이 자동으로 채워짐

**CSV 다운로드:**
- **"📥 CSV 다운로드"** 버튼으로 로컬에 저장

## 📁 CSV 파일 형식

### 예약 정보 (reservations.csv)

```csv
방이름,시작시간,종료시간,주소,테마,최소인원,적정인원,최대인원
미스터리 하우스,2026-02-15 14:00,2026-02-15 16:00,서울 강남구 테헤란로 123,추리,2,4,5
공포의 지하실,2026-02-15 16:30,2026-02-15 18:30,서울 마포구 홍익로 456,공포,2,3,4
```

**필드 설명:**
- **방이름**: 방탈출 방 이름
- **시작시간**: `YYYY-MM-DD HH:MM` 형식
- **종료시간**: `YYYY-MM-DD HH:MM` 형식
- **주소**: 정확한 주소 (이동 시간 계산에 사용)
- **테마**: 추리, 공포, 액션 등
- **최소인원**: 입장 가능한 최소 인원
- **적정인원**: 권장 인원
- **최대인원**: 입장 가능한 최대 인원

### 참여자 정보 (users.csv)

```csv
이름,참여시작시간,참여종료시간,공포포지션
홍길동,2026-02-15 13:00,2026-02-15 22:00,탱커
김철수,2026-02-15 14:00,2026-02-15 20:00,평민
이영희,2026-02-15 13:00,2026-02-15 22:00,쫄
```

**필드 설명:**
- **이름**: 참여자 이름
- **참여시작시간**: `YYYY-MM-DD HH:MM` 형식
- **참여종료시간**: `YYYY-MM-DD HH:MM` 형식
- **공포포지션**:
  - **탱커**: 공포 방에서 리드하는 역할 (공포 방 우선 배정)
  - **평민**: 보통 수준
  - **쫄**: 공포에 약한 사람 (공포 방 우회 시도)

## 🛠️ Docker 명령어

```bash
make build      # Docker 이미지 빌드 및 서비스 시작
make up         # 서비스 시작 (빌드 제외)
make down       # 서비스 중지
make restart    # 서비스 재시작
make logs       # 실시간 로그 확인
make clean      # 완전 삭제 (컨테이너, 이미지, 볼륨)
```

**docker-compose 직접 사용:**
```bash
docker-compose up -d --build    # 빌드 후 백그라운드 실행
docker-compose down             # 중지
docker-compose logs -f app      # 로그 확인
docker-compose restart          # 재시작
```

## 📦 프로젝트 구조

```
escape-room-calendar-maker/
├── main.py                      # Streamlit 앱 진입점
├── config.py                    # 환경 설정 및 검증
├── requirements.txt             # Python 패키지 의존성
├── Dockerfile                   # Docker 이미지 정의
├── docker-compose.yml           # Docker Compose 설정
├── Makefile                     # 빌드/실행 명령어 단축키
├── credentials.json             # Google Sheets 인증 (gitignore)
├── README.md                    # 이 문서
├── .gitignore                   # Git 제외 파일 목록
├── data/
│   ├── example_reservations.csv # 예약 정보 예시
│   └── example_users.csv        # 참여자 정보 예시
└── src/
    ├── models.py                # Pydantic 데이터 모델
    ├── parser.py                # CSV 파싱 및 검증
    ├── travel.py                # Naver Maps API (이동 시간)
    ├── claude_agent.py          # Claude AI 스케줄링
    └── sheets.py                # Google Sheets 내보내기
```

## 🐛 문제 해결

### 1. API 키 인식 안 됨

**증상:** "❌ API 키가 설정되지 않았습니다" 에러

**해결:**
```bash
# 환경 변수 확인
echo $ANTHROPIC_API_KEY
echo $NAVER_MAPS_CLIENT_ID

# 비어있으면 Shell 설정 파일 재로드
source ~/.zshrc  # 또는 ~/.bashrc

# Docker 재시작 (환경 변수 다시 로드)
make restart
```

### 2. Google Sheets 권한 오류

**증상:** "❌ 스프레드시트 접근 권한이 없습니다"

**해결:**
1. Google Sheets 열기 → **"공유"** 클릭
2. UI에 표시된 Service Account 이메일 추가
   - 이메일 예시: `xxx@xxx.iam.gserviceaccount.com`
3. 권한: **"편집자"** 선택
4. **"완료"** 후 다시 시도

**또는:**
- "링크가 있는 모든 사용자" → "편집자" 권한으로 설정

### 3. Naver Maps API 401 Unauthorized

**증상:** "Geocoding error: 401 Client Error: Unauthorized"

**원인:** Naver Maps API 키가 잘못되었거나 API가 활성화되지 않음

**해결:**
1. [Naver Cloud Platform](https://www.ncloud.com/)에서 Application 확인
2. **Maps** → **Geocoding**, **Directions 5** 활성화 확인
3. Client ID/Secret 재확인
4. 환경 변수 재설정 후 Docker 재시작

### 4. Claude API 오류

**증상:** "❌ 시나리오 생성 실패"

**원인:**
- API 키가 잘못됨
- API 크레딧 소진
- 네트워크 문제

**해결:**
1. [Anthropic Console](https://console.anthropic.com/)에서 API 키 확인
2. 크레딧/사용량 확인
3. 새 API 키 생성 후 환경 변수 업데이트

### 5. Docker 컨테이너가 unhealthy 상태

**증상:** `docker-compose ps`에서 Status가 "unhealthy"

**확인:**
```bash
# 로그 확인
make logs

# 또는
docker-compose logs -f app
```

**일반적인 원인:**
- 포트 8501이 이미 사용 중
- 환경 변수 누락
- Python 패키지 설치 실패

**해결:**
```bash
# 완전 재빌드
make clean
make build
```

### 6. 생성된 일정이 사라짐

**증상:** 다른 작업을 하면 일정이 사라짐

**해결:**
- 브라우저 탭을 닫지 않는 한 일정은 유지됩니다
- 새로 만들려면 **"🗑️ 일정 초기화"** 버튼 클릭
- 브라우저를 새로고침하면 세션이 초기화되어 일정이 사라집니다

## 🤖 AI 스케줄링 알고리즘

Claude AI는 다음 요소를 고려하여 최적의 일정을 생성합니다:

- ✅ **팀 균등 분배**: 각 팀의 인원을 비슷하게 유지
- ✅ **공포 포지션 고려**: 탱커를 공포 방에 우선 배치, 쫄 보호
- ✅ **이동 시간 최소화**: 인접한 장소를 연속으로 배치
- ✅ **방 인원 제한**: 최소/최대 인원 준수
- ✅ **식사 시간 배치**: 점심(11-14시), 저녁(17-20시) 자동 고려
- ✅ **시간 효율성**: 대기 시간 및 공백 최소화
- ✅ **참여자 가용 시간**: 각 참여자의 참여 가능 시간 준수

## 🤝 기여

Issue와 Pull Request는 언제나 환영합니다!

## 📄 라이선스

MIT License

---

**만든 사람**: [@artit.anthony](https://github.com/artit-anthony)
**문의**: 이슈를 통해 질문해주세요
