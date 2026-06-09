# agent

LangGraph ReAct agent powered by OpenAI + Composio tools.

| File | Purpose |
|---|---|
| `state.py` | `AgentState` schema (`messages` with `add_messages` reducer) |
| `tools.py` | Composio Gmail + Google Drive tools (per Firebase `uid`) |
| `graph.py` | `StateGraph`: agent → `tools_condition` → ToolNode loop, `MemorySaver`, streaming |
| `message_trim.py` | Truncate tool output + cap history before LLM calls |

## Graph flow

```
START → agent → tools_condition
                  ├─ tools → ToolNode (Composio) → agent
                  └─ END → stream tokens to client
```

- **Memory**: `MemorySaver` checkpointer, `thread_id = {uid}:{session_id}`
- **Persistence**: Firestore seeds checkpoint on server restart
- **Streaming**: `app.astream(..., stream_mode=["messages", "updates"])`

Model: `OPENAI_MODEL` env var (default: `gpt-5`).
