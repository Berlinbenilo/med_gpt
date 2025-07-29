import json
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from fastapi.responses import StreamingResponse

from backend.src.constants.config import vector_store
from backend.src.entities.api_model import Chat
from backend.src.graphs.med_tutor import MedTutor

router = APIRouter(tags=["Chat"])


@router.post("/chat")
async def chat(item: Chat):
    print("Invoke get triggered..!")
    state = {
        "user_id": item.user_id,
        "messages": [HumanMessage(content=item.input_query)],
        "model_config": item.config,
        "remaining_steps": 5
    }
    graph = MedTutor(collection=vector_store, model_config=item.config, session=item.session_id)
    response = await graph.arun(input_payload=state,
                                config={"configurable": {"thread_id": item.session_id}},
                                memory=MemorySaver()
                                )
    return {"message": response.content, "status": True}

@router.post("/chat/stream")
async def chat_stream(item: Chat):
    print("streaming get triggered...!")
    state = {
        "user_id": item.user_id,
        "messages": [HumanMessage(content=item.input_query)],
        "model_config": item.config,
        "remaining_steps": 5
    }
    graph = MedTutor(collection=vector_store, model_config=item.config, session=item.session_id)
    
    async def event_generator():
        try:
            memory = MemorySaver()
            
            # Define the final nodes that should stream their responses
            final_nodes = {"short_answer", "unstructured_search", "case_studies"}
            
            # Stream the actual content
            async for event in graph.astream(input_payload=state,
                                             config={"configurable": {"thread_id": item.session_id}},
                                             memory=memory):
                # Only stream from final response nodes
                if event["event"] == "on_chat_model_stream":
                    # Check if the event is from one of the final nodes
                    event_metadata = event.get('metadata', {})
                    node_name = event_metadata.get('langgraph_checkpoint_ns', '')
                    
                    # print(f"Node name: {node_name}")  # Debug log
                    #
                    # Only stream if this is from a final response node
                    if node_name.split(":")[0] in final_nodes:
                        token = event["data"].get("chunk", {}).content
                        if token:
                            # Simple format that's easier to parse
                            data = {"content": token}
                            yield f"data: {json.dumps(data)}\n\n"
            
            # Send completion signal
            yield "data: {\"done\": true}\n\n"
            
        except Exception as e:
            print(f"Streaming error: {e}")
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )
