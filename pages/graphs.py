# graphs.py
import streamlit as st

def render_graphs():
    st.title("⚙️ Graph Manager")
    st.caption("노드를 추가하고 엣지로 연결하여 에이전트의 워크플로우를 설계하세요.")

    graph_list = list(st.session_state.graphs.keys())
    options = graph_list + ["+ Graph 추가"]
    prev_graph = st.session_state.temps.get("prev_graph", "+ Graph 추가")
    try:
        prev_index = options.index(prev_graph)
    except ValueError:
        prev_index = len(options) - 1
    selected_graph = st.selectbox("Graph 선택", options, index=prev_index)
    st.session_state.temps["prev_graph"] = selected_graph

    # --- Graph 추가 ---
    if selected_graph == "+ Graph 추가":
        new_graph = st.text_input("Graph 이름 (영어/언더바)")
        if st.button("Graph 생성"):
            if new_graph:
                if new_graph not in graph_list:
                    st.session_state.graphs[new_graph] = {
                        "nodes": [],
                        "normal_edges": [],
                        "cond_edges": []
                    }
                    st.session_state.temps["prev_graph"] = new_graph
                    st.rerun()
                else:
                    st.warning("이미 존재하는 그래프 이름입니다.")
            else:
                st.warning("Graph 이름을 입력하세요.")
        st.divider()
    
    # --- Graph 시각화 및 상세 설정 ---
    else:
        graph_data = st.session_state.graphs[selected_graph]

        # --- 그래프 시각화 ---
        st.subheader("📊 그래프 프리뷰")
        if graph_data["nodes"]:

            # DOT 언어로 그래프 생성
            dot_code = "digraph G {\n"
            dot_code += '  rankdir=LR;\n' # 왼쪽에서 오른쪽으로 흐름
            dot_code += '  node [shape=box, style=filled, color="#E1F5FE", fontname="Arial"];\n'
            dot_code += '  "__START__" [shape=circle, style=filled, color="#C8E6C9", label="START"];\n'
            dot_code += '  "__END__" [shape=doublecircle, style=filled, color="#FFCCBC", label="END"];\n'
            
            for node in graph_data["nodes"]:
                dot_code += f'  "{node}";\n'
            for start, end in graph_data["normal_edges"]:
                dot_code += f'  "{start}" -> "{end}";\n'
            for start, cond, val, end in graph_data["cond_edges"]:
                dot_code += f'  "{start}" -> "{end}" [label="{cond}-{val}", color="orange", fontcolor="orange"];\n'
            dot_code += "}"
            
            st.graphviz_chart(dot_code)
        else:
            st.info("노드를 추가하세요.")
        st.divider()

        # --- 노드, 엣지 관리 ---
        col_node, col_edge = st.columns([1, 1])

        with col_node:
            st.subheader("노드 추가")
            with st.container(border=True):
                if st.session_state.agents:
                    new_node = st.selectbox("Agent 선택", list(st.session_state.agents.keys()))
                    if st.button("➕ 노드 추가", use_container_width=True):
                        if new_node not in graph_data["nodes"]:
                            graph_data["nodes"].append(new_node)
                            st.rerun()
                        else:
                            st.warning("이미 그래프에 존재하는 노드입니다.")
                else:
                    st.info("먼저 Agent를 생성해주세요.")

                # 노드 확인 및 삭제
                if graph_data["nodes"]:
                    with st.container(border=True):
                        for node in graph_data["nodes"]:
                            c1, c2 = st.columns([4, 1])
                            c1.code(node)
                            if c2.button("🗑️", key=f"del_node_{node}"):
                                graph_data["nodes"].remove(node)
                                graph_data["normal_edges"] = [e for e in graph_data["normal_edges"] if node not in e]
                                graph_data["cond_edges"] = [e for e in graph_data["cond_edges"] if node != e[0] and node != e[3]]
                                st.rerun()

        with col_edge:
            st.subheader("엣지 연결")
            if not graph_data["nodes"]:
                st.info("먼저 노드를 추가하세요.")
            else:
                with st.container(border=True):
                    tab_normal, tab_cond = st.tabs(["일반 엣지", "조건부 엣지"])
                    with tab_normal:
                        f_node = st.selectbox("출발", graph_data["nodes"] + ["__START__"], key=f"f_norm_{selected_graph}")
                        t_node = st.selectbox("도착", graph_data["nodes"] + ["__END__"], key=f"t_norm_{selected_graph}")
                        if st.button("🔗 일반 엣지 연결", use_container_width=True):
                            edge = (f_node, t_node)
                            if edge not in graph_data["normal_edges"]:
                                graph_data["normal_edges"].append(edge)
                                st.rerun()
                    with tab_cond:
                        cf_node = st.selectbox("출발", graph_data["nodes"], key=f"cf_cond_{selected_graph}")
                        c_cond = st.text_input("조건", placeholder="예: is_success", key=f"c_cond_{selected_graph}")
                        c_val = st.text_input("조건명", placeholder="예: success, failure", key=f"c_val_{selected_graph}")
                        ct_node = st.selectbox("도착", graph_data["nodes"] + ["__END__"], key=f"ct_cond_{selected_graph}")
                        if st.button("🔀 조건부 엣지 연결", use_container_width=True):
                            if c_cond and c_val:
                                c_edge = (cf_node, c_cond, c_val, ct_node)
                                if c_edge not in graph_data["cond_edges"]:
                                    graph_data["cond_edges"].append(c_edge)
                                    st.rerun()
        st.divider()

        # --- 그래프 초기화 및 삭제 ---
        c_btn1, c_btn2, _ = st.columns([1, 1, 4])
        
        if c_btn1.button("⚠️ 전체 그래프 초기화"):
            st.session_state.graphs[selected_graph] = {
                "nodes": [],
                "normal_edges": [],
                "cond_edges": []
            }
            st.rerun()

        if c_btn2.button("🗑️ Graph 삭제"):
            del st.session_state.graphs[selected_graph]
            st.rerun()