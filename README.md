# 📊 StockInsight Omni

> **AI 기반 크로스플랫폼 주식 분석 허브**
> PC 웹브라우저 & 아이폰(iOS) 모두에서 최적화된 경험을 제공합니다.

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 📊 **대시보드** | KOSPI, S&P500 등 실시간 시장 지수 + 관심 종목 현황 |
| 📈 **기술적 분석** | 인터랙티브 캔들스틱 차트, 이동평균선, RSI, MACD, 볼린저 밴드 |
| 🤖 **AI 애널리스트** | 무료 AI 챗봇 (Hugging Face) + 프리미엄 재무 분석 (GPT/Gemini) |
| 🔮 **AI 예측** | Prophet 모델 기반 주가 예측, 투자 매력도 점수 |
| 💼 **백테스터** | 포트폴리오 수익률, MDD, 샤프지수, 벤치마크 비교 |

---

## 🚀 로컬 실행 방법

### 1단계: Python 설치
- [Python 3.10+](https://www.python.org/downloads/) 설치 (3.11 권장)

### 2단계: 프로젝트 다운로드 및 의존성 설치
```bash
# 프로젝트 폴더로 이동
cd Stock_Analizer

# 가상 환경 생성 (권장)
python -m venv venv

# 가상 환경 활성화
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 3단계: Hugging Face 토큰 설정 (무료 AI 챗봇용)
1. [Hugging Face](https://huggingface.co/) 회원가입
2. Settings > Access Tokens > New Token (Read) 생성
3. `.streamlit/secrets.toml` 파일 생성:
```toml
HF_TOKEN = "hf_your_token_here"
```

### 4단계: 앱 실행
```bash
streamlit run app.py
```
→ 브라우저에서 `http://localhost:8501` 자동 열림

---

## 🌐 Streamlit Cloud 무료 배포 (나만의 웹 주소 만들기)

### 1단계: GitHub에 코드 올리기
```bash
# Git 초기화
git init
git add .
git commit -m "Initial commit: StockInsight Omni"

# GitHub에서 새 저장소 생성 후
git remote add origin https://github.com/YOUR_USERNAME/stock-insight-omni.git
git branch -M main
git push -u origin main
```

### 2단계: Streamlit Cloud 배포
1. [share.streamlit.io](https://share.streamlit.io/) 접속
2. **GitHub 계정으로 로그인**
3. **"New app"** 클릭
4. 설정:
   - **Repository**: `YOUR_USERNAME/stock-insight-omni`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. **Advanced settings** 에서 Secrets 입력:
   ```toml
   HF_TOKEN = "hf_your_token_here"
   ```
6. **"Deploy!"** 클릭

✅ 배포 완료! 나만의 URL 발급:
```
https://your-app-name.streamlit.app
```

---

## 📱 아이폰 홈 화면에 앱으로 등록하기

배포된 앱을 아이폰에서 네이티브 앱처럼 사용할 수 있습니다!

### 방법:
1. **Safari**에서 배포된 URL 접속 (예: `https://your-app.streamlit.app`)
2. 하단의 **공유 버튼** (□↑ 모양) 탭
3. 스크롤하여 **"홈 화면에 추가"** 선택
4. 앱 이름 확인 → **"추가"** 탭
5. 홈 화면에 📊 아이콘 생성!

> 💡 홈 화면에서 앱을 열면 주소창 없이 전체 화면으로 실행됩니다.

---

## 🔑 프리미엄 AI 기능 (선택사항)

GPT 또는 Gemini API 키가 있으면 더 강력한 AI 분석이 가능합니다:

- **심층 재무제표 분석**: 매출, 영업이익, 순이익 트렌드 분석
- **초보자용 3줄 요약**: 복잡한 분석을 쉽게 요약
- **더 정확한 AI 응답**: 대형 LLM 모델 사용

앱 사이드바 > 🔑 AI API 설정에서 키를 입력하세요.
(키는 세션에만 저장되며, 서버에 저장되지 않습니다.)

---

## 📁 프로젝트 구조

```
Stock_Analizer/
├── app.py              # 메인 앱 (엔트리 포인트)
├── config.py           # 전역 설정
├── styles.py           # CSS/PWA 주입 모듈
├── style.css           # 커스텀 CSS (반응형)
├── data_fetcher.py     # yfinance 데이터 수집
├── indicators.py       # 기술적 분석 지표
├── ai_agent.py         # AI 챗봇 & 분석
├── predictor.py        # Prophet 주가 예측
├── backtester.py       # 포트폴리오 백테스트
├── requirements.txt    # Python 의존성
├── packages.txt        # 시스템 의존성
├── .streamlit/
│   └── config.toml     # Streamlit 테마
└── .gitignore
```

---

## ⚠️ 면책 조항

본 서비스는 **정보 제공 목적**으로만 제공되며, 투자 권유나 조언이 아닙니다.
모든 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.
과거 실적이 미래 수익을 보장하지 않습니다.
