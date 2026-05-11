import streamlit as st
import json
import os

from pages import agents, graphs, meeting

# =====================================
# 1. 파일 시스템 설정 
# =====================================
DATA_DIR = "work_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_works():
    """저장된 모든 작업 파일 목록을 가져옴"""
    return [f.replace(".json", "") for f in os.listdir(DATA_DIR) if f.endswith(".json")]

def save_work_to_file(work):
    """현재 세션 상태를 파일에 저장"""
    file_path = os.path.join(DATA_DIR, f"{work}.json")
    data = {
        "agents": st.session_state.get("agents", {}),
        "graphs": st.session_state.get("graphs", {}),
        "threads": st.session_state.get("threads", {})
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_work_from_file(work):
    """파일에서 데이터를 읽어 세션에 로드"""
    file_path = os.path.join(DATA_DIR, f"{work}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            st.session_state.current_work = work
            st.session_state.agents = data.get("agents", {})
            st.session_state.graphs = data.get("graphs", {})
            st.session_state.threads = data.get("threads", {})

# =====================================
# 2. 전역 상태 초기화
# =====================================
def initiate_state(target):
    defaults = {
        "current_work": "",
        "threads": {},
        "agents": {},
        "graphs": {},
        "temps": {}
    }
    for key, val in defaults.items():
        if target == "all":
            st.session_state[key] = val
        else:
            if key not in st.session_state:
                st.session_state[key] = val

# =====================================
# 3. 화면 렌더링
# =====================================
st.set_page_config(page_title="실시간 AI 회의실", layout="wide")

# CASE 1: 대시보드 (파일 목록 보기 및 생성)
if not st.session_state.get("current_work"):
    initiate_state("rerun")

    st.title("🗂️ 프로젝트 매니저")
    
    # 새 작업 생성
    with st.expander("➕ 새 작업 만들기"):
        new_name = st.text_input("프로젝트 이름")
        if st.button("생성"):
            if new_name:
                # 초기 빈 파일 생성
                save_work_to_file(new_name)
                st.rerun()
    st.divider()

    st.subheader("📁 저장된 작업 목록")
    files = get_works()
    if not files:
        st.info("저장된 파일이 없습니다.")
    else:
        for f_name in files:
            col1, col2 = st.columns([4, 1])
            if col1.button(f"📖 {f_name}", use_container_width=True):
                load_work_from_file(f_name)
                st.rerun()
            if col2.button("🗑️", key=f"del_{f_name}"):
                os.remove(os.path.join(DATA_DIR, f"{f_name}.json"))
                st.rerun()

# CASE 2: 작업 공간 (탭 UI)
else:
    c1, c2 = st.columns([7, 3])
    c1.title(f"🚀 {st.session_state.current_work}")
    
    if c2.button("💾 저장 후 나가기"):
        save_work_to_file(st.session_state.current_work)
        initiate_state("all")
        st.rerun()
    
    t1, t2, t3 = st.tabs(["Agents", "Graphs", "Meeting"])
    with t1:
        agents.render_agents()
    with t2:
        graphs.render_graphs()
    with t3:
        meeting.render_meeting()