"""
StockInsight Omni - AI 에이전트 모듈
Hugging Face (무료) + GPT/Gemini (프리미엄) 통합 AI 챗봇 & 분석
"""
import streamlit as st
from config import STOCK_SYSTEM_PROMPT, FINANCIAL_ANALYSIS_PROMPT, AI_MODELS


class HuggingFaceAgent:
    """무료 AI 챗봇 (Hugging Face Inference API)"""

    def __init__(self):
        self.model_id = AI_MODELS["huggingface"]["model_id"]
        self.client = None
        self._init_client()

    def _init_client(self):
        """HF InferenceClient 초기화"""
        try:
            from huggingface_hub import InferenceClient
            # 세션 상태 또는 secrets로부터 토큰 확보 및 엄격한 안전 가공(문자열화 및 양쪽 공백 소거)
            raw_token = st.session_state.get("hf_token", "") or st.secrets.get("HF_TOKEN", "")
            token = str(raw_token).strip() if raw_token else ""
            
            # 토큰의 실질적인 존재 유무 판독
            if token and token.lower() != "none":
                self.client = InferenceClient(api_key=token)
            else:
                # 비인증 호출 시 충돌을 막기 위해 명시적으로 None 할당
                self.client = None
        except Exception:
            self.client = None

    def chat(self, messages: list, stream: bool = True):
        """채팅 응답 생성"""
        if not self.client:
            yield (
                "### ⚠️ 무료 AI 가동을 위한 10초 연동 안내 🤖\n\n"
                "최신 AI 연동 엔진 정책 강화로 인해, **100% 무상 발급** 가능한 전용 키(Access Token) 입력이 필수가 되었습니다.\n\n"
                "간단히 아래 순서로 발급받아 적용해 주세요:\n\n"
                "1. **[huggingface.co/join](https://huggingface.co/join)** 에 접속하여 무료 이메일 회원 가입을 합니다.\n"
                "2. 로그인 후 **[설정 ➡️ Access Tokens](https://huggingface.co/settings/tokens)** 페이지로 들어갑니다.\n"
                "3. **Create new token** 버튼을 클릭한 뒤, `Read` 권한을 부여하여 무상 키를 생성합니다.\n"
                "4. 생성된 키(`hf_...`)를 복사하여 **사이드바의 Access Token** 란에 적거나 `.streamlit/secrets.toml`에 저장하시면 **평생 무료로 최고급 한국어 AI(Qwen-7B)가 가동됩니다!**"
            )
            return

        full_messages = [{"role": "system", "content": STOCK_SYSTEM_PROMPT}] + messages
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=full_messages,
                max_tokens=768,
                temperature=0.6,
                stream=stream,
            )
            if stream:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            # 런타임 도중 발견된 토큰 누락(api_key 부재) 에러 차단 및 전용 안내문 사출
            if any(keyword in error_msg.lower() for keyword in ["api_key", "auth", "token"]):
                yield (
                    "### 🌐 배포 환경 전용 API 연동 가이드 ⚠️\n\n"
                    "웹 서버(예: Streamlit Cloud 등) 배포 환경에 **무상 Hugging Face 키가 주입되지 않아** 실행이 잠시 멈춘 상태입니다.\n\n"
                    "**배포판 사이트에서 즉시 작동하게 만드는 2가지 해법:**\n\n"
                    "**✅ 방법 A. 즉석 처방 (사용자용)**\n"
                    "- 왼쪽 사이드바 아코디언 메뉴를 열어 **[HF Access Token]** 란에 발급받으신 무료 키(`hf_...`)를 직접 써넣고 작동시키세요!\n\n"
                    "**✅ 방법 B. 영구 귀속 (개발자용)**\n"
                    "- 배포하신 **Streamlit Cloud 관리자 대시보드**로 접속합니다.\n"
                    "- 배포된 앱 옆의 **Settings(설정) ➡️ Secrets** 항목으로 이동합니다.\n"
                    "- 아래 스키마를 그대로 복사하여 입력창에 저장(Save)하시면 즉각 영구 고정됩니다!\n"
                    "```toml\n"
                    "HF_TOKEN = \"본인의_무료_허깅페이스_토큰\"\n"
                    "```"
                )
            elif "rate" in error_msg.lower() or "429" in error_msg:
                yield "⏳ 요청이 너무 많습니다. 잠시 후 다시 시도해주세요. (무료 API 제한)"
            else:
                yield f"⚠️ AI 응답 생성 실패: {error_msg}"

    def is_available(self) -> bool:
        return self.client is not None


