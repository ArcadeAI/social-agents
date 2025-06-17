from arcadepy import Arcade
from dotenv import load_dotenv
from utils.reddit import get_top_posts_metadata_in_subreddit, filter_posts, expand_posts, auth_tools
import os
import pprint
from langchain_openai import ChatOpenAI
import asyncio
from pydantic import BaseModel, Field
#load_dotenv()

class OutputSchema(BaseModel):
    post_ids: list[str] = Field(description="The list of post ids in order of best to worst")
    reasoning: str = Field(description="The reasoning for the ranking")



async def main():

    await auth_tools(
        os.getenv("USER_ID"),
        ["Reddit.GetContentOfMultiplePosts",
         "Reddit.GetPostsInSubreddit"])

    posts = await get_top_posts_metadata_in_subreddit(subreddit="mcp", time_range="TODAY", limit=100)
    posts = await filter_posts(posts, target_number=10)
    posts = await expand_posts(posts)

    subreddit = "mcp"
    subreddit_description = open("subreddit_info.txt").read()

    system_prompt_template = """
    You are a helpful assistant that is an expert in identifying the BEST Reddit posts from any subreddit.
    Your job is to rank the posts from best to worst.
    The best post is the one that you think will get the most engagement (comments, upvotes, etc.).
    Deprioritize posts that are obviously marketing oriented, everyone is trying to sell something, we want developer-oriented content instead.
    Deprioritize posts that are obviously spam.

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

    system_prompt = system_prompt_template.format(
        subreddit=subreddit,
        subreddit_description=subreddit_description,
        posts=few_shot_examples)

    agent = ChatOpenAI(
        model="gpt-4o-2024-08-06",
    )
    agent = agent.with_structured_output(OutputSchema)

    response = agent.invoke([{"role": "system", "content": system_prompt}])
    print(response)

if __name__ == "__main__":
    asyncio.run(main())