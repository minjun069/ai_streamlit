# build_graph.py
import streamlit as st

from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


# 0. llm 호출
@st.cache_resource
def get_llm():
    from dotenv import load_dotenv
    load_dotenv()
    from langchain_google_genai import GoogleGenerativeAI
    return GoogleGenerativeAI(model="gemini-2.5-flash")

llm = get_llm()

# 1. 상태 정의 (기존에 정의한 구조)
class AgentState(TypedDict):
    logs: Annotated[list[str], operator.add]
    # 여기에 필요한 다른 상태 값들을 추가 (예: task_results, input_data 등)

def call_task(task_name: str, state: AgentState) -> dict:
    # 1. 설정 불러오기
    config = st.session_state.agent_registry[task_name]

    # 2. 프롬프트 준비
    prompt = ChatPromptTemplate.from_messages([
        ("system", config["system_prompt"]),
        ("human", config["human_prompt"])
    ])

    # 3. 파서 및 체인 연결
    if config["schema"]:
        parser = PydanticOutputParser(pydantic_object=config["schema"])
        prompt = prompt.partial(format=parser.get_format_instructions())
        chain = prompt | llm | parser
    else:
        chain = prompt | llm

    # 4. LLM 실행 (input_prep이 있으면 실행하고, 없으면 state 통째로 전달)
    # LangChain은 prompt에 필요한 변수만 state에서 알아서 쏙쏙 골라 씁니다.
    invoke_inputs = {**state, **config["input_prep"](state)} if "input_prep" in config else state
    result = chain.invoke(invoke_inputs)

    # 5. 리턴할 State 딕셔너리 조립
    updates = {}

    # schema가 있으면 Pydantic 객체를 딕셔너리로 변환해서 넣음 (예: is_sufficient, parsed_intent 등)
    if config.get("schema", None):
        updates.update(result.model_dump())

    # schema가 없으면 output_mapping 이름으로 문자열을 넣음 (예: worker_output)
    else:
        updates[config["output_mapping"]] = result

    # 고정 리턴값 및 로그 추가
    updates.update(config.get("static_returns", {}))
    updates["logs"] = [f"[{task_name}] 완료"]

    return updates

# 2. 그래프 빌드 함수
def build_langgraph():

    # 0. 데이터 검증
    if not st.session_state.nodes:
        return None

    # 1. 그래프 초기화
    workflow = StateGraph(AgentState)
    
    for node_name in st.session_state.nodes:
        # 각 노드가 실행될 때 자신의 이름을 call_task에 전달하도록 람다/부분함수 구성
        workflow.add_node(node_name, lambda state, name=node_name: call_task(name, state))

    # 3. 일반 엣지 추가
    for start, end in st.session_state.normal_edges:
        start = START if start == "__START__" else start
        target = END if end == "__END__" else end
        workflow.add_edge(start, target)

    # 4. 조건부 엣지 추가
    # 출발 노드별로 조건들을 그룹화해야 합니다.
    from collections import defaultdict
    cond_map = defaultdict(dict)
    for start, label, end in st.session_state.cond_edges:
        target = END if end == "__END__" else end
        cond_map[start][label] = target

    for start_node, path_map in cond_map.items():
        # 간단한 라우터 함수: 상태 내 특정 값이나 로직에 따라 path_map의 키를 반환
        # 여기서는 예시로 'next_step'이라는 상태 값을 기준으로 분기한다고 가정
        def router(state, paths=path_map):
            # 실제로는 state["some_decision_value"] 등을 보고 분기합니다.
            # 지금은 UI에서 설정한 '조건명'이 state에 저장되어 있다고 가정하거나 
            # 특정 로직에 따라 결정되도록 작성합니다.
            return state.get("decision", list(paths.keys())[0])
        
        workflow.add_conditional_edges(start_node, router, path_map)

    # 5. 진입점 설정 (첫 번째 노드를 시작점으로 가정)
    workflow.set_entry_point(st.session_state.nodes[0])

    # 6. 컴파일
    return workflow.compile()