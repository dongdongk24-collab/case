"""
광진구 복지서비스 매칭 시스템
사회복지사 전용 케이스매니지먼트 도우미
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from tools.pdf_reader import extract_text_from_pdfs, load_default_pdfs
from tools.gemini_client import call_welfare_matching

# 기본 PDF 자동 로드 (data/ 폴더)
@st.cache_resource
def get_default_pdf_text():
    return load_default_pdfs()

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="광진구 복지서비스 매칭 시스템",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    * { font-family: 'Malgun Gothic', 'Apple Gothic', 'NanumGothic', sans-serif !important; }
    .main-title { font-size: 1.8rem; font-weight: 700; color: #1a4a8a; margin-bottom: 0.2rem; }
    .sub-title  { font-size: 1rem; color: #666; margin-bottom: 1.5rem; }
    .section-label {
        font-size: 1rem; font-weight: 700; color: #1a4a8a;
        margin-top: 1rem; margin-bottom: 0.3rem;
        display: flex; align-items: center; gap: 6px;
    }
    section[data-testid="stSidebar"] { width: 340px !important; }
    /* 사이드바 접기 버튼 아이콘 텍스트 숨기기 */
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="collapsedControl"] span,
    button[aria-label="Close sidebar"] span,
    button[aria-label="Open sidebar"] span,
    button[aria-label="Close sidebar"],
    button[aria-label="Open sidebar"] {
        font-size: 0 !important;
        color: transparent !important;
    }
    .material-symbols-rounded {
        font-size: 0 !important;
        color: transparent !important;
        width: 24px; height: 24px;
    }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ─────────────────────────────────────────────────────
st.markdown('<div class="main-title">광진구 복지서비스 매칭 시스템</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">사회복지사 전용 · AI 기반 맞춤형 서비스 매칭 도우미</div>', unsafe_allow_html=True)
st.divider()

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:

    # ── 기본 정보 ──
    st.markdown('<div class="section-label">👤 기본 정보</div>', unsafe_allow_html=True)
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        age = st.text_input("나이", placeholder="예: 75")
    with col2:
        gender = st.selectbox("성별", ["선택", "남성", "여성"])

    st.markdown("**가구 유형**")
    family_selected = st.pills(
        "가구유형선택",
        ["독거", "부부가구", "한부모", "조손가구", "다자녀", "다문화"],
        selection_mode="multi",
        label_visibility="collapsed",
    )
    family_other = st.text_input(
        "기타 가구유형 직접 입력",
        placeholder="예: 노인부부, 북한이탈주민 등",
    )

    # ── 경제 상황 ──
    st.markdown('<div class="section-label">💰 경제 상황</div>', unsafe_allow_html=True)
    st.divider()

    income = st.selectbox(
        "소득 수준",
        ["선택 안 함", "기초생활수급자", "차상위계층 (중위소득 50% 이하)",
         "중위소득 60% 이하", "중위소득 80% 이하", "일반"],
        label_visibility="collapsed",
    )

    # ── 욕구 / 어려움 ──
    st.markdown('<div class="section-label">🧩 욕구 / 어려움</div>', unsafe_allow_html=True)
    st.divider()

    needs_selected = st.pills(
        "욕구선택",
        ["의료비", "주거", "식품/영양", "돌봄", "치매", "정신건강",
         "고독/고립", "일상생활", "취업훈련", "법률/행정", "교육비",
         "가정폭력", "경제적어려움", "부채/채무", "실직/무직", "자산형성"],
        selection_mode="multi",
        label_visibility="collapsed",
    )
    needs_other = st.text_input(
        "기타 욕구 직접 입력",
        placeholder="예: 고독사 위험, 이동 불편 등",
    )

    # ── 장애 및 건강 ──
    st.markdown('<div class="section-label">♿ 장애 및 건강</div>', unsafe_allow_html=True)
    st.divider()

    disability = st.selectbox(
        "등록 장애",
        ["없음/모름", "지체장애", "뇌병변장애", "시각장애",
         "청각장애", "지적장애", "정신장애", "기타장애"],
    )
    health = st.text_input(
        "건강 상태 / 질환",
        placeholder="예: 고혈압, 당뇨, 치매 초기 등",
    )

    # ── 추가 메모 ──
    st.markdown('<div class="section-label">📝 추가 메모</div>', unsafe_allow_html=True)
    st.divider()

    notes = st.text_area(
        "추가메모입력",
        placeholder="주거 형태, 가족 관계, 위기 상황, 특이사항 등",
        height=100,
        label_visibility="collapsed",
    )

    # ── PDF 첨부 ──
    st.markdown('<div class="section-label">📎 복지 자료 첨부 (선택)</div>', unsafe_allow_html=True)
    st.divider()
    st.caption("각종 지침 45개의 자료가 기본 포함됨")

    uploaded_files = st.file_uploader(
        "PDF 업로드",
        type=["pdf"],
        accept_multiple_files=True,
        help="광진구 복지 안내서, 사업안내 PDF 등",
        label_visibility="collapsed",
    )
    if uploaded_files:
        st.success(f"{len(uploaded_files)}개 파일 업로드 완료")

    st.divider()
    run_button = st.button(
        "복지서비스 매칭 시작",
        type="primary",
        use_container_width=True,
    )

# ── 메인 영역 ─────────────────────────────────────────────────
if not run_button:
    st.markdown("""
**사용 방법**

1. 왼쪽 사이드바에 민원인 기본 정보를 입력하세요
2. 광진구, 보건복지부, 기관 등의 복지 관련 PDF가 있으면 첨부해도 됩니다
3. **복지서비스 매칭 시작** 버튼을 누르면 AI가 분석합니다

**AI가 하는 일**
- 광진구·서울시·전국 복지 서비스 실시간 검색
- 민원인 상황에 맞는 서비스 매칭
- 신청 방법·조건까지 포함한 6단계 보고서 생성
""")

else:
    # 입력 데이터 조합
    family_parts = list(family_selected) if family_selected else []
    if family_other.strip():
        family_parts.append(family_other.strip())
    family_str = ", ".join(family_parts) if family_parts else "미입력"

    needs_parts = list(needs_selected) if needs_selected else []
    if needs_other.strip():
        needs_parts.append(needs_other.strip())
    needs_str = ", ".join(needs_parts) if needs_parts else "미입력"

    client_data = {
        "age":        age.strip() if age.strip() else "미입력",
        "gender":     gender if gender != "선택" else "미입력",
        "family":     family_str,
        "income":     income if income != "선택 안 함" else "미입력",
        "needs":      needs_str,
        "disability": disability,
        "health":     health.strip() if health.strip() else "미입력",
        "notes":      notes.strip() if notes.strip() else "없음",
    }

    with st.spinner("AI가 복지서비스를 분석 중입니다... (30초~1분 소요)"):
        try:
            default_text = get_default_pdf_text()
            upload_text = extract_text_from_pdfs(uploaded_files) if uploaded_files else ""
            pdf_text = "\n\n".join(filter(None, [default_text, upload_text]))
            result = call_welfare_matching(client_data, pdf_text)
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            st.stop()

    st.success("분석 완료!")
    st.divider()

    # 요약 정보 표시
    cols = st.columns(4)
    cols[0].metric("나이", f"{client_data['age']}세" if client_data['age'] != "미입력" else "-")
    cols[1].metric("성별", client_data['gender'])
    cols[2].metric("소득", income.split(" ")[0] if income != "선택 안 함" else "-")
    cols[3].metric("장애", disability)

    st.divider()
    st.markdown(result)
