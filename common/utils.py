from typing import List
from arcadepy import AsyncArcade
import asyncio


async def auth_tools(
    client: AsyncArcade,
    user_id: str,
    tool_names: List[str],
    provider: str
):
    # collect the scopes for every tool I want to use
    scopes = set()
    tools = []
    if tool_names:
        tasks = [client.tools.get(name=tool_id) for tool_id in tool_names]
        responses = await asyncio.gather(*tasks)
        for response in responses:
            tools.append(response)

    # collect the scopes
    # TODO(Mateo): Providers can be inferred here, no need for provider parameter
    scopes = set()
    for tool in tools:
        if tool.requirements.authorization.oauth2.scopes:
            scopes |= set(tool.requirements.authorization.oauth2.scopes)

    # start auth
    auth_response = await client.auth.start(
        user_id=user_id,
        scopes=list(scopes),
        provider=provider
    )

    # show the url to the user if needed
    if auth_response.status != "completed":
        print(f"Please click here to authorize: {auth_response.url}")
        # Wait for the authorization to complete
        await client.auth.wait_for_completion(auth_response)