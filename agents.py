# agents.py
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import GoogleGenerativeAI
llm = GoogleGenerativeAI(model="gemini-2.5-flash")
# ===========================================================

from typing import TypedDict, Annotated
import operator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver # 🌟 기억 저장소 추가


# 1. State 정의 (리스트로 대화 기록을 누적합니다)
class MeetingState(TypedDict):
    topic: str
    context: str
    draft: str
    chat_history: Annotated[list, operator.add] # 오고 간 의견을 누적
    human_feedback: str # 사람이 중간에 찔러넣을 피드백

# 2. 노드 정의
def red_team_critics(state: MeetingState):
    """두 비판자가 동시에(또는 순차적으로) 의견을 내는 노드"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 무자비한 레드팀입니다.
        현재까지의 회의 기록을 보고, 논리적 허점이나 맥락(Context)을 벗어난 부분을 날카롭게 비판하세요.
        특히 [사용자의 추가 피드백]이 있다면 그 방향성에 맞춰 비판을 수정하세요."""),
        ("human", """
        [회의 주제]: {topic}
        [맥락]: {context}
        [초안]: {draft}
        [사용자의 최근 피드백]: {human_feedback}
        [이전 회의 기록]: {history}
        """)
    ])
    
    history_text = "\n".join(state.get("chat_history", ["최초"]))
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({
        "topic": state["topic"],
        "context": state["context"],
        "draft": state["draft"],
        "human_feedback": state.get("human_feedback", "없음"),
        "history": history_text
    })
    
    return {"chat_history": [f"🤖 레드팀: {result}"]}

def human_intervention(state: MeetingState):
    """
    이 노드는 아무 동작도 하지 않는 '더미 노드'입니다.
    이 노드 '직전'에 일시정지(interrupt)를 걸어 사람의 입력을 기다릴 것입니다.
    """
    return {}

def moderator(state: MeetingState):
    """회의 종료를 선언하고 요약하는 노드"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 조율자입니다. 기나긴 회의 기록을 요약하고 최종 결론을 내리세요."),
        ("human", "기록: {history}")
    ])
    chain = prompt | llm | StrOutputParser()
    history_text = "\n".join(state.get("chat_history", []))
    result = chain.invoke({"history": history_text})
    
    return {"chat_history": [f"👨‍⚖️ 조율자 최종 결론:\n{result}"]}

# 3. 라우팅 (계속 토론할지, 종료할지 결정)
def route_after_human(state: MeetingState):
    feedback = state.get("human_feedback", "")
    if "종료" in feedback or "그만" in feedback:
        return "moderator"
    return "red_team_critics"

# 4. 그래프 조립 및 컴파일
def build_streaming_graph():
    workflow = StateGraph(MeetingState)
    
    workflow.add_node("red_team_critics", red_team_critics)
    workflow.add_node("human_intervention", human_intervention)
    workflow.add_node("moderator", moderator)
    
    workflow.set_entry_point("red_team_critics")

    workflow.add_edge("red_team_critics", "human_intervention")
    
    # 사람 개입 후 피드백 내용에 따라 다시 토론시킬지 종료할지 분기
    workflow.add_conditional_edges("human_intervention", route_after_human)
    workflow.add_edge("moderator", END)
    
    # 🌟 핵심: 메모리를 달아주고, human_intervention 직전에 멈추도록 설정
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory, interrupt_before=["human_intervention"])
    return app