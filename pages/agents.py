# agents.py
import streamlit as st
import json

def render_agents():
    st.title("⚙️ Agent Manager")

    # --- 전체 Agent 정보 ---
    with st.expander("📄 전체 Agent 보기"):
        st.code(json.dumps(st.session_state.agents, indent=4, ensure_ascii=False), language="json")
    st.divider()

    # --- Agent 목록 및 추가 ---
    agent_list = list(st.session_state.agents.keys())
    options = agent_list + ["+ Agent 추가"]
    prev_agent = st.session_state.temps.get("prev_agent", "+ Agent 추가")
    try:
        prev_index = options.index(prev_agent)
    except ValueError:
        prev_index = len(options) - 1
    selected_agent = st.selectbox("Agent 선택", options, index=prev_index)
    st.session_state.temps["prev_agent"] = selected_agent

    # --- Agent 추가 ---
    if selected_agent == "+ Agent 추가":
        new_agent = st.text_input("Agent 이름 (영어/언더바)")
        if st.button("Agent 생성"):
            if new_agent:
                if new_agent not in agent_list:
                    st.session_state.agents[new_agent] = {
                        "system_prompt": "", 
                        "human_prompt": "", 
                        "output_mapping": "output",
                        "schema": None, 
                        "static_returns": {},
                        "requirements": []
                    }
                    st.session_state.temps["prev_agent"] = new_agent
                    st.rerun()
                else:
                    st.info("이미 있는 Agent 이름입니다.")
            else:
                st.info("Agent 이름을 입력하세요.")
        st.divider()

    # --- Agent 상세 설정 ---
    else:
        agent_data = st.session_state.agents[selected_agent]

        # --------------
        ## Prompts
        st.subheader("📋 Prompts")
        system_p = st.text_area("System Prompt", value=agent_data["system_prompt"], height=150)
        human_p = st.text_area("Human Prompt", value=agent_data["human_prompt"], height=200)
        st.caption("`{variable}` 형식을 사용하여 state의 변수를 매핑하세요.")
        
        # --------------
        ## Requirements
        st.subheader("📋 Requirements 설정")
        st.caption("이 에이전트가 작동하기 위해 State에서 반드시 필요한 변수들을 정의하세요.")
        
        new_req_list = []

        h_col1, h_col2, h_col3, h_col4 = st.columns([3, 3, 2, 1])
        h_col1.write("**이름 (Label)**")
        h_col2.write("**변수명 (Key)**")
        h_col3.write("**자료형 (Type)**")
        h_col4.write("**삭제**")

        for idx, req in enumerate(agent_data["requirements"]):
            col1, col2, col3, col4 = st.columns([3, 3, 2, 1])
            with col1:
                label = st.text_input(f"label_{idx}", value=req["label"], label_visibility="collapsed", key=f"req_label_{selected_agent}_{idx}")
            with col2:
                key = st.text_input(f"key_{idx}", value=req["key"], label_visibility="collapsed", key=f"req_key_{selected_agent}_{idx}")
            with col3:
                type_options = ["str", "int", "bool"]
                default_idx = type_options.index(req["type"]) if req["type"] in type_options else 0
                dtype = st.selectbox(f"type_{idx}", options=type_options, index=default_idx, label_visibility="collapsed", key=f"req_type_{selected_agent}_{idx}")
            with col4:
                if st.button("🗑️", key=f"req_del_{selected_agent}_{idx}"):
                    agent_data["requirements"].pop(idx)
                    st.rerun()

            new_req_list.append({"label": label, "key": key, "type": dtype})

        if st.button("➕ Requirements 추가"):
            agent_data["requirements"].append({"label": "", "key": "", "type": "str"})
            st.rerun()

        # --------------
        ## Mappings & Outputs
        st.subheader("📋 Mappings & Outputs")

        # 단일 output
        out_map = st.text_input("Output 저장 변수명", value=agent_data["output_mapping"])

        # schema
        has_schema = st.checkbox("Schema 사용 여부", value=(agent_data["schema"] is not None))
        schema_val = None
        if has_schema:
            schema_val = st.text_area("Schema 정의 (JSON/Field List)", placeholder='{"field1": "string"}')
            # schema_val = class_mapping_sth(scheme_val)
        
        # static_returns
        static_ret = st.text_area("Static Returns (고정 리턴값 JSON)", value=json.dumps(agent_data["static_returns"]))

        # --------------
        # 저장 및 삭제 버튼
        c_btn1, c_btn2, _ = st.columns([1, 1, 2])
        if c_btn1.button("💾 설정 저장", type="primary"):
            st.session_state.agents[selected_agent].update({
                "system_prompt": system_p,
                "human_prompt": human_p,
                "output_mapping": out_map,
                "schema": schema_val,
                "static_returns": static_ret,
                "requirements": new_req_list,
            })
            st.success("설정이 저장되었습니다.")

        if c_btn2.button("🗑️ Agent 삭제"):
            del st.session_state.agents[selected_agent]
            st.rerun()
