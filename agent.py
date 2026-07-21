"""
BI Agent — Groq-powered analyst
Uses groq SDK with llama-3.3-70b-versatile.
Routes queries to pipeline/work-order/cross-board analysis
and narrates results via Groq.
"""

import os
import json
import re
import pandas as pd
import streamlit as st
from groq import Groq
from typing import Optional
from data_cleaner import (
    build_work_orders_df, build_deals_df,
    format_currency, data_quality_report
)
from monday_client import get_work_orders, get_deals


# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a sharp, concise Business Intelligence analyst for a drone/survey services company.
You have access to real Monday.com data from two boards: Work Orders (project execution) and Deals (Deal Funnel / sales pipeline).

Key context:
- All monetary values are in Indian Rupees (Rs.). Use Rs. symbol, format as Lakhs (Rs.2.5L) or Crores (Rs.1.2Cr).
- Work Orders track project execution: customer codes, sectors (Mining, Renewables, etc.), execution status, billing.
- Deals track sales pipeline: deal owner, company, status, sector, priority, value.
- Customer/owner fields are anonymized codes (e.g. WOCOMPANY_002, OWNER_001).

Your personality:
- Speak like a senior analyst briefing a founder — direct, insightful, no fluff
- Always lead with the KEY number or insight, then explain
- Flag data quality issues honestly but briefly (one line max)
- Format numbers cleanly: Rs.2.5L not 250000

When answering:
1. Give the direct answer FIRST
2. Add 2-3 supporting data points
3. Note any caveats about data quality
4. End with one actionable insight if relevant

