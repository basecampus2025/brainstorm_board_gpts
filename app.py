import streamlit as st
import google.generativeai as genai
from typing import List, Set
import os

# API 키 확인
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ Gemini API 키가 설정되지 않았습니다. `.streamlit/secrets.toml` 파일에 `GEMINI_API_KEY`를 설정해주세요.")
    st.stop()

# Gemini API 설정
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ Gemini API 설정 중 오류가 발생했습니다: {str(e)}")
    st.stop()

def reset_session_state():
    """세션 상태를 초기화합니다."""
    for key in ["topic", "ideas", "liked_ideas", "removed_ideas", "current_round"]:
        if key in st.session_state:
            del st.session_state[key]
    # 초기 상태 설정
    st.session_state.topic = ""
    st.session_state.ideas = []
    st.session_state.liked_ideas = set()
    st.session_state.removed_ideas = set()
    st.session_state.current_round = 1

def generate_ideas(topic: str, liked_ideas: Set[str], removed_ideas: Set[str], round_num: int) -> List[str]:
    """주어진 주제에 대해 5개의 창의적인 아이디어를 생성합니다."""
    if not topic.strip():
        st.warning("⚠️ 주제를 입력해주세요.")
        return []

    # 이전 라운드의 피드백을 프롬프트에 반영
    feedback_context = ""
    if round_num > 1:
        feedback_context = f"""
        이전 라운드에서 사용자가 좋아한 아이디어 유형:
        {', '.join(liked_ideas) if liked_ideas else '없음'}
        
        이전 라운드에서 사용자가 제거한 아이디어 유형:
        {', '.join(removed_ideas) if removed_ideas else '없음'}
        
        위의 피드백을 참고하여, 좋아한 아이디어와 유사한 새로운 접근 방식을 제시하고,
        제거된 아이디어와 유사한 접근 방식은 피해주세요.
        """
    
    prompt = f"""
    다음 주제에 대해 5개의 창의적이고 실용적인 아이디어를 생성해주세요:
    주제: {topic}
    
    {feedback_context}
    
    요구사항:
    - 각 아이디어는 1~2문장으로 간결하게 작성
    - 중복되는 아이디어는 제외
    - 각 아이디어는 번호와 함께 작성 (예: "1. 아이디어 내용")
    - 창의적이고 실현 가능한 아이디어를 제시
    - 이전에 제시된 아이디어와 유사한 접근 방식은 피해주세요
    """
    
    try:
        response = model.generate_content(prompt)
        if not response.text:
            st.error("⚠️ 아이디어 생성에 실패했습니다. 다시 시도해주세요.")
            return []
            
        # 응답 텍스트를 줄 단위로 분리하고 빈 줄 제거
        ideas = [line.strip() for line in response.text.split('\n') if line.strip()]
        # 번호가 포함된 줄만 필터링하고 번호 제거
        ideas = [idea.split('. ', 1)[1] if '. ' in idea else idea for idea in ideas if any(c.isdigit() for c in idea[:2])]
        
        if not ideas:
            st.error("⚠️ 생성된 아이디어를 파싱할 수 없습니다. 다시 시도해주세요.")
            return []
            
        return ideas[:5]  # 최대 5개 아이디어 반환
    except Exception as e:
        st.error(f"⚠️ 아이디어 생성 중 오류가 발생했습니다: {str(e)}")
        return []

# 페이지 기본 설정
st.set_page_config(
    page_title="브레인스토밍 아이디어 보드",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 세션 상태 초기화
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "ideas" not in st.session_state:
    st.session_state.ideas = []
if "liked_ideas" not in st.session_state:
    st.session_state.liked_ideas = set()
if "removed_ideas" not in st.session_state:
    st.session_state.removed_ideas = set()
if "current_round" not in st.session_state:
    st.session_state.current_round = 1

# 메인 컨테이너
main_container = st.container()

with main_container:
    # 헤더 섹션
    st.title("🧠 브레인스토밍 아이디어 보드")
    st.markdown("창의적인 아이디어가 필요할 때, 주제만 입력하세요! 💡")
    st.markdown("---")

    # 초기화 버튼 (항상 상단에 표시)
    if st.button("🆕 주제 초기화 및 새로 시작", type="secondary", use_container_width=True):
        reset_session_state()
        st.rerun()

    # 입력 섹션
    topic = ""
    generate_clicked = False
    
    if not st.session_state.topic:  # 초기 화면 또는 초기화 후
        st.markdown("### 📝 새로운 주제 입력")
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                topic = st.text_input(
                    "주제를 입력하세요",
                    placeholder="예: 새로운 스마트폰 앱 아이디어",
                    key="topic_input"
                )
            with col2:
                generate_clicked = st.button(
                    "아이디어 생성하기",
                    type="primary",
                    use_container_width=True
                )

    # 아이디어 생성 및 표시
    if generate_clicked and topic:
        with st.spinner("아이디어를 생성하는 중..."):
            st.session_state.topic = topic
            st.session_state.ideas = generate_ideas(
                topic,
                st.session_state.liked_ideas,
                st.session_state.removed_ideas,
                st.session_state.current_round
            )
            if st.session_state.ideas:  # 아이디어가 성공적으로 생성된 경우에만 라운드 증가
                st.session_state.current_round += 1
            st.rerun()

    # 생성된 아이디어 표시
    if st.session_state.ideas:
        st.markdown("---")
        st.markdown(f"### 🎯 현재 주제: {st.session_state.topic}")
        
        # 피드백 통계 표시
        if st.session_state.liked_ideas or st.session_state.removed_ideas:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("👍 좋아요", len(st.session_state.liked_ideas))
            with col2:
                st.metric("🗑️ 제거됨", len(st.session_state.removed_ideas))
        
        # 현재 라운드 아이디어 표시
        st.markdown(f"### 💡 #{st.session_state.current_round-1} 라운드 아이디어")
        for i, idea in enumerate(st.session_state.ideas, 1):
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1:
                st.markdown(f"**{i}.** {idea}")
            with col2:
                if st.button("👍", key=f"like_{i}"):
                    st.session_state.liked_ideas.add(idea)
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"remove_{i}"):
                    st.session_state.removed_ideas.add(idea)
                    st.rerun()
        
        st.markdown("---")
        
        # 새 아이디어 생성 버튼
        if st.button("🔄 다른 아이디어 생성하기", type="secondary", use_container_width=True):
            with st.spinner("새로운 아이디어를 생성하는 중..."):
                new_ideas = generate_ideas(
                    st.session_state.topic,
                    st.session_state.liked_ideas,
                    st.session_state.removed_ideas,
                    st.session_state.current_round
                )
                if new_ideas:  # 아이디어가 성공적으로 생성된 경우에만 업데이트
                    st.session_state.ideas = new_ideas
                    st.session_state.current_round += 1
                st.rerun()

        # 좋아한 아이디어 목록 표시
        if st.session_state.liked_ideas:
            st.markdown("### ⭐ 좋아한 아이디어 목록")
            with st.container():
                for idea in st.session_state.liked_ideas:
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(f"- {idea}")
                    with col2:
                        if st.button("🗑️ 제거", key=f"remove_liked_{idea}"):
                            st.session_state.liked_ideas.remove(idea)
                            st.rerun()
            st.markdown("---") 
