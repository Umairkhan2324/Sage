import os
import streamlit as st
from langchain_groq import ChatGroq
from typing import List, Dict, TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import START, END, StateGraph
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.document_loaders import WikipediaLoader
import json

# Initialize LLM and search tools
llm = ChatGroq(model="llama-3.1-70b-versatile", max_tokens=26420, temperature=0.1)
tavily_search = TavilySearchResults(max_results=3)

# Define data models
class Analyst(BaseModel):
    name: str = Field(description="Name of the analyst.")
    role: str = Field(description="Role of the analyst in the context of the topic.")
    affiliation: str = Field(description="Primary affiliation of the analyst.")

class ResearchState(TypedDict):
    topic: str
    analysts: List[Dict]
    current_analyst_index: int
    sections: List[str]
    content: str
    introduction: str
    conclusion: str
    final_report: str

# Define graph nodes
def create_analysts(state: ResearchState) -> Dict:
    topic = state['topic']
    system_message = f"""Create 3 diverse AI analyst personas for the topic: {topic}.
    Output in JSON format with a single key 'analysts' containing an array of objects, each with fields: name, role, affiliation."""
    analysts_response = llm.invoke([SystemMessage(content=system_message)])
    
    try:
        analysts_data = json.loads(analysts_response.content)
        analysts = [Analyst(**analyst).dict() for analyst in analysts_data['analysts'][:3]]
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error parsing analysts: {e}")
        analysts = [
            Analyst(name="Default Analyst 1", role="General Researcher", affiliation="University").dict(),
            Analyst(name="Default Analyst 2", role="Industry Expert", affiliation="Tech Company").dict(),
            Analyst(name="Default Analyst 3", role="Policy Advisor", affiliation="Government Think Tank").dict()
        ]
    
    return {
        "analysts": analysts,
        "current_analyst_index": 0
    }

def conduct_interview(state: ResearchState) -> Dict:
    topic = state['topic']
    analyst = state['analysts'][state['current_analyst_index']]
    
    # Generate question
    system_message = f"You are {analyst['name']}, {analyst['role']}. Ask a question about {topic}."
    question = llm.invoke([SystemMessage(content=system_message)])
    
    # Search and answer
    search_query = llm.invoke([SystemMessage(content="Generate a search query based on the question."), HumanMessage(content=question.content)])
    search_docs = tavily_search.invoke(search_query.content)
    wiki_docs = WikipediaLoader(query=search_query.content, load_max_docs=1).load()
    
    # Handle different possible formats of search results
    search_contents = []
    for doc in search_docs:
        if isinstance(doc, dict):
            search_contents.append(doc.get('content', '') or doc.get('snippet', ''))
        elif isinstance(doc, str):
            search_contents.append(doc)
    
    wiki_contents = [doc.page_content for doc in wiki_docs]
    
    context = "\n".join(search_contents + wiki_contents)
    
    system_message = f"""You are an expert answering questions about {topic}.
    Use this context to answer: {context}"""
    answer = llm.invoke([SystemMessage(content=system_message), HumanMessage(content=question.content)])
    
    # Write section
    interview = f"Q: {question.content}\nA: {answer.content}"
    system_message = f"Summarize this interview about {topic} conducted by {analyst['name']}:"
    section = llm.invoke([SystemMessage(content=system_message), HumanMessage(content=interview)])
    
    return {
        "sections": state.get("sections", []) + [section.content],
        "current_analyst_index": state["current_analyst_index"] + 1
    }

def write_report(state: ResearchState) -> Dict:
    sections = state['sections']
    topic = state['topic']
    system_message = f"Write a comprehensive report on {topic} based on these sections: {sections}"
    report = llm.invoke([SystemMessage(content=system_message)])
    return {"content": report.content}

def write_intro_conclusion(state: ResearchState) -> Dict:
    content = state['content']
    topic = state['topic']
    system_message = f"""Write an introduction and conclusion for this report on {topic}. 
    Format your response as follows:
    Introduction:
    [Your introduction here]
    Conclusion:
    [Your conclusion here]"""
    intro_conclusion = llm.invoke([SystemMessage(content=system_message), HumanMessage(content=content)])
    
    # Split the response into introduction and conclusion
    parts = intro_conclusion.content.split("Conclusion:")
    if len(parts) == 2:
        intro = parts[0].replace("Introduction:", "").strip()
        conclusion = parts[1].strip()
    else:
        # If "Conclusion:" is not found, assume the first half is intro and the second half is conclusion
        mid_point = len(intro_conclusion.content) // 2
        intro = intro_conclusion.content[:mid_point].strip()
        conclusion = intro_conclusion.content[mid_point:].strip()
    
    return {
        "introduction": intro,
        "conclusion": conclusion
    }

def finalize_report(state: ResearchState) -> Dict:
    final_report = f"{state['introduction']}\n\n{state['content']}\n\n{state['conclusion']}"
    return {"final_report": final_report}

# Define graph
def build_research_graph():
    workflow = StateGraph(ResearchState)
    
    workflow.add_node("create_analysts", create_analysts)
    workflow.add_node("conduct_interview", conduct_interview)
    workflow.add_node("write_report", write_report)
    workflow.add_node("write_intro_conclusion", write_intro_conclusion)
    workflow.add_node("finalize_report", finalize_report)

    workflow.set_entry_point("create_analysts")
    
    workflow.add_edge("create_analysts", "conduct_interview")
    workflow.add_conditional_edges(
        "conduct_interview",
        lambda x: "conduct_interview" if x["current_analyst_index"] < len(x["analysts"]) else "write_report",
        {
            "conduct_interview": "conduct_interview",
            "write_report": "write_report"
        }
    )
    workflow.add_edge("write_report", "write_intro_conclusion")
    workflow.add_edge("write_intro_conclusion", "finalize_report")
    workflow.add_edge("finalize_report", END)

    return workflow.compile()

# Streamlit UI
st.title("SAGE")

topic = st.text_input("Enter a research topic:")

if st.button("Generate Report"):
    if topic:
        with st.spinner("Generating report..."):
            graph = build_research_graph()
            result = graph.invoke({
                "topic": topic,
                "analysts": [],
                "current_analyst_index": 0,
                "sections": [],
                "content": "",
                "introduction": "",
                "conclusion": "",
                "final_report": ""
            })
            st.markdown(result["final_report"])
    else:
        st.warning("Please enter a research topic.")
