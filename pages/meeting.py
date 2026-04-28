# meeting.py
import streamlit as st
import uuid
import importlib
from pages import graphs

def render_meeting():
    st.set_page_config(page_title="실시간 AI 회의실", layout="wide")

    if st.session_state.get("compiled_graph", False):
        app = st.session_state.compiled_graph
    else:
        st.write("graph 생성을 해주세요.")

    # 고유한 회의 방 번호(thread_id) 생성 (메모리 추적용)
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
        
    # 화면에 보여줄 채팅 로그
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 상태 설정을 위한 config (체크포인터가 이 ID를 보고 기억을 불러옴)
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    st.title("🔥 실시간 AI 회의실 (Human-in-the-Loop)")


    # ================================================
    # 2. 회의록 저장 기능
    # ================================================

    import json
    import os
    from datetime import datetime

    def save_meeting_to_local(state_values):
        """현재 State 값을 받아 JSON/MD 파일로 저장하는 함수"""
        # 저장 폴더 생성
        if not os.path.exists("meeting_logs"):
            os.makedirs("meeting_logs")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. JSON 저장용 데이터 구조화
        data_to_save = {
            "topic": state_values.get("topic", "N/A"),
            "context": state_values.get("context", "N/A"),
            "history": state_values.get("chat_history", []),
            "human_feedback_last": state_values.get("human_feedback", ""),
            "timestamp": timestamp
        }
        
        filename = f"meeting_logs/meeting_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        
        return filename


    # ================================================
    # 3. 사이드바 UI
    # ================================================

    with st.sidebar:

        st.header("1. 회의 설정")
        topic = st.text_input("회의 안건", "주식 기초 교육 자료 만들기")
        context = st.text_area("맥락", "완전 초보자를 위한 10분 분량")
        draft = st.text_area("초안", "...")
        
        if st.button("회의 시작"):
            # 초기 상태 주입 및 실행
            st.session_state.messages = []
            initial_input = {
                "topic": topic, 
                "context": context, 
                "draft": draft,
                "chat_history": []
            }
            
            # app.stream으로 실행 (인간 개입 노드 직전까지 알아서 실행됨)
            for event in app.stream(initial_input, config):
                for value in event.values():
                    if "chat_history" in value:
                        st.session_state.messages.append({"role": "ai", "content": value["chat_history"][-1]})
            st.rerun()
        
        st.divider()
        st.subheader("💾 데이터 관리")
        
        if st.button("현재 회의록 저장하기", use_container_width=True):
            # 🌟 중요: LangGraph의 현재 최신 상태를 직접 가져옵니다.
            current_state = app.get_state(config)
            
            if current_state.values:
                saved_path = save_meeting_to_local(current_state.values)
                st.success(f"저장 완료! \n\n 파일명: {saved_path}")
            else:
                st.warning("저장할 회의 내용이 없습니다.")
                
        # 필요하다면 기록 전체 삭제 버튼도 추가 가능
        if st.button("채팅 로그 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # ================================================
    # 2. 채팅 화면 렌더링
    # ================================================
    with st.expander("💬 이전 대화 기록 보기", expanded=True):
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "human" else "assistant"
            with st.chat_message(role):
                st.markdown(msg["content"])

    # ================================================
    # 3. 사람의 개입 (입력창)
    # ================================================

    # 회의가 일시정지 상태(human_intervention 직전)일 때 사용자의 입력을 받음
    user_input = st.chat_input("의견을 추가하거나 '종료'를 입력하세요...")

    if user_input:
        # 화면에 내 의견 출력
        st.session_state.messages.append({"role": "human", "content": f"👤 개입: {user_input}"})
        with st.chat_message("user"):
            st.markdown(f"👤 개입: {user_input}")

        # 🌟 핵심: 일시정지된 그래프에 사람의 피드백을 밀어넣고(update_state) 재개(stream)
        app.update_state(config, {
            "human_feedback": user_input, 
            "chat_history": [f"👤 사람: {user_input}"]
        })
        
        # None을 넣고 stream을 돌리면 '멈췄던 곳부터 알아서 다시 시작'합니다.
        for event in app.stream(None, config):
            for value in event.values():
                # value가 None이 아니고, 딕셔너리이며, 내부에 chat_history가 있는지 확인
                if value and isinstance(value, dict) and "chat_history" in value:
                    latest_msg = value["chat_history"][-1]
                    
                    # 중복 방지: 내가 방금 넣은 '사람' 메시지가 다시 출력되지 않게 필터링
                    if not latest_msg.startswith("👤 사람:"):
                        st.session_state.messages.append({"role": "ai", "content": latest_msg})
                        with st.chat_message("assistant"):
                            st.markdown(latest_msg)