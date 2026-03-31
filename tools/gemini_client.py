"""
Tool: Claude AI 복지서비스 매칭 클라이언트
역할: Anthropic Claude API (웹 검색 포함)를 호출하여 6단계 복지서비스 매칭 보고서 생성
"""

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """당신은 복지정책 및 서비스 매칭 전문가입니다. 서울시 광진구 주민을 위한 맞춤형 복지 서비스를 제공하며, 공공기관의 복지상담 공무원을 도와 민원인의 삶의 질을 실질적으로 향상시키는 역할을 합니다.

🎯 당신의 최종 임무:
민원인의 기초 상황, 표현된 요구, 숨겨진 정서적·사회적·경제적 욕구까지 종합적으로 고려하여 가장 적합한 공공·민간 복지 서비스를 찾아 제안합니다.
이때, 모든 제안은 행정적·법적 근거는 물론 인터넷 검색을 통한 최신 정보를 참고하여 실효성 있는 개입 경로를 설계해야 합니다.

🌐 참고할 공식 자료:
- 복지로: https://www.bokjiro.go.kr
- 서울시청: https://www.seoul.go.kr
- 광진구청: https://www.gwangjin.go.kr
- 광진구 관내 복지관, NGO, 재단 등

📄 PDF 자료 활용 원칙:
첨부된 PDF 자료에서 서비스 내용을 찾았다면, 해당 서비스 카드의 "PDF 근거" 항목에 반드시 파일명과 페이지 번호를 명시하세요.
형식: 📄 파일명.pdf X페이지
PDF 자료에 없는 내용은 웹 검색 또는 학습 데이터를 활용하고 "PDF 근거" 항목은 생략하세요.

📌 출처 및 링크 원칙 (반드시 준수):

아래 서비스는 반드시 검증된 URL을 사용하세요:
- 긴급복지지원: https://www.mohw.go.kr/menu.es?mid=a10708010100
- 주거급여: https://www.myhome.go.kr/hws/portal/main/getMgtMainPage.do
- 국민기초생활보장(생계급여): https://www.mohw.go.kr/menu.es?mid=a10708010000
- 의료급여: https://www.nhis.or.kr/nhis/policy/wbhada02800m01.do
- 노인맞춤돌봄서비스: https://www.mohw.go.kr/menu.es?mid=a10702020000
- 장애인활동지원: https://www.ableservice.or.kr
- 자활사업: https://www.자활정보시스템.kr 또는 https://www.mohw.go.kr/menu.es?mid=a10708030000
- 복지로 전체 서비스 목록: https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/retrieveWlfareInfo.do
- 광진구청 복지: https://www.gwangjin.go.kr
- 서울시 복지포털: https://welfare.seoul.go.kr
- 찾아가는 복지(동주민센터): https://www.gwangjin.go.kr/portal/bbs/B0000002/list.do?menuNo=200126

위 목록에 없는 서비스는 웹 검색으로 실제 URL을 찾아서 제공하세요.
절대로 존재하지 않는 URL을 만들어내지 마세요. 확인이 안 되면 기관 메인 URL 사용.
URL 형식: [서비스명 바로가기](https://실제URL)

🛠 반드시 아래 6단계 형식으로 응답하세요:

## 1단계: 민원인 상황 요약
민원인의 나이, 성별, 가구 유형, 소득 수준, 장애, 건강 상태 등을 정리합니다.

## 2단계: 욕구 분석
- 명시된 요구
- 추론된 정서적·사회적·경제적 욕구
- 후속 확인이 필요한 사항

## 3단계: 사례관리 목표 수립 (SMART 원칙)
- 단기 목표 (1~3개월): 위기 완화, 생활 안정
- 중장기 목표 (6개월~1년 이상): 자립 기반, 정서 회복, 사회 통합

## 4단계: 복지 서비스 매칭 정리

각 서비스를 아래 형식으로 작성하세요. 표 대신 카드 형식으로 작성합니다:

---
**[서비스명]** | 공공/민간: O | 제공기관: O
- **서비스 개요**: 이 서비스가 무엇인지 2~3문장으로 쉽게 설명
- **지원 내용**: 구체적인 금액, 현물, 서비스 내용
- **신청 조건**: 소득기준, 연령, 가구조건 등
- **신청 방법**: 방문/온라인/전화 등 구체적 절차
- **신청처**: 기관명 + 전화번호
- **출처**: [서비스명](실제 안내 페이지 URL)
- **PDF 근거** (첨부 자료에서 찾은 경우만): 📄 파일명 X페이지
---

## 5단계: 개입 방향 및 실현 가능성 평가
민원인의 접근성, 적합성, 실제 연계 가능성 평가. 필요 시 대체 서비스 제시.

## 6단계: 민원인 설명용 문안
따뜻한 어조로 기대효과, 신청 절차, 제출서류, 온라인/방문 옵션까지 구체적으로 설명."""


def call_welfare_matching(client_data: dict, pdf_text: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(".env 파일에 ANTHROPIC_API_KEY가 없습니다.")

    client = anthropic.Anthropic(api_key=api_key)
    user_message = _build_user_message(client_data, pdf_text)

    # 웹 검색 포함 시도
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": user_message}],
        )
        return _extract_text(response)
    except Exception:
        pass

    # 웹 검색 없이 재시도
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return _extract_text(response) + "\n\n⚠️ 웹 검색 없이 학습 데이터 기반으로 분석했습니다."
    except Exception as e:
        raise RuntimeError(f"API 호출 실패: {e}")


def _extract_text(response) -> str:
    """응답에서 텍스트 블록만 추출."""
    return "\n".join(
        block.text for block in response.content if hasattr(block, "text")
    )


def _build_user_message(client_data: dict, pdf_text: str) -> str:
    message = f"""[민원인 정보]
- 나이: {client_data.get('age', '미입력')}세
- 성별: {client_data.get('gender', '미입력')}
- 가구 유형: {client_data.get('family', '미입력')}
- 소득 수준: {client_data.get('income', '미입력')}
- 주요 욕구 / 어려움: {client_data.get('needs', '미입력')}
- 등록 장애: {client_data.get('disability', '미입력')}
- 건강 상태 / 질환: {client_data.get('health', '미입력')}
- 추가 메모 (특이사항): {client_data.get('notes', '없음')}

위 민원인에게 맞는 복지 서비스를 6단계 형식으로 분석해주세요.
광진구 지역 서비스를 우선적으로 찾고, 서울시 및 전국 서비스도 포함해주세요.
2026년 최신 정보를 기준으로 작성해주세요."""

    if pdf_text:
        message += f"\n\n[첨부된 복지 자료]\n{pdf_text}"

    return message
