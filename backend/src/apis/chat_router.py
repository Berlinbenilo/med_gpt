import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from backend.src.constants.config import vector_store
from backend.src.entities.api_model import Chat
from backend.src.graphs.med_tutor import MedTutor
from backend.src.services.chat_service import ChatService

router = APIRouter(tags=["Chat"])


@router.post("/chat")
async def chat(item: Chat):
    print("Invoke get triggered..!")

    # Ensure session exists
    session = ChatService.get_session(item.session_id)
    message_count = 0
    if not session:
        session = ChatService.create_session(
            user_id=item.user_id,
            session_id=item.session_id,
            model_config=item.config
        )
        message_count = 1
        print(f"Created new session: {item.session_id}")

    # Store user message
    user_message = ChatService.add_message(
        session_id=item.session_id,
        role="user",
        content=item.input_query
    )

    if message_count == 1:
        title = ChatService.generate_session_title(item.input_query)
        ChatService.update_session_title(item.session_id, title)

    state = {
        "user_id": item.user_id,
        "messages": [HumanMessage(content=item.input_query)],
        "model_config": item.config,
        "remaining_steps": 5
    }

    try:
        graph = MedTutor(collection=vector_store, model_config=item.config, session=item.session_id)
        response = await graph.arun(input_payload=state,
                                    config={"configurable": {"thread_id": item.session_id}},
                                    memory=MemorySaver()
                                    )

        # Store assistant message
        ChatService.add_message(
            session_id=item.session_id,
            role="assistant",
            content=response.content,
            node_type="final_response",  # Since this is the final response
            metadata={"model_config": item.config}
        )

        return {"message": response.content, "status": True}

    except Exception as e:
        print(f"Chat error: {e}")
        # Store error message
        error_content = "Sorry, I encountered an error processing your request. Please try again."
        ChatService.add_message(
            session_id=item.session_id,
            role="assistant",
            content=error_content,
            node_type="error",
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(item: Chat):
    print("streaming get triggered...!")

    # Ensure session exists
    session = ChatService.get_session(item.session_id)
    message_count = 0
    if not session:
        session = ChatService.create_session(
            user_id=item.user_id,
            session_id=item.session_id,
            model_config=item.config
        )
        message_count = 1
        print(f"Created new session: {item.session_id}")

    # Store user message
    user_message = ChatService.add_message(
        session_id=item.session_id,
        role="user",
        content=item.input_query
    )

    # Update session title if this is the first user message
    if message_count == 1:
        title = ChatService.generate_session_title(item.input_query)
        ChatService.update_session_title(item.session_id, title)

    state = {
        "user_id": item.user_id,
        "messages": [HumanMessage(content=item.input_query)],
        "model_config": item.config,
        "remaining_steps": 5
    }
    graph = MedTutor(collection=vector_store, model_config=item.config, session=item.session_id)

    async def event_generator():
        accumulated_response = ""
        current_node_type = None

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

                    # Extract the actual node name
                    if ":" in node_name:
                        current_node_type = node_name.split(":")[0]

                    # Only stream if this is from a final response node
                    if current_node_type in final_nodes:
                        token = event["data"].get("chunk", {}).content
                        if token:
                            accumulated_response += token
                            # Simple format that's easier to parse
                            data = {"content": token}
                            yield f"data: {json.dumps(data)}\n\n"

            # Store the complete assistant response
            if accumulated_response:
                ChatService.add_message(
                    session_id=item.session_id,
                    role="assistant",
                    content=accumulated_response,
                    node_type=current_node_type or "unknown",
                    metadata={"model_config": item.config, "streaming": True}
                )

            # Send completion signal
            yield "data: {\"done\": true}\n\n"

        except Exception as e:
            print(f"Streaming error: {e}")
            # Store error message
            error_content = "Sorry, I encountered an error processing your request. Please try again."
            ChatService.add_message(
                session_id=item.session_id,
                role="assistant",
                content=error_content,
                node_type="error",
                metadata={"error": str(e), "streaming": True}
            )
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
