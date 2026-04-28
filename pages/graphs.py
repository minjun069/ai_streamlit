# graphs.py
import streamlit as st
from build_graph import build_langgraph

def render_graphs():

    # 세션 상태 초기화 확인 (app.py에서 처리하지만 안전을 위해)
    if "nodes" not in st.session_state: st.session_state.nodes = [] + list(st.session_state.agent_registry.keys())
    if "normal_edges" not in st.session_state: st.session_state.normal_edges = []
    if "cond_edges" not in st.session_state: st.session_state.cond_edges = []

    st.title("⚙️ Graph Manager")
    st.caption("노드를 추가하고 엣지로 연결하여 에이전트의 워크플로우를 설계하세요.")
    st.divider()
    
    # --- 그래프 시각화 (Graphviz 사용) ---
    st.subheader("📊 그래프 프리뷰")
    if st.session_state.nodes:
        # DOT 언어로 그래프 생성
        dot_code = "digraph G {\n"
        dot_code += '  rankdir=LR;\n' # 왼쪽에서 오른쪽으로 흐름
        dot_code += '  node [shape=box, style=filled, color="#E1F5FE"];\n'
        
        # 노드 추가
        for node in st.session_state.nodes:
            dot_code += f'  "{node}";\n'
        # 일반 엣지 추가
        for start, end in st.session_state.normal_edges:
            dot_code += f'  "{start}" -> "{end}";\n'
        # 조건부 엣지 추가
        for start, cond, end in st.session_state.cond_edges:
            dot_code += f'  "{start}" -> "{end}" [label="{cond}", color="orange", fontcolor="orange"];\n'
        dot_code += "}"
        
        st.graphviz_chart(dot_code)
        
        # 데이터 초기화 버튼
        if st.button("⚠️ 전체 그래프 초기화"):
            st.session_state.nodes = []
            st.session_state.normal_edges = []
            st.session_state.cond_edges = []
            st.rerun()
    else:
        st.info("그래프를 설계하면 여기에 시각화됩니다.")
    
    st.divider()

    # 화면을 두 구역으로 나눔
    col_node, col_edge = st.columns([1, 1])

    with col_node:
        # --- 1. 노드 관리 ---
        st.subheader("노드 관리")
        with st.container(border=True):
            new_node = st.text_input("새 노드 이름", placeholder="예: researcher, writer")
            if st.button("➕ 노드 추가", use_container_width=True):
                if new_node and new_node not in st.session_state.nodes:
                    st.session_state.nodes.append(new_node)
                    st.rerun()
                elif new_node in st.session_state.nodes:
                    st.warning("이미 존재하는 노드입니다.")

            # 등록된 노드 삭제 기능
            if st.session_state.nodes:
                with st.expander("현재 노드:"):
                    for node in st.session_state.nodes:
                        c1, c2 = st.columns([4, 1])
                        c1.code(node)
                        if c2.button("🗑️", key=f"del_node_{node}"):
                            st.session_state.nodes.remove(node)
                            st.rerun()

    with col_edge:
        # --- 2. 엣지 관리 ---
        st.subheader("엣지 연결")
        if not st.session_state.nodes:
            st.info("먼저 노드를 추가해야 엣지를 연결할 수 있습니다.")
        else:
            with st.container(border=True):
                tab_normal, tab_cond = st.tabs(["일반 엣지", "조건부 엣지"])
                with tab_normal:
                    f_node = st.selectbox("출발", st.session_state.nodes + ["__START__"], key="f_norm")
                    t_node = st.selectbox("도착", st.session_state.nodes + ["__END__"], key="t_norm")
                    if st.button("🔗 일반 엣지 연결", use_container_width=True):
                        edge = (f_node, t_node)
                        if edge not in st.session_state.normal_edges:
                            st.session_state.normal_edges.append(edge)
                            st.rerun()
                with tab_cond:
                    cf_node = st.selectbox("출발", st.session_state.nodes, key="cf_cond")
                    c_val = st.text_input("조건명", placeholder="예: success, failure", key="c_val")
                    ct_node = st.selectbox("도착", st.session_state.nodes + ["__END__"], key="ct_cond")
                    if st.button("🔀 조건부 엣지 연결", use_container_width=True):
                        if c_val:
                            c_edge = (cf_node, c_val, ct_node)
                            if c_edge not in st.session_state.cond_edges:
                                st.session_state.cond_edges.append(c_edge)
                                st.rerun()
    st.divider()
    if st.button("🚀 그래프 빌드 및 시스템 적용", type="primary", use_container_width=True):
        try:

            compiled_app = build_langgraph()
            if compiled_app:
                st.session_state.compiled_graph = compiled_app
                st.success("✅ 그래프가 성공적으로 빌드되었습니다! Meeting 탭에서 테스트하세요.")
            else:
                st.error("노드가 설정되지 않았습니다.")
        except Exception as e:
            st.error(f"빌드 오류: {e}")