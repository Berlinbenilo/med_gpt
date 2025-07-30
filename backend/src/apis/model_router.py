from fastapi import APIRouter

router = APIRouter(tags=["Models"])

@router.get("/models")
async def get_models():
    return {
        "object": "list",
        "data": [
            {
                'id': 'deepseek-r1-0528', 
                'name': 'DeepSeek R1 (Latest)',
                'description': 'Advanced reasoning model with excellent performance',
                'owned_by': 'deepseek',
                'created': 1705539600
            },
            {
                'id': 'gpt-4.1', 
                'name': 'GPT-4.1',
                'description': 'Latest GPT-4 model with enhanced capabilities',
                'owned_by': 'openai',
                'created': 1705539600
            },
            {
                'id': 'llama4-maverick-instruct-basic', 
                'name': 'Llama 4 Maverick',
                'description': 'Meta\'s latest instruction-tuned model',
                'owned_by': 'meta',
                'created': 1705539600
            },
            {
                'id': 'gemini-2.5-pro',
                'name': 'Gemini 2.5 Pro',
                'description': 'Google\'s advanced multimodal AI model',
                'owned_by': 'google',
                'created': 1705539600
            },
        ]
    }
