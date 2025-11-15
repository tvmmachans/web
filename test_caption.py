import asyncio
import sys
sys.path.append('.')
from backend.services.ai_service import generate_caption_service

async def test():
    result = await generate_caption_service('test text')
    print(f'Caption result: {result}')

if __name__ == "__main__":
    asyncio.run(test())
