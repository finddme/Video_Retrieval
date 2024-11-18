import argparse
import six, os, torch
from app.app import app
import asyncio

async def main(args):
    await app(args)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--llm', type=str, default='together', 
                        choices=["openai","groq","claude","together"], required=False)
    parser.add_argument('--db-sync', type=str, default=False,choices=[True,False], required=False)
    parser.add_argument('--main-class-name', type=str, default='retrieval', required=False)

    args = parser.parse_args()

    asyncio.run(main(args))




    
