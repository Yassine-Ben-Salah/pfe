"""
agent.py — True ReAct agent using LangGraph + Groq tool calling
"""

import json
import os
import numpy as np
from typing import TypedDict, Optional, Annotated
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from search import search_hybrid, normalize

load_dotenv(dotenv_path="D:/projects/extraction/.env")

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatGroq(
    api_key=os.environ["GROQ_API_KEY"],
    model="llama-3.3-70b-versatile",
    temperature=0,
)

# ── State ─────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    report: Optional[dict]

# ── Severity keywords ─────────────────────────────────────────────────────────
SEVERITY_KEYWORDS = {
    "major":    ["chassis", "moteur", "airbag", "capot", "carrosserie", "epave"],
    "moderate": ["aile", "porte", "pare choc", "pare-choc", "parechoc",
                 "phare", "vitre", "coffre", "optique"],
    "minor":    ["rayure", "bosse", "retroviseur", "enjoliveur", "poignee"],
}

SEVERITY_MULTIPLIER = {"minor": 0.6, "moderate": 1.0, "major": 1.5}

# ── Tools ─────────────────────────────────────────────────────────────────────
@tool
def search_damage_tool(marque: str, damage_query: str, top_k: int = 5) -> str:
    """
    Search the rapport index for similar past repair cases.
    Use this to find cases with similar vehicle brand and damage description.
    Returns a list of similar cases with their repair costs.
    """
    results = search_hybrid(
        marque=marque if marque else None,
        damage_query=damage_query if damage_query else None,
        top_k=top_k,
    )
    simplified = [
        {
            "filename":  r.get("filename"),
            "marque":    r.get("marque"),
            "damage":    r.get("damage_text"),
            "total_ttc": r.get("total_ttc"),
            "total_ht":  r.get("total_ht"),
            "score":     r.get("score"),
        }
        for r in results
    ]
    return json.dumps(simplified, ensure_ascii=False)


@tool
def assess_severity_tool(damage_text: str) -> str:
    """
    Assess the severity of vehicle damage based on damage description.
    Returns severity level (minor/moderate/major) and matched keywords.
    """
    combined = normalize(damage_text)
    matched = []
    severity = "minor"

    for level in ["major", "moderate", "minor"]:
        for kw in SEVERITY_KEYWORDS[level]:
            if normalize(kw) in combined:
                matched.append(kw)
                if level == "major":
                    severity = "major"
                elif level == "moderate" and severity != "major":
                    severity = "moderate"

    return json.dumps({
        "severity": severity,
        "matched_keywords": matched,
    })


@tool
def estimate_cost_tool(search_results_json: str, severity: str) -> str:
    """
    Estimate repair cost range based on similar past cases and severity.
    Pass the search results as JSON string and severity level.
    Returns cost_min, cost_max, cost_median in DT.
    """
    try:
        results = json.loads(search_results_json)
    except Exception:
        return json.dumps({"error": "Invalid search_results_json"})

    prices = []
    basis = []
    for r in results:
        ttc = r.get("total_ttc") or r.get("total_ht")
        if ttc:
            try:
                clean = (
                    str(ttc)
                    .replace("\xa0", "")
                    .replace("\u202f", "")
                    .replace("DT", "")
                    .replace(" ", "")
                    .strip()
                )

                # Handle European format: 1.179,100 → 1179.100
                if "," in clean and "." in clean:
                    # dot = thousands separator, comma = decimal
                    clean = clean.replace(".", "").replace(",", ".")
                elif "," in clean:
                    # comma = decimal
                    clean = clean.replace(",", ".")
                # else: already standard float format

                val = float(clean)
                if val > 0:
                    prices.append(val)
                    basis.append({"filename": r.get("filename"), "total_ttc": val})
            except ValueError:
                continue

    if not prices:
        return json.dumps({"error": "No valid prices found in search results"})

    arr = np.array(prices)
    if len(arr) >= 4:
        q1, q3 = np.percentile(arr, 25), np.percentile(arr, 75)
        iqr = q3 - q1
        arr = arr[(arr >= q1 - 1.5 * iqr) & (arr <= q3 + 1.5 * iqr)]

    if len(arr) == 0:
        return json.dumps({"error": "All prices filtered as outliers"})

    multiplier = SEVERITY_MULTIPLIER.get(severity, 1.0)

    return json.dumps({
        "cost_min":    round(float(arr.min())      * multiplier, 2),
        "cost_max":    round(float(arr.max())      * multiplier, 2),
        "cost_median": round(float(np.median(arr)) * multiplier, 2),
        "basis":       basis,
    })


