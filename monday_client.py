"""
Monday.com API Client
Fetches all items from Work Orders and Deal Funnel boards via GraphQL.
Handles pagination, errors, and caching.
"""

import os
import time
import requests
import streamlit as st
from typing import Optional

MONDAY_API_URL = "https://api.monday.com/v2"

def get_headers():
    token = os.getenv("MONDAY_API_TOKEN") or st.secrets.get("MONDAY_API_TOKEN", "")
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "API-Version": "2024-01"
    }

def run_query(query: str, variables: dict = None) -> dict:
    """Execute a GraphQL query against Monday.com API."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        response = requests.post(
            MONDAY_API_URL,
            json=payload,
            headers=get_headers(),
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            raise ValueError(f"Monday API error: {data['errors']}")
        return data
    except requests.exceptions.Timeout:
        raise ConnectionError("Monday.com API timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Cannot connect to Monday.com. Check your internet connection.")
    except Exception as e:
        raise RuntimeError(f"Monday.com API call failed: {str(e)}")


def fetch_all_boards() -> list[dict]:
    """Fetch all boards to find Work Orders and Deal Funnel."""
    query = """
    query {
        boards(limit: 50) {
            id
            name
        }
    }
    """
    data = run_query(query)
    return data.get("data", {}).get("boards", [])


def fetch_board_items(board_id: str, limit: int = 500) -> list[dict]:
    """
    Fetch all items from a board with pagination.
    Returns a flat list of dicts with column values parsed.
    """
    all_items = []
    cursor = None

    while True:
        if cursor:
            query = """
            query ($board_id: ID!, $limit: Int!, $cursor: String!) {
                boards(ids: [$board_id]) {
                    items_page(limit: $limit, cursor: $cursor) {
                        cursor
                        items {
                            id
                            name
                            column_values {
                                id
                                column {
                                    title
                                }
                                text
                                value
                            }
                        }
                    }
                }
            }
            """
            variables = {"board_id": board_id, "limit": limit, "cursor": cursor}
        else:
            query = """
            query ($board_id: ID!, $limit: Int!) {
                boards(ids: [$board_id]) {
                    items_page(limit: $limit) {
                        cursor
                        items {
                            id
                            name
                            column_values {
                                id
                                column {
                                    title
                                }
                                text
                                value
                            }
                        }
                    }
                }
            }
            """
            variables = {"board_id": board_id, "limit": limit}

        data = run_query(query, variables)
        page = data.get("data", {}).get("boards", [{}])[0].get("items_page", {})
        items = page.get("items", [])
        cursor = page.get("cursor")

        for item in items:
            flat = {"item_name": item["name"], "item_id": item["id"]}
            for col in item.get("column_values", []):
                title = col.get("column", {}).get("title", col["id"])
                text_val = col.get("text") or ""
                flat[title] = text_val.strip() if text_val else None
            all_items.append(flat)

        if not cursor or len(items) < limit:
            break

    return all_items


@st.cache_data(ttl=300, show_spinner=False)  # Cache 5 minutes
def get_work_orders(board_id: str) -> list[dict]:
    """Fetch and cache Work Orders board."""
    return fetch_board_items(board_id)


@st.cache_data(ttl=300, show_spinner=False)  # Cache 5 minutes
def get_deals(board_id: str) -> list[dict]:
    """Fetch and cache Deals/Deal Funnel board."""
    return fetch_board_items(board_id)


def discover_board_ids() -> dict:
    """
    Auto-discover board IDs by name matching.
    Returns {"work_orders": id, "deals": id}
    """
    boards = fetch_all_boards()
    result = {"work_orders": None, "deals": None}

    work_order_keywords = ["work order", "workorder", "work_order", "projects", "project"]
    deal_keywords = ["deal", "funnel", "pipeline", "sales", "crm"]

    for board in boards:
        name_lower = board["name"].lower()
        if any(kw in name_lower for kw in work_order_keywords):
            result["work_orders"] = board["id"]
        elif any(kw in name_lower for kw in deal_keywords):
            result["deals"] = board["id"]

    return result
