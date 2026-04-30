# graphs.py
import streamlit as st
from build_graph import build_langgraph

def render_graphs():
    st.title("⚙️ Graph Manager")
    st.caption("노드를 추가하고 엣지로 연결하여 에이전트의 워크플로우를 설계하세요.")
    graph_list = list(st.session_state.graphs.keys())
    selected_graph_name = st.selectbox("Graph 선택", graph_list + ["+ Graph 추가"])
    
    # --- 새 그래프 생성 ---
    if selected_graph_name == "+ Graph 추가":
        st.divider()
        new_graph_name = st.text_input("Graph 이름 (영어/언더바)")
        if st.button("Graph 생성"):
            if new_graph_name and new_graph_name not in graph_list:
                st.session_state.graphs[new_graph_name] = {
                    "nodes": list(st.session_state.agent_registry.keys()),
                    "normal_edges": [],
                    "cond_edges": []
                }
                st.rerun()
    else:
        selected_graph = st.session_state.graphs[selected_graph_name]
    
        st.divider()

        # --- 그래프 시각화 (Graphviz 사용) ---
        st.subheader("📊 그래프 프리뷰")
        if selected_graph["nodes"]:

            # DOT 언어로 그래프 생성
            dot_code = "digraph G {\n"
            dot_code += '  rankdir=LR;\n' # 왼쪽에서 오른쪽으로 흐름
            dot_code += '  node [shape=box, style=filled, color="#E1F5FE"];\n'
            
            for node in selected_graph["nodes"]:
                dot_code += f'  "{node}";\n'
            for start, end in selected_graph["normal_edges"]:
                dot_code += f'  "{start}" -> "{end}";\n'
            for start, cond, val, end in selected_graph["cond_edges"]:
                dot_code += f'  "{start}" -> "{end}" [label="{cond}-{val}", color="orange", fontcolor="orange"];\n'
            dot_code += "}"
            
            st.graphviz_chart(dot_code)
            
            # 데이터 초기화 버튼
            if st.button("⚠️ 전체 그래프 초기화"):
                st.session_state.graphs[selected_graph_name] = {
                    "nodes": [],
                    "normal_edges": [],
                    "cond_edges": []
                }
                st.rerun()
        else:
            st.info("그래프를 설계하면 여기에 시각화됩니다.")
        
        st.divider()

        # =================노드, 엣지 관리==================
        col_node, col_edge = st.columns([1, 1])

        with col_node:
            # --- 1. 노드 관리 ---
            st.subheader("노드 관리")
            with st.container(border=True):
                new_node = st.text_input("새 노드 이름", placeholder="예: researcher, writer")
                if st.button("➕ 노드 추가", use_container_width=True):
                    if new_node and new_node not in selected_graph["nodes"]:
                        selected_graph["nodes"].append(new_node)
                        st.rerun()
                    elif new_node in selected_graph["nodes"]:
                        st.warning("이미 존재하는 노드입니다.")

                # 등록된 노드 삭제 기능
                if selected_graph["nodes"]:
                    with st.expander("현재 노드:"):
                        for node in selected_graph["nodes"]:
                            c1, c2 = st.columns([4, 1])
                            c1.code(node)
                            if c2.button("🗑️", key=f"del_node_{node}"):
                                selected_graph["nodes"].remove(node)
                                st.rerun()

        with col_edge:
            # --- 2. 엣지 관리 ---
            st.subheader("엣지 연결")
            if not selected_graph["nodes"]:
                st.info("먼저 노드를 추가해야 엣지를 연결할 수 있습니다.")
            else:
                with st.container(border=True):
                    tab_normal, tab_cond = st.tabs(["일반 엣지", "조건부 엣지"])
                    with tab_normal:
                        f_node = st.selectbox("출발", selected_graph["nodes"] + ["__START__"], key="f_norm")
                        t_node = st.selectbox("도착", selected_graph["nodes"] + ["__END__"], key="t_norm")
                        if st.button("🔗 일반 엣지 연결", use_container_width=True):
                            edge = (f_node, t_node)
                            if edge not in selected_graph["normal_edges"]:
                                selected_graph["normal_edges"].append(edge)
                                st.rerun()
                    with tab_cond:
                        cf_node = st.selectbox("출발", selected_graph["nodes"], key="cf_cond")
                        c_cond = st.text_input("조건", placeholder="예: is_success", key="c_cond")
                        c_val = st.text_input("조건명", placeholder="예: success, failure", key="c_val")
                        ct_node = st.selectbox("도착", selected_graph["nodes"] + ["__END__"], key="ct_cond")
                        if st.button("🔀 조건부 엣지 연결", use_container_width=True):
                            if c_cond and c_val:
                                c_edge = (cf_node, c_cond, c_val, ct_node)
                                if c_edge not in selected_graph["cond_edges"]:
                                    selected_graph["cond_edges"].append(c_edge)
                                    st.rerun()
        st.divider()

        # ===============시스템 적용, 그래프 삭제 버튼============================
        c_btn1, c_btn2 = st.columns([5, 1])
        if c_btn1.button("🚀 그래프 빌드 및 시스템 적용", type="primary", use_container_width=True):
            try:

                compiled_app = build_langgraph(selected_graph)
                if compiled_app:
                    st.session_state.compiled_graph = compiled_app
                    st.success("✅ 그래프가 성공적으로 빌드되었습니다! Meeting 탭에서 테스트하세요.")
                else:
                    st.error("노드가 설정되지 않았습니다.")
            except Exception as e:
                st.error(f"빌드 오류: {e}")

        # 삭제 버튼
        if c_btn2.button("🗑️ Graph 삭제"):
            del st.session_state.graphs[selected_graph_name]
            st.rerun()