@tool
def finalize_report_tool(
    vehicule_a: str,
    vehicule_b: str,
    severity: str,
    matched_keywords: str,
    cost_min: float,
    cost_max: float,
    cost_median: float,
    similar_cases: str,
) -> str:
    """
    Finalize and structure the claim report. Call this when you have
    collected all necessary information (severity + cost estimate).
    All vehicle info as JSON strings.
    """
    try:
        va = json.loads(vehicule_a)
    except Exception:
        va = {}
    try:
        vb = json.loads(vehicule_b)
    except Exception:
        vb = {}
    try:
        cases = json.loads(similar_cases)
    except Exception:
        cases = []
    try:
        keywords = json.loads(matched_keywords)
    except Exception:
        keywords = []

    return json.dumps({
        "vehicule_a":       va,
        "vehicule_b":       vb,
        "severity":         severity,
        "matched_keywords": keywords,
        "cost_min":         cost_min,
        "cost_max":         cost_max,
        "cost_median":      cost_median,
        "similar_cases":    cases,
    }, ensure_ascii=False)


# ── Bind tools to LLM ─────────────────────────────────────────────────────────
tools = [
    search_damage_tool,
    assess_severity_tool,
    estimate_cost_tool,
    finalize_report_tool,
]
llm_with_tools = llm.bind_tools(tools)


# ── Nodes ─────────────────────────────────────────────────────────────────────
def agent_node(state: AgentState) -> AgentState:
    """LLM decides what to do next."""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response], "report": state.get("report")}


def tool_node_fn(state: AgentState) -> AgentState:
    """Execute whatever tool the LLM called."""
    tool_node = ToolNode(tools)
    result = tool_node.invoke(state)

    # Check if finalize_report was called — extract the report
    report = state.get("report")
    for msg in result.get("messages", []):
        if hasattr(msg, "content") and msg.content:
            try:
                parsed = json.loads(msg.content)
                if "severity" in parsed and "cost_median" in parsed:
                    report = parsed
            except Exception:
                pass

    return {"messages": result["messages"], "report": report}


def should_continue(state: AgentState) -> str:
    """Route: if LLM called a tool → run it. If done → end."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


# ── Build Graph ────────────────────────────────────────────────────────────────
def build_claim_graph():
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node_fn)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


claim_graph = build_claim_graph()


# ── Entry point ───────────────────────────────────────────────────────────────
def run_claim_analysis(full_text: str) -> dict:
    system = SystemMessage(content="""You are an insurance claim analyst for a Tunisian auto insurance company (Comar).

You have access to these tools:
- search_damage_tool: search past repair cases by vehicle brand and damage
- assess_severity_tool: assess damage severity from damage description
- estimate_cost_tool: estimate repair cost from search results
- finalize_report_tool: produce the final structured report

Your workflow:
1. Extract vehicle and damage info from the constat text
2. Call assess_severity_tool on the damage description
3. Call search_damage_tool to find similar past cases
4. If fewer than 2 results, retry search with broader terms (damage only, no marque)
5. Call estimate_cost_tool with the search results and severity
6. Call finalize_report_tool with everything you gathered

Always complete all steps before finalizing. Be thorough.""")

    human = HumanMessage(content=f"""Analyze this insurance constat and produce a cost estimate report:

{full_text}""")

    result = claim_graph.invoke({
        "messages": [system, human],
        "report": None,
    })


    return result.get("report") or {"error": "Agent did not produce a report"}