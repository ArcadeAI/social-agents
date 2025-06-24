import asyncio
from datetime import datetime
from parser_agents.reddit.agent import get_content, InputSchema
from common.writers import write_documents_to_json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Getting content for MCP subreddit")

    today = datetime.now().strftime("%Y-%m-%d")
    subreddits_to_process = [
        InputSchema( subreddit="mcp", time_range="TODAY", limit=100, target_number=10, audience_specification="Deprioritize posts that are obviously marketing oriented, everyone is trying to sell something, we want developer-oriented content instead.",
            subreddit_description=open("./input_sources/reddit/mcp/subreddit_info.txt").read(),
        ),
        InputSchema( subreddit="modelcontextprotocol", time_range="TODAY", limit=100, target_number=10, audience_specification="Deprioritize posts that are obviously marketing oriented, everyone is trying to sell something, we want developer-oriented content instead.",
            subreddit_description=open("./input_sources/reddit/mcp/subreddit_info.txt").read(),
        ),
        InputSchema( subreddit="AgentsOfAI", time_range="TODAY", limit=100, target_number=10, audience_specification="Deprioritize posts that are obviously marketing oriented, everyone is trying to sell something, we want developer-oriented content instead.",
            subreddit_description=open("./input_sources/reddit/AgentsOfAI/subreddit_info.txt").read(),
        ),
        InputSchema( subreddit="Anthropic", time_range="TODAY", limit=100, target_number=10, audience_specification="Deprioritize posts that are obviously marketing oriented, everyone is trying to sell something, we want developer-oriented content instead.",
            subreddit_description=open("./input_sources/reddit/Anthropic/subreddit_info.txt").read(),
        ),
        InputSchema( subreddit="AI_Agents", time_range="TODAY", limit=100, target_number=10, audience_specification="Deprioritize posts that are obviously marketing oriented, everyone is trying to sell something, we want developer-oriented content instead.",
            subreddit_description=open("./input_sources/reddit/AI_Agents/subreddit_info.txt").read(),
        ),
        InputSchema( subreddit="aiagents", time_range="TODAY", limit=100, target_number=10, audience_specification="Deprioritize posts that are obviously marketing oriented, everyone is trying to sell something, we want developer-oriented content instead.",
            subreddit_description=open("./input_sources/reddit/aiagents/subreddit_info.txt").read(),
        ),
        InputSchema( subreddit="agentdevelopmentkit", time_range="TODAY", limit=100, target_number=10, audience_specification="Deprioritize posts that are obviously marketing oriented, everyone is trying to sell something, we want developer-oriented content instead.",
            subreddit_description=open("./input_sources/reddit/agentdevelopmentkit/subreddit_info.txt").read(),
        ),
        InputSchema( subreddit="LLMDevs", time_range="TODAY", limit=100, target_number=10, audience_specification="Deprioritize posts that are obviously marketing oriented, everyone is trying to sell something, we want developer-oriented content instead.",
            subreddit_description=open("./input_sources/reddit/LLMDevs/subreddit_info.txt").read(),
        ),
        InputSchema( subreddit="LangChain", time_range="TODAY", limit=100, target_number=10, audience_specification="Deprioritize posts that are obviously marketing oriented, everyone is trying to sell something, we want developer-oriented content instead.",
            subreddit_description=open("./input_sources/reddit/langchain/subreddit_info.txt").read(),
        ),
        InputSchema( subreddit="PydanticAI", time_range="TODAY", limit=100, target_number=10, audience_specification="Deprioritize posts that are obviously marketing oriented, everyone is trying to sell something, we want developer-oriented content instead.",
            subreddit_description=open("./input_sources/reddit/PydanticAI/subreddit_info.txt").read(),
        ),
    ]
    for subreddit in subreddits_to_process:
        try:
            content = await get_content(
                parser_agent_config=subreddit
            )
            logger.info(f"Writing content for {subreddit.subreddit} subreddit")
            write_documents_to_json(content, f"output_data/{today}/reddit-{subreddit.subreddit}_content.json")
        except RuntimeError as e:
            logger.error(f"Error getting content for {subreddit.subreddit} subreddit: {e}")

if __name__ == "__main__":
    asyncio.run(main())