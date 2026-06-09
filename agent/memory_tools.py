from langchain_core.tools import StructuredTool

from db import firestore as db


def create_memory_tools(uid: str) -> list:
    def save_user_memory(fact: str) -> str:
        """Save a durable fact about the user for future chats (name, preferences, role, etc.)."""
        facts = db.add_user_memory_fact(uid, fact)
        return "Saved for future chats. Known facts: " + "; ".join(facts)

    return [
        StructuredTool.from_function(
            func=save_user_memory,
            name="save_user_memory",
            description=(
                "Persist a fact about the user across all chat sessions. "
                "Use when they share their name, how to address them, preferences, "
                "or other information they would expect you to remember later."
            ),
        )
    ]
