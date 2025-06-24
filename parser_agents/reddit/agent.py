from common.partials import DOCUMENT_CATEGORY_PARTIAL
from common.schemas import Document, DocumentCategory
from common.utils import auth_tools
from parser_agents.reddit.tools import (
    get_top_posts_metadata_in_subreddit,
    filter_posts, expand_posts, translate_items)
import os
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List
from arcadepy import AsyncArcade
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class OutputSchema(BaseModel):
    post_ids: list[str] = Field(description="The list of post ids in order of best to worst")
    reasoning: str = Field(description="The reasoning for the ranking")
    document_category: list[DocumentCategory] = Field(
        description="The list document categories (tones) of the posts"
    )
class InputSchema(BaseModel):
    subreddit: str = Field(description="The subreddit to get content from")
    time_range: str = Field(description="The time range to get content from")
    limit: int = Field(description="The number of posts to get")
    target_number: int = Field(description="The number of posts to return")
    audience_specification: str = Field(description="The audience specification")
    subreddit_description: str = Field(description="The description of the subreddit")

async def get_content(parser_agent_config: InputSchema) -> List[Document]:
    client = AsyncArcade()
    await auth_tools(
        client=client,
        user_id=os.getenv("USER_ID"),
        tool_names=["Reddit.GetContentOfMultiplePosts",
                    "Reddit.GetPostsInSubreddit"],
        provider="reddit"
    )

    logger.info(f"Getting top posts metadata in subreddit {parser_agent_config.subreddit}")
    posts = await get_top_posts_metadata_in_subreddit(
        client=client,
        subreddit=parser_agent_config.subreddit,
        time_range=parser_agent_config.time_range,
        limit=parser_agent_config.limit
    )
    posts = await filter_posts(
        posts=posts,
        target_number=parser_agent_config.target_number
    )

    logger.info("Expanding posts...")
    posts = await expand_posts(
        client=client,
        posts=posts
    )

    subreddit = parser_agent_config.subreddit
    subreddit_description = parser_agent_config.subreddit_description

    system_prompt_template = """
    You are a helpful assistant that is an expert in identifying the BEST Reddit posts from any subreddit.
    Your job is to rank the posts from best to worst.
    The best post is the one that you think will get the most engagement (comments, upvotes, etc.).
    {audience_specification}
    Deprioritize posts that are obviously spam.

    {partials}

    You will be given a subreddit and a list of posts from the subreddit.

    The subreddit is "{subreddit}".

    A detailed description of the subreddit is provided below.

    <subreddit_description>
    {subreddit_description}
    </subreddit_description>

    Here are 10 posts from the subreddit.

    <posts>
    {posts}
    </posts>

    """

    few_shot_template = """
    <post>
    <id>
    {id}
    </id>
    <title>
    {title}
    </title>
    <body>
    {body}
    </body>
    </post>
    """

    few_shot_examples = []
    for post in posts:
        few_shot_examples.append(
            few_shot_template.format(
                id=post['id'],
                title=post['title'],
                body=post['body']))

    few_shot_examples = "\n".join(few_shot_examples)

    partials = DOCUMENT_CATEGORY_PARTIAL

    system_prompt = system_prompt_template.format(
        subreddit=subreddit,
        audience_specification=parser_agent_config.audience_specification,
        partials=partials,
        subreddit_description=subreddit_description,
        posts=few_shot_examples)

    # TODO(Mateo): Implement simple model selection logic
    agent = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06"),
    )
    agent = agent.with_structured_output(OutputSchema)

    logger.info("Invoking agent...")
    ids_before = [post["id"] for post in posts]
    logger.info(f"IDs before: {ids_before}")
    response = agent.invoke([{"role": "system", "content": system_prompt}])

    logger.info(f"IDs after: {response.post_ids}")
    if set(ids_before) != set(response.post_ids):
        logger.warning("IDs before and after are different, this is not expected")
        logger.warning(f"IDs before: {ids_before}")
        logger.warning(f"IDs after: {response.post_ids}")
        logger.warning("This is not expected, please investigate")
        raise RuntimeError("IDs before and after are different, this is not expected")

    logger.info("Translating posts...")
    return await translate_items(
        posts=posts,
        ordered_ids=response.post_ids,
        document_categories=response.document_category
    )
