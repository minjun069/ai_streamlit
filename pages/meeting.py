# meeting.py
import streamlit as st
from build_graph import get_initial_state
import json
import os
from datetime import datetime

def render_meeting():
    if st.session_state.get("compiled_graph", False):
        app = st.session_state.compiled_graph
    else:
        st.write("먼저 Graph를 빌드해주세요.")

    st.title("🔥 실시간 AI 회의실")

    # ================================================
    # 회의록 저장 기능
    # ================================================
    def save_messages():
        """현재 State 값을 받아 JSON/MD 파일로 저장하는 함수"""
        # 저장 폴더 생성
        if not os.path.exists("meeting_logs"):
            os.makedirs("meeting_logs")

        data_to_save = {"timestamp": st.session_state.timestamp}
        data_to_save.update(st.session_state.initial_input)
        data_to_save["messages"] = st.session_state.messages
        
        filename = f"meeting_logs/meeting_{st.session_state.timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        
        return filename


    # ================================================
    # 3. 사이드바 UI
    # ================================================
    with st.sidebar:
        st.header("회의 설정")

        initial_input = get_initial_state()
        initial_input["latest_raw_output"] = []
        if st.session_state.get("start_task"):
            
            for req in st.session_state.agent_registry[st.session_state.start_task]["requirements"]:
                text = st.text_area(req["label"], st.session_state.inputs.get(req["label"], "입력해주세요."))
                st.session_state.inputs[req["label"]] = text
                initial_input[req["key"]] = text
            st.session_state.initial_input = initial_input

            recursion_limit = st.number_input(
                "Recursion Limit", 
                min_value=1,      # 최소값
                max_value=100,    # 최대값
                value=10,         # 초기값
                step=1            # 증감 단위
            )
            config = {
                "configurable": {"thread_id": st.session_state.thread_id},
                "recursion_limit": recursion_limit
            }
            st.session_state.config = config
        else:
            st.text("먼저 Graph를 선택하고 생성해주세요")

        st.divider()
        st.subheader("💾 데이터 관리")
        
        if st.button("현재 회의록 저장하기", use_container_width=True):
            if st.session_state.messages:
                saved_path = save_messages()
                st.success(f"저장 완료! \n\n 파일명: {saved_path}")
            else:
                st.warning("저장할 회의 내용이 없습니다.")
                
        if st.button("채팅 로그 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # ================================================
    # 2. 채팅 화면 렌더링
    # ================================================
    for msg in st.session_state.messages:
        with st.expander(f"💬{msg["role"]}", expanded=False):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if st.session_state.meeting_status == "finished":
        user_input = st.chat_input("의견을 입력하세요.")
        st.session_state.user_input = user_input

    if st.button("회의 시작"):
        with st.spinner("회의 중... 🧠"):
            try:
                st.session_state.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.session_state.meeting_status = "running"
                st.session_state.messages = []

                if st.session_state.user_input == "":
                    for event in app.stream(initial_input, st.session_state.config):
                        for value in event.values():
                            msg = {"role": value["curr_agent"], "content": value["latest_raw_output"]}
                            st.session_state.messages.append(msg)
                            with st.expander(f"💬{msg["role"]}", expanded=False):
                                with st.chat_message(msg["role"]):
                                    st.markdown(msg["content"])
                else:
                    app.update_state(st.session_state.config, {"latest_raw_output": f"관리자: {st.session_state.user_input}"})
                    for event in app.stream(None, st.session_state.config):
                        for value in event.values():
                            st.session_state.messages.append({"role": "ai", "content": value["latest_raw_output"]})

                st.session_state.meeting_status = "finished"
                st.session_state.compiled_graph = app
                st.rerun()

            except Exception as e:
                st.error(f"회의 중 오류 발생: {e}")
                st.session_state.meeting_status = "error"
                st.session_state.meeting_status = "finished"
                st.session_state.compiled_graph = app
                st.rerun()