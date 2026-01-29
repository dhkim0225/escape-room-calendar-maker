# 🔐 Escape Room Calendar Maker

방탈출 모임을 위한 AI 기반 자동 일정 생성 도구

## 📋 기능

- 📊 CSV 파일로 예약 정보와 참여자 정보 입력
- 🤖 Claude AI 기반 최적 일정 자동 생성
- 🗺️ Naver Maps API를 통한 이동 시간 계산
- 👥 팀 균등 분배 및 공포 포지션 고려
- 🍽️ 식사 시간 자동 배치
- 📈 Google Sheets로 일정표 자동 출력

## 🚀 빠른 시작

### 1. 환경 설정

`.env` 파일을 생성하고 API 키를 설정하세요:

```bash
cp .env.example .env
```

`.env` 파일 수정:
```bash
# Claude API
CLAUDE_API_KEY=sk-ant-your-api-key-here

# Naver Maps API
NAVER_MAPS_CLIENT_ID=your-client-id-here
NAVER_MAPS_CLIENT_SECRET=your-client-secret-here

# Google Sheets API
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials.json
```

### 2. Google Sheets 인증 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. Google Sheets API 활성화
3. 서비스 계정 생성 후 JSON 키 다운로드
4. 다운로드한 파일을 `credentials.json`으로 저장

### 3. 서비스 시작

```bash
make build
```

브라우저에서 http://localhost:8501 접속

## 📁 CSV 파일 형식

### 예약 정보 (reservations.csv)

| 방이름 | 시작시간 | 종료시간 | 주소 | 테마 | 최소인원 | 적정인원 | 최대인원 |
|--------|----------|----------|------|------|----------|----------|----------|
| 미스터리 하우스 | 2026-02-15 14:00 | 2026-02-15 16:00 | 서울 강남구 테헤란로 123 | 추리 | 2 | 4 | 5 |

### 참여자 정보 (users.csv)

| 이름 | 참여시작시간 | 참여종료시간 | 공포포지션 |
|------|--------------|--------------|------------|
| 홍길동 | 2026-02-15 13:00 | 2026-02-15 22:00 | 탱커 |

**공포포지션**: `탱커`, `평민`, `쫄` 중 하나

## 🛠️ 명령어

```bash
make build    # Docker 이미지 빌드 및 서비스 시작
make up       # 서비스 시작
make down     # 서비스 중지
make restart  # 서비스 재시작
make logs     # 로그 확인
make clean    # 완전 삭제 (컨테이너, 이미지, 볼륨)
```

## 📦 프로젝트 구조

```
escape-room-calendar-maker/
├── main.py                  # Streamlit 앱 진입점
├── config.py                # 설정 및 환경 변수
├── requirements.txt         # Python 의존성
├── Dockerfile               # Docker 이미지 정의
├── docker-compose.yml       # Docker Compose 설정
├── Makefile                 # 빌드/실행 명령어
├── .env                     # API 키 (gitignore)
├── credentials.json         # Google Sheets 인증 (gitignore)
├── data/
│   ├── example_reservations.csv  # 예시 예약 데이터
│   └── example_users.csv         # 예시 참여자 데이터
└── src/
    ├── models.py            # 데이터 모델
    ├── parser.py            # CSV 파서
    ├── travel.py            # 이동 시간 계산 (TODO)
    ├── scheduler.py         # 스케줄링 로직 (TODO)
    ├── claude_agent.py      # Claude API 호출 (TODO)
    └── sheets.py            # Google Sheets 출력 (TODO)
```

## 🤝 기여

Issue와 PR은 언제나 환영입니다!

## 📄 라이선스

MIT License
