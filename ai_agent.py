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
            token = st.secrets.get("HF_TOKEN", "")
            if token:
                self.client = InferenceClient(api_key=token)
            else:
                self.client = InferenceClient()
        except Exception:
            self.client = None

    def chat(self, messages: list, stream: bool = True):
        """채팅 응답 생성"""
        if not self.client:
            yield "⚠️ Hugging Face 연결에 실패했습니다. HF_TOKEN을 확인해주세요."
            return

        full_messages = [{"role": "system", "content": STOCK_SYSTEM_PROMPT}] + messages
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=full_messages,
                max_tokens=1024,
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
            if "rate" in error_msg.lower() or "429" in error_msg:
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
        try:
            if self.provider == "gpt":
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                if not self.model:
                    self.model = "gpt-4o-mini"
            elif self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                if not self.model:
                    self.model = "gemini-3.0-flash"
                self.client = genai.GenerativeModel(self.model)
        except Exception:
            self.client = None

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
            yield f"⚠️ AI 응답 생성 실패: {str(e)}"

    def _chat_gpt(self, messages, stream):
        """GPT 채팅"""
        full_messages = [{"role": "system", "content": STOCK_SYSTEM_PROMPT}] + messages
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

    def _chat_gemini(self, messages, stream):
        """Gemini 채팅"""
        # Gemini 포맷으로 변환
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        chat = self.client.start_chat(history=history)
        last_msg = messages[-1]["content"] if messages else ""
        prompt = f"{STOCK_SYSTEM_PROMPT}\n\n{last_msg}"

        if stream:
            response = chat.send_message(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        else:
            response = chat.send_message(prompt)
            yield response.text

    def analyze_financials(self, financial_data: str, stream: bool = True):
        """재무제표 심층 분석"""
        prompt = FINANCIAL_ANALYSIS_PROMPT.format(financial_data=financial_data)
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
        lines.append(f"- 배당수익률: {info['dividend_yield']*100:.2f}%")

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