class PremiumAIAgent:
    """프리미엄 AI 에이전트 (GPT / Gemini)"""

    def __init__(self, provider: str, api_key: str, model: str = None):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.client = None
        self._init_client()

    def _init_client(self):
        """API 클라이언트 초기화"""
        # 이전 오류 정보 청소
        if "ai_init_error" in st.session_state:
            st.session_state["ai_init_error"] = None
            
        try:
            if self.provider == "gpt":
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                if not self.model:
                    self.model = "gpt-4o-mini"
            elif self.provider == "gemini":
                from google import genai
                if not self.model:
                    self.model = "gemini-2.5-flash"
                # 신규 google-genai SDK 클라이언트 객체 생성
                self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            self.client = None
            # 유저 디버깅을 위해 상세 예외 메시지를 세션 상태로 전송
            st.session_state["ai_init_error"] = f"[{self.provider.upper()} 라이브러리 로드 실패] {str(e)}"

    def chat(self, messages: list, stream: bool = True):
        """채팅 응답 생성"""
        if not self.client:
            yield "⚠️ API 연결에 실패했습니다. API 키를 확인해주세요."
            return

        try:
            if self.provider == "gpt":
                yield from self._chat_gpt(messages, stream)
            elif self.provider == "gemini":
                yield from self._chat_gemini(messages, stream)
        except Exception as e:
            yield from self._handle_api_error(e)

    def _handle_api_error(self, e: Exception):
        """API 에러를 사용자 친화적 메시지로 변환"""
        error_msg = str(e).lower()
        if any(k in error_msg for k in ["invalid_api_key", "invalid api key", "incorrect api key",
                                         "authentication", "401", "api_key_invalid"]):
            yield ("🔑 **API 키가 올바르지 않거나 활성화되지 않았습니다.**\n\n"
                   "사이드바 → ⚙️ AI API 설정에서 키를 다시 확인해 주세요.")
        elif any(k in error_msg for k in ["quota", "429", "rate limit", "exceeded"]):
            yield "⏳ API 사용량 한도에 도달했습니다. 잠시 후 다시 시도하거나, 플랜을 확인해 주세요."
        elif any(k in error_msg for k in ["model", "not found", "404", "is not supported"]):
            yield (f"🤖 선택하신 모델 `{self.model}` 을(를) 찾을 수 없습니다.\n\n"
                   "사이드바에서 다른 모델을 선택하거나, '직접 입력(Custom)'으로 정확한 모델명을 입력해 주세요.")
        elif "permission" in error_msg or "403" in error_msg:
            yield "🚫 해당 모델에 접근 권한이 없습니다. API 플랜과 권한 설정을 확인해 주세요."
        else:
            yield f"⚠️ AI 응답 생성 실패: {str(e)}"

    def _chat_gpt(self, messages, stream):
        """GPT 채팅"""
        full_messages = [{"role": "system", "content": STOCK_SYSTEM_PROMPT}] + messages
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=2048,
                stream=stream,
            )
            if stream:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield response.choices[0].message.content
        except Exception as e:
            yield from self._handle_api_error(e)

    def _chat_gemini(self, messages, stream):
        """Gemini 채팅 (Modern google-genai SDK 구현)"""
        from google.genai import types

        history = []
        # types.Content 객체 형태로 히스토리 매핑
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            ))

        try:
            # system_instruction은 chats.create의 config로 전달하면 매 요청마다 프롬프트 앞에 붙이는 비용이 사라져 스트리밍 시작이 더 빠릅니다.
            chat = self.client.chats.create(
                model=self.model,
                history=history,
                config=types.GenerateContentConfig(
                    system_instruction=STOCK_SYSTEM_PROMPT,
                    max_output_tokens=1536,
                ),
            )
            last_msg = messages[-1]["content"] if messages else ""

            if stream:
                response = chat.send_message_stream(last_msg)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            else:
                response = chat.send_message(last_msg)
                yield response.text
        except Exception as e:
            yield from self._handle_api_error(e)

    def analyze_financials(self, financial_data: str, stream: bool = True):
        """재무제표 심층 분석"""
        try:
            prompt = FINANCIAL_ANALYSIS_PROMPT.format(financial_data=financial_data)
        except KeyError:
            prompt = f"다음 재무 데이터를 분석해 주세요:\n{financial_data}"
        messages = [{"role": "user", "content": prompt}]
        yield from self.chat(messages, stream)

    def is_available(self) -> bool:
        return self.client is not None


def get_ai_agent(premium_provider=None, api_key=None, model=None):
    """적절한 AI 에이전트 반환"""
    if premium_provider and api_key:
        agent = PremiumAIAgent(premium_provider, api_key, model)
        if agent.is_available():
            return agent, "premium"
    # 폴백: 무료 HF 에이전트
    agent = HuggingFaceAgent()
    return agent, "free"


def format_financial_data_for_prompt(info: dict, financials: dict) -> str:
    """재무 데이터를 AI 프롬프트용 텍스트로 변환"""
    lines = []
    lines.append(f"## {info.get('name', 'N/A')} 재무 분석 데이터")
    lines.append(f"- 섹터: {info.get('sector', 'N/A')}")
    lines.append(f"- 산업: {info.get('industry', 'N/A')}")

    if info.get("market_cap"):
        mc = info["market_cap"]
        if mc >= 1e12:
            lines.append(f"- 시가총액: ${mc/1e12:.2f}T")
        else:
            lines.append(f"- 시가총액: ${mc/1e9:.2f}B")

    if info.get("per"):
        lines.append(f"- PER: {info['per']:.2f}")
    if info.get("pbr"):
        lines.append(f"- PBR: {info['pbr']:.2f}")
    if info.get("dividend_yield"):
        # yfinance dividend_yield는 이미 퍼센트 단위(예: 2.5%)이므로 곱하지 않음
        lines.append(f"- 배당수익률: {info['dividend_yield']:.2f}%")

    # 재무제표 요약
    if "income_statement" in financials:
        inc = financials["income_statement"]
        lines.append("\n### 손익계산서 (최근)")
        for col in inc.columns[:3]:
            lines.append(f"\n**{col.strftime('%Y') if hasattr(col, 'strftime') else col}:**")
            for row_name in ["Total Revenue", "Operating Income", "Net Income"]:
                if row_name in inc.index:
                    val = inc.loc[row_name, col]
                    if val and not (isinstance(val, float) and val != val):
                        lines.append(f"  - {row_name}: {val:,.0f}")

    return "\n".join(lines)
