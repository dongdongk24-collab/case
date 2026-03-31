"""
Tool: PDF 텍스트 추출기
역할: 업로드된 PDF 파일에서 텍스트를 추출하여 하나의 문자열로 반환
"""

import io
import os
import pdfplumber


MAX_CHARS = 60000  # 토큰 한도 초과 방지용 최대 글자 수
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def extract_text_from_pdfs(uploaded_files: list) -> str:
    """
    Streamlit UploadedFile 목록을 받아 전체 텍스트를 추출해 반환.
    파일이 없으면 빈 문자열 반환.
    """
    if not uploaded_files:
        return ""

    all_text_parts = []

    for file in uploaded_files:
        file_name = getattr(file, "name", "알 수 없는 파일")
        try:
            file_bytes = file.read()
            extracted = _extract_from_bytes(file_bytes, file_name)
            all_text_parts.append(f"=== 문서: {file_name} ===\n{extracted}\n")
        except Exception as e:
            all_text_parts.append(
                f"=== 문서: {file_name} ===\n[오류: 이 파일을 읽을 수 없습니다. ({e})]\n"
            )

    combined = "\n".join(all_text_parts)

    # 너무 길면 앞부분만 사용
    if len(combined) > MAX_CHARS:
        combined = combined[:MAX_CHARS]
        combined += "\n\n[참고: 문서가 너무 길어 일부만 포함되었습니다. AI가 웹 검색으로 보완합니다.]"

    return combined


def load_default_pdfs() -> str:
    """
    data/ 폴더에 있는 PDF를 자동으로 읽어서 반환.
    앱 시작 시 항상 기본 참고 자료로 포함됨.
    """
    if not os.path.exists(DATA_DIR):
        return ""

    pdf_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        return ""

    all_parts = []
    for file_name in sorted(pdf_files):
        file_path = os.path.join(DATA_DIR, file_name)
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            extracted = _extract_from_bytes(file_bytes, file_name)
            all_parts.append(f"=== 기본 자료: {file_name} ===\n{extracted}\n")
        except Exception as e:
            all_parts.append(f"=== 기본 자료: {file_name} ===\n[읽기 실패: {e}]\n")

    combined = "\n".join(all_parts)
    if len(combined) > MAX_CHARS:
        combined = combined[:MAX_CHARS] + "\n[자료가 너무 길어 일부만 포함됨]"
    return combined


def _extract_from_bytes(file_bytes: bytes, file_name: str) -> str:
    """PDF 바이트에서 텍스트 추출. 이미지 PDF이면 안내 문구 반환."""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        pages_text = []
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                pages_text.append(f"[{file_name} - {i}페이지]\n{text}")

    if not pages_text:
        return "[이 PDF는 이미지로만 구성되어 텍스트를 추출할 수 없습니다. AI가 웹 검색으로 관련 정보를 찾겠습니다.]"

    return "\n\n".join(pages_text)
