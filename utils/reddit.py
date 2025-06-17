from arcadepy import AsyncArcade
from dotenv import load_dotenv
import os
from typing import List
import pprint
import asyncio
load_dotenv()

client = AsyncArcade()

async def get_top_posts_metadata_in_subreddit(
    subreddit: str,
    time_range: str = "TODAY",
    limit: int = 100,
) -> List[dict]:

    async def get_posts_metadata(cursor: str = None) -> dict:
        tool_input = {
            #"cursor": cursor,
            "subreddit": subreddit,
            "listing": "top",
            "time_range": time_range,
            "limit": limit,
        }

        if cursor is not None:
            tool_input["cursor"] = cursor

        return await client.tools.execute(
            tool_name="Reddit.GetPostsInSubreddit",
            input=tool_input,
            user_id=os.getenv("USER_ID"),
        )

    posts = []

    response = await get_posts_metadata()
    try:
        posts.extend(response.output.value["posts"])
    except TypeError as e:
        print(e)
        print(response)
        exit(1)

    cursor = response.output.value["cursor"]
    while cursor is not None:
        response = await get_posts_metadata(cursor=cursor)
        posts.extend(response.output.value["posts"])
        cursor = response.output.value["cursor"]

    return posts



async def filter_posts(posts: List[dict], target_number: int = 10) -> List[dict]:
    """
    Filter posts to only include the top target_number of posts.

    The logic is:
    - only posts that are not videos
    - order by number of comments
    - order by number of upvotes
    - truncate to target_number (if there are more than target_number posts)
    """
    posts = [post for post in posts if not post["is_video"]]
    posts.sort(key=lambda x: x["num_comments"], reverse=True)
    posts.sort(key=lambda x: x["upvotes"], reverse=True)
    return posts[:target_number]


async def expand_posts(posts: List[dict]) -> List[dict]:
    """
    Expand posts to include the full text of the post.
    """

    tool_input = {
        "post_identifiers": [post["id"] for post in posts],
    }

    expanded_posts = await client.tools.execute(
        tool_name="Reddit.GetContentOfMultiplePosts",
        input=tool_input,
        user_id=os.getenv("USER_ID"),
    )

    return expanded_posts.output.value["posts"]


async def auth_tools(user_id: str, tool_names: List[str]):
    # collect the scopes for every tool I want to use
    scopes = set()
    tools = []
    if tool_names:
        tasks = [client.tools.get(name=tool_id) for tool_id in tool_names]
        responses = await asyncio.gather(*tasks)
        for response in responses:
            tools.append(response)

    # collect the scopes
    scopes = set()
    for tool in tools:
        if tool.requirements.authorization.oauth2.scopes:
            scopes |= set(tool.requirements.authorization.oauth2.scopes)

    # start auth
    auth_response = await client.auth.start(user_id=os.getenv("USER_ID"),
                                            scopes=list(scopes),
                                            provider="reddit")

    # show the url to the user if needed
    if auth_response.status != "complete":
        print(f"Please click here to authorize: {auth_response.url}")
        # Wait for the authorization to complete
        await client.auth.wait_for_completion(auth_response)
