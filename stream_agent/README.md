# Arcade's Livestreaming Agents

The agents below are being built live on Arcade's live-streaming every Tuesday.

The purpose of the _current_ agent is to replicate the functionality of LangChain's
[Social Media Agent](https://github.com/langchain-ai/social-media-agent) but splitting
the concerns into multiple smaller, composable agents.

# DevLog

## 2025-06-17 - Starting the Reddit Agent
We used [The Reddit Toolkit](https://docs.arcade.dev/toolkits/social-communication/reddit) to gather and rank the top 10 posts from a subreddit. We sort the posts manually based on the engagement metrics, and the use LangChain to prioritize the posts based on how relevant they are for developers.