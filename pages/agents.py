# agents.py
import streamlit as st
import json

def render_agents():

    # --- Task 목록 및 추가 ---
    st.title("⚙️ Agent Manager")
    task_list = list(st.session_state.agent_registry.keys())
    selected_task = st.selectbox("수정할 Task 선택", task_list + ["+ Agent 추가"], index=st.session_state.get("prev_selected_task_idx", 0))
    
    if selected_task == "+ Agent 추가":
        new_task_name = st.text_input("Agent 이름 (영어/언더바)")
        if st.button("Agent 생성"):
            if new_task_name and new_task_name not in st.session_state.agent_registry:
                st.session_state.agent_registry[new_task_name] = {
                    "system_prompt": "", 
                    "human_prompt": "", 
                    "output_mapping": "output",
                    "schema": None, 
                    "static_returns": {},
                    "requirements": []
                }
                st.session_state.prev_selected_task_idx = len(task_list)
                st.rerun()

    st.divider()

    # --- 3. 메인 화면: Task 상세 설정 ---
    if selected_task and selected_task != "+ Agent 추가":
        task_data = st.session_state.agent_registry[selected_task]

        # --------------
        ## Prompts
        st.subheader("Prompts")
        system_p = st.text_area("System Prompt", value=task_data["system_prompt"], height=150)
        human_p = st.text_area("Human Prompt", value=task_data["human_prompt"], height=200)
        st.caption("`{variable}` 형식을 사용하여 state의 변수를 매핑하세요.")
        
        # --------------
        ## Requirements
        st.subheader("📋 Requirements 설정")
        st.caption("이 에이전트가 작동하기 위해 State에서 반드시 필요한 변수들을 정의하세요.")

        if "requirements" not in task_data:
            # 기존에 dict 형태의 requirements가 있다면 리스트로 변환해서 초기화
            current_reqs = task_data.get("requirements", [])
            task_data["requirements"] = [
                {"label": k, "key": k, "type": "str"} for k in current_reqs.keys()
            ]
        
        new_req_list = []

        h_col1, h_col2, h_col3, h_col4 = st.columns([3, 3, 2, 1])
        h_col1.write("**이름 (Label)**")
        h_col2.write("**변수명 (Key)**")
        h_col3.write("**자료형 (Type)**")
        h_col4.write("**삭제**")

        for idx, req in enumerate(task_data["requirements"]):
            col1, col2, col3, col4 = st.columns([3, 3, 2, 1])
            with col1:
                label = st.text_input(f"label_{idx}", value=req["label"], label_visibility="collapsed", key=f"req_label_{selected_task}_{idx}")
            with col2:
                key = st.text_input(f"key_{idx}", value=req["key"], label_visibility="collapsed", key=f"req_key_{selected_task}_{idx}")
            with col3:
                type_options = ["str", "int", "bool"]
                default_idx = type_options.index(req["type"]) if req["type"] in type_options else 0
                dtype = st.selectbox(f"type_{idx}", options=type_options, index=default_idx, label_visibility="collapsed", key=f"req_type_{selected_task}_{idx}")
            with col4:
                if st.button("🗑️", key=f"req_del_{selected_task}_{idx}"):
                    task_data["requirements"].pop(idx)
                    st.rerun()

            new_req_list.append({"label": label, "key": key, "type": dtype})

        if st.button("➕ Requirements 추가"):
            task_data["requirements"].append({"label": "", "key": "", "type": "str"})
            st.rerun()

        # --------------
        ## Mappings & Outputs
        st.subheader("Mappings & Outputs")
        out_map = st.text_input("Output 저장 변수명", value=task_data["output_mapping"])
        has_schema = st.checkbox("Schema 사용 여부", value=task_data["schema"] is not None)
        schema_val = None
        if has_schema:
            schema_text = st.text_area("Schema 정의 (JSON/Field List)", placeholder='{"field1": "string"}')
            schema_val = schema_text # 실제 구현 시에는 명칭만 저장하거나 class 매핑 로직 필요
            
        static_ret = st.text_area("Static Returns (고정 리턴값 JSON)", 
                                value=json.dumps(task_data.get("static_returns", {})))

        # --------------
        # 저장 및 삭제 버튼
        c_btn1, c_btn2, _ = st.columns([1, 1, 2])
        if c_btn1.button("💾 설정 저장", type="primary"):
            st.session_state.agent_registry[selected_task].update({
                "system_prompt": system_p,
                "human_prompt": human_p,
                "output_mapping": out_map,
                "schema": schema_val if has_schema else None,
                "static_returns": json.loads(static_ret) if static_ret else {},
                "requirements": new_req_list,
            })
            st.success("설정이 저장되었습니다.")

        if c_btn2.button("🗑️ Agent 삭제"):
            del st.session_state.agent_registry[selected_task]
            st.rerun()

        # --- 4. 최종 Registry 결과 확인 (복사해서 코드에 적용 가능) ---
        st.divider()
        with st.expander("📄 전체 Agent 보기"):
            st.code(json.dumps(st.session_state.agent_registry, indent=4, ensure_ascii=False), language="json")

    else:
        st.info("관리할 Agent를 선택하거나 새로 생성해 주세요.")