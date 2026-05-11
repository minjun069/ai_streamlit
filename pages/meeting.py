# meeting.py
import streamlit as st

import json
import os
from datetime import datetime
from build_graph import build_langgraph

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

def render_meeting():
    # ================================================
    # 사이드바 UI
    # ================================================
    with st.sidebar:
        st.header("회의 설정")

        thread_list = list(st.session_state.threads.keys())
        options = thread_list + ["+ 새 회의"]
        prev_thread = st.session_state.temps.get("prev_thread", "+ 새 회의")
        try:
            prev_index = options.index(prev_thread)
        except ValueError:
            prev_index = len(options) - 1
        selected_thread = st.selectbox("회의 선택", thread_list + ["+ 새 회의"], index=prev_index)

        # --- 새 회의 ---
        if selected_thread == "+ 새 회의":
            new_thread = st.text_input("회의 이름 (영어/언더바)")
            if st.button("회의 추가"):
                if new_thread:
                    if new_thread not in thread_list:
                        st.session_state.threads[new_thread] = {
                            "messages": [],
                            "initial_input": {},
                            "graph_name": "",
                            "timestamp": "",
                            "config": {}
                        }
                        st.session_state.temps["prev_thread"] = new_thread
                        st.rerun()
                    else:
                        st.warning("이미 존재하는 회의 이름입니다.")
                else:
                    st.warning("회의 이름을 입력하세요.")
        
        else:
            # --- 그래프 선택 및 빌드 ---
            st.subheader("그래프 선택")
            graph_list = list(st.session_state.graphs.keys())
            if graph_list:
                selected_graph = st.selectbox("Graph 선택", graph_list, #prev_thread_graph 추가)
                if st.button("🚀 그래프 빌드 및 시스템 적용", type="primary", use_container_width=True):
                    try:
                        st.session_state.temps[selected_thread]["compiled_graph"] = build_langgraph(st.session_state.graphs[selected_graph])
                        st.success("✅ 그래프가 성공적으로 빌드되었습니다!")
                    except Exception as e:
                        st.error(f"빌드 오류: {e}")
                
                if st.session_state.temps.get(selected_thread, {}).get("compiled_graph"):
                    st.divider()
                    # ==============================
                    # 초기값 입력
                    # ==============================
                    for req in st.session_state.agent_registry[st.session_state.temps["start_task"]]["requirements"]:
                        text = st.text_area(req["label"], st.session_state.initial_input.get(req["label"], "입력해주세요."))
                        st.session_state.initial_input[req["label"]] = text

                    recursion_limit = st.number_input(
                        "Recursion Limit", 
                        min_value=1,      # 최소값
                        max_value=100,    # 최대값
                        value=10,         # 초기값
                        step=1            # 증감 단위
                    )
                    st.session_state.config = {
                        "configurable": {"thread_id": st.session_state.thread_id},
                        "recursion_limit": recursion_limit
                    }
                else:
                    st.info("먼저 그래프를 빌드해주세요.")
            else:
                st.info("먼저 그래프를 생성해주세요.")

            # ==============================
            # 회의록 저장 및 초기화
            # ==============================
            if st.session_state.meeting_status == "finished":
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
    # 채팅 화면 렌더링
    # ================================================

    st.title("🔥 실시간 AI 회의실")

    for msg in st.session_state.messages:
        with st.expander(f"💬{msg["role"]}", expanded=False):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if st.session_state.meeting_status == "finished":
        user_input = st.chat_input("의견을 입력하세요.")
        st.session_state.user_input = user_input

    if st.session_state.get("compiled_graph", False):
        if st.button("회의 시작"):
            with st.spinner("회의 중... 🧠"):
                try:
                    st.session_state.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.session_state.meeting_status = "running"
                    st.session_state.messages = []

                    if st.session_state.user_input == "":
                        for event in st.session_state.compiled_graph.stream(st.session_state.initial_input, st.session_state.config):
                            for value in event.values():
                                msg = {"role": value["curr_agent"], "content": value["latest_raw_output"]}
                                st.session_state.messages.append(msg)
                                with st.expander(f"💬{msg["role"]}", expanded=False):
                                    with st.chat_message(msg["role"]):
                                        st.markdown(msg["content"])
                    else:
                        st.session_state.compiled_graph.update_state(st.session_state.config, {"latest_raw_output": f"관리자: {st.session_state.user_input}"})
                        for event in st.session_state.compiled_graph.stream(None, st.session_state.config):
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
    else:
        st.info("먼저 그래프를 선택하고 빌드해주세요.")