# build_graph.py
import streamlit as st

from typing import TypedDict, List, Dict, Annotated, Optional, get_type_hints
import operator
from collections import defaultdict

from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from langgraph.checkpoint.memory import MemorySaver

# 0. llm 호출
@st.cache_resource
def get_llm():
    from dotenv import load_dotenv
    load_dotenv()
    from langchain_google_genai import GoogleGenerativeAI
    return GoogleGenerativeAI(model="gemini-2.5-flash")
llm = get_llm()


# 1. AgentState 및 초기화 함수 정의
class TaskStep(TypedDict):
    total_seq: int
    agent_role: str
    role_seq: int
    # output_summary: str

class BaseAgentState(TypedDict):
    curr_seq: int
    task_seq: Dict[str, int]
    curr_agent: str
    task_history: Annotated[List[TaskStep], operator.add]
    latest_raw_output: str

def initiate_state():
    new_annotations = dict(get_type_hints(BaseAgentState))
    for registry in st.session_state.agent_registry.values():
        requirements = registry.get("requirements", [])
        if requirements:
            for req in requirements:
                key = req.get("key")
                type = req.get("type")
                if key and type:
                    new_annotations[key] = type
    DynamicState = TypedDict("AgentState", new_annotations)
    return DynamicState

def get_initial_state():
    return {
        "curr_seq": 0,
        "task_seq": {task_name: 0 for task_name in st.session_state.agent_registry.keys()},
        "curr_agent": "",
        "prev_agent": "",
        "task_history": [],
        "latest_raw_output": ""
    }

# 2. Agent 작업 함수 정의 
def call_task(task_name, state) -> dict:
    # 1) 설정 불러오기
    config = st.session_state.agent_registry[task_name]

    # 2) 프롬프트 준비
    prompt = ChatPromptTemplate.from_messages([
        ("system", config["system_prompt"]),
        ("human", config["human_prompt"])
    ])

    # 3) 파서 및 체인 연결
    if config.get("schema"):
        parser = PydanticOutputParser(pydantic_object=config["schema"])
        prompt = prompt.partial(format=parser.get_format_instructions())
        chain = prompt | llm | parser
    else:
        chain = prompt | llm

    # 4) LLM 실행
    result = chain.invoke(state)

    # 5) 결과물 조합
    updates = {}
    if config.get("schema"):
        updates.update(result.model_dump())
    elif config.get("output_mapping"):
        updates[config["output_mapping"]] = result

    if "action" in config:
        action_updates = config["action"](state)
        updates.update(action_updates)

    updates["prev_agent"] = state["curr_agent"]
    updates["curr_agent"] = task_name
    updates.update(config.get("static_returns", {}))

    return updates


# 3. 그래프 빌드 함수
def build_langgraph(graph):

    # 1. 그래프 초기화
    AgentState = initiate_state()
    workflow = StateGraph(AgentState)
    
    # 2. 노드 추가
    for node_name in graph["nodes"]:
        # 각 노드가 실행될 때 자신의 이름을 call_task에 전달하도록 람다/부분함수 구성
        workflow.add_node(node_name, lambda state, name=node_name: call_task(name, state))

    # 3. 일반 엣지 추가
    for start, end in graph["normal_edges"]:
        start = START if start == "__START__" else start
        target = END if end == "__END__" else end
        workflow.add_edge(start, target)
        if start == START:
            st.session_state.start_task = target

    # 4. 조건부 엣지 추가
    cond_map = defaultdict(lambda: defaultdict(dict))
    for start, cond, val, end in graph["cond_edges"]:
        target = END if end == "__END__" else end
        cond_map[start][cond][val] = target

    for start_node, cond_dict in cond_map.items():
        for cond, path_map in cond_dict.items():
            workflow.add_conditional_edges(
                start_node, 
                lambda state, c=cond, p=path_map: state.get(c, list(p.keys())[0]), 
                path_map
            )

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)