If you don't have enough data, say so clearly and suggest what to check.
Never make up numbers. Only use data from the tool results."""


# ─── Groq Client Factory ──────────────────────────────────────────────────────

def get_groq_key() -> str:
    """Read GROQ_API_KEY from secrets.toml directly — always works inside Streamlit."""
    try:
        key = st.secrets["GROQ_API_KEY"]
        if key:
            return key
    except Exception:
        pass
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        raise ValueError("GROQ_API_KEY is missing. Add it to .streamlit/secrets.toml")
    return key

def get_client(api_key: str = None) -> Groq:
    if not api_key:
        api_key = get_groq_key()
    return Groq(api_key=api_key)


# ─── Analysis Functions ───────────────────────────────────────────────────────

def analyze_pipeline(deals_df: pd.DataFrame, filters: dict = None) -> dict:
    """Aggregate pipeline metrics from deals data with optional filters."""
    if deals_df.empty:
        return {"error": "No deals data available"}

    df = deals_df.copy()
    if filters:
        if filters.get("sector"):
            df = df[df["sector"].str.contains(filters["sector"], case=False, na=False)]
        if filters.get("status"):
            df = df[df["status"].str.contains(filters["status"], case=False, na=False)]
        if filters.get("quarter"):
            df = df[df["quarter"] == filters["quarter"]]
        if filters.get("owner"):
            df = df[df["owner"].str.contains(filters["owner"], case=False, na=False)]

    total_deals = len(df)
    open_deals  = df[df["status"].isin(["Open", "In Progress", "Pending", "New"])]
    won_deals   = df[df["status"] == "Won"]
    lost_deals  = df[df["status"] == "Lost"]

    total_value = df["value"].sum()
    open_value  = open_deals["value"].sum()
    won_value   = won_deals["value"].sum()
    win_rate    = (len(won_deals) / total_deals * 100) if total_deals > 0 else 0
    avg_deal    = df["value"].mean() if not df["value"].isna().all() else None

    def safe_records(grp, sort_col="total_value"):
        return (
            grp.reset_index()
               .sort_values(sort_col, ascending=False)
               .head(10)
               .to_dict("records")
        )

    by_status = df.groupby("status").agg(count=("name","count"), total_value=("value","sum"))
    by_sector = df.groupby("sector").agg(count=("name","count"), total_value=("value","sum"))
    by_owner  = df.groupby("owner").agg(count=("name","count"),  total_value=("value","sum"))

    return {
        "summary": {
            "total_deals":          total_deals,
            "open_deals":           len(open_deals),
            "won_deals":            len(won_deals),
            "lost_deals":           len(lost_deals),
            "win_rate_pct":         round(win_rate, 1),
            "total_pipeline_value": round(float(total_value) if pd.notna(total_value) else 0, 2),
            "open_pipeline_value":  round(float(open_value)  if pd.notna(open_value)  else 0, 2),
            "won_revenue":          round(float(won_value)   if pd.notna(won_value)   else 0, 2),
            "avg_deal_size":        round(float(avg_deal), 2) if avg_deal and pd.notna(avg_deal) else None,
            "filters_applied":      filters or "none",
        },
        "by_status": safe_records(by_status),
        "by_sector": safe_records(by_sector),
        "by_owner":  safe_records(by_owner),
        "data_quality": {
            "missing_values": int(df["value"].isna().sum()),
            "missing_dates":  int(df["close_date"].isna().sum() if "close_date" in df else 0),
            "total_records":  total_deals,
        }
    }


def analyze_work_orders(wo_df: pd.DataFrame, filters: dict = None) -> dict:
    """Aggregate work-order execution metrics with optional filters."""
    if wo_df.empty:
        return {"error": "No work orders data available"}

    df = wo_df.copy()
    if filters:
        if filters.get("sector"):
            df = df[df["sector"].str.contains(filters["sector"], case=False, na=False)]
        if filters.get("status"):
            df = df[df["status"].str.contains(filters["status"], case=False, na=False)]
        if filters.get("quarter"):
            df = df[df["quarter"] == filters["quarter"]]
        if filters.get("customer"):
            df = df[df["customer"].str.contains(filters["customer"], case=False, na=False)]

    total_value   = df["value"].sum()
    avg_value     = df["value"].mean() if not df["value"].isna().all() else None

    by_status     = df.groupby("status").agg(count=("name","count"), total_value=("value","sum"))
    by_sector     = df.groupby("sector").agg(count=("name","count"), total_value=("value","sum"))
    top_customers = df.groupby("customer").agg(orders=("name","count"), total_value=("value","sum"))

    def safe_records(grp, sort_col="total_value"):
        return grp.reset_index().sort_values(sort_col, ascending=False).head(10).to_dict("records")

    return {
        "summary": {
            "total_work_orders": len(df),
            "total_value":       round(float(total_value) if pd.notna(total_value) else 0, 2),
            "avg_value":         round(float(avg_value), 2) if avg_value and pd.notna(avg_value) else None,
            "filters_applied":   filters or "none",
        },
        "by_status":     safe_records(by_status),
        "by_sector":     safe_records(by_sector),
        "top_customers": safe_records(top_customers, "total_value"),
        "data_quality":  {"missing_values": int(df["value"].isna().sum()), "total_records": len(df)},
    }


def cross_board_analysis(wo_df: pd.DataFrame, deals_df: pd.DataFrame, filters: dict = None) -> dict:
    """Combined pipeline + execution overview."""
    pipeline  = analyze_pipeline(deals_df, filters)
    execution = analyze_work_orders(wo_df, filters)
    return {
        "pipeline":          pipeline.get("summary", {}),
        "execution":         execution.get("summary", {}),
        "combined_value":    (
            pipeline.get("summary",  {}).get("total_pipeline_value", 0) +
            execution.get("summary", {}).get("total_value", 0)
        ),
        "pipeline_by_sector":  pipeline.get("by_sector",  []),
        "execution_by_sector": execution.get("by_sector", []),
    }


# ─── Agent Class ──────────────────────────────────────────────────────────────

class BIAgent:
    def __init__(self, wo_board_id: str, deals_board_id: str):
        self.wo_board_id    = wo_board_id
        self.deals_board_id = deals_board_id
        self._wo_df    = None
        self._deals_df = None
        # Read the key once at init time so it's always available
        self._groq_key  = get_groq_key()

    # ── data loading ──

    def load_data(self):
        wo_raw     = get_work_orders(self.wo_board_id)
        deals_raw  = get_deals(self.deals_board_id)
        self._wo_df    = build_work_orders_df(wo_raw)
        self._deals_df = build_deals_df(deals_raw)
        return self._wo_df, self._deals_df

    @property
    def wo_df(self) -> pd.DataFrame:
        if self._wo_df is None:
            self.load_data()
        return self._wo_df

    @property
    def deals_df(self) -> pd.DataFrame:
        if self._deals_df is None:
            self.load_data()
        return self._deals_df

    # ── helpers ──

    def _extract_filters(self, query: str) -> dict:
        filters = {}
        q = query.lower()
        sectors = ["energy","technology","tech","finance","healthcare",
                   "manufacturing","retail","construction","telecom","education","logistics"]
        for s in sectors:
            if s in q:
                filters["sector"] = s
                break

        m = re.search(r"q([1-4])\s*(\d{4})?", q)
        if m:
            filters["quarter"] = f"Q{m.group(1)} {m.group(2) or '2024'}"

        status_map = {"open":"Open","won":"Won","lost":"Lost","closed":"Closed",
                      "pending":"Pending","on hold":"On Hold","in progress":"In Progress"}
        for kw, val in status_map.items():
            if kw in q:
                filters["status"] = val
                break
        return filters

    def _detect_query_type(self, query: str) -> str:
        q = query.lower()
        pipe_score = sum(1 for kw in ["pipeline","deal","funnel","sales","revenue","win rate","close","prospect"] if kw in q)
        wo_score   = sum(1 for kw in ["work order","project","execution","delivery","customer","work"] if kw in q)
        cross_score= sum(1 for kw in ["overview","overall","business","both","all","health","summary","report","brief"] if kw in q)
        if cross_score > 0 or (pipe_score > 0 and wo_score > 0):
            return "cross"
        return "pipeline" if pipe_score >= wo_score else "work_orders"

    # ── main chat ──

    def chat(self, query: str, history: list[dict]) -> str:
        try:
            filters    = self._extract_filters(query)
            query_type = self._detect_query_type(query)

            if query_type == "pipeline":
                data    = analyze_pipeline(self.deals_df, filters)
                context = f"PIPELINE ANALYSIS:\n{json.dumps(data, indent=2, default=str)}"
            elif query_type == "work_orders":
                data    = analyze_work_orders(self.wo_df, filters)
                context = f"WORK ORDERS ANALYSIS:\n{json.dumps(data, indent=2, default=str)}"
            else:
                data    = cross_board_analysis(self.wo_df, self.deals_df, filters)
                context = f"CROSS-BOARD ANALYSIS:\n{json.dumps(data, indent=2, default=str)}"

            quality = data_quality_report(self.wo_df, self.deals_df)
            quality_note = f"\nDATA QUALITY:\n{json.dumps(quality, indent=2, default=str)}"

            # Build messages list for Groq
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

            full_query = (
                f"User question: {query}\n\n"
                f"Relevant Monday.com data:\n{context}\n{quality_note}\n\n"
                f"Answer directly and insightfully."
            )
            messages.append({"role": "user", "content": full_query})

            client   = get_client(self._groq_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )
            return response.choices[0].message.content

        except Exception as e:
            return f"Error: {str(e)}"

    # ── leadership brief ──

    def generate_leadership_brief(self) -> str:
        try:
            data      = cross_board_analysis(self.wo_df, self.deals_df)
            pipeline  = analyze_pipeline(self.deals_df)
            execution = analyze_work_orders(self.wo_df)

            prompt = (
                "Generate a concise, professional leadership update brief (board meeting / investor update).\n"
                "Format:\n"
                "1. Executive Summary (2-3 sentences)\n"
                "2. Pipeline Health (key metrics)\n"
                "3. Execution Status (work orders)\n"
                "4. Top Opportunities / Risks (bullet points)\n"
                "5. Recommended Actions (2-3 bullets)\n\n"
                f"Data:\nCROSS-BOARD: {json.dumps(data, indent=2, default=str)}\n"
                f"PIPELINE: {json.dumps(pipeline, indent=2, default=str)}\n"
                f"EXECUTION: {json.dumps(execution, indent=2, default=str)}\n\n"
                "Be concise, leadership-ready, and data-backed."
            )

            client   = get_client(self._groq_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
            )
            return response.choices[0].message.content

        except Exception as e:
            return f"Could not generate brief: {str(e)}"
