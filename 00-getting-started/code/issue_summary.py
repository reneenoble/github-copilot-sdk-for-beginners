"""
Chapter 0 — Getting Started: Starter Code
GitHub Copilot SDK for Beginners

TODO: Complete this script to create your first Copilot SDK agent.
Follow the instructions in the comments below.
"""

import asyncio
from copilot import CopilotClient


# A sample GitHub issue to summarize
SAMPLE_ISSUE = """
Title: Login page crashes on mobile Safari

When users try to log in using Safari on iOS 17, the page crashes after
clicking the "Sign In" button. The error in the console shows:
TypeError: Cannot read properties of undefined (reading 'focus')

This happens because the autofocus directive is trying to reference a
DOM element that hasn't rendered yet on mobile browsers.

Steps to reproduce:
1. Open the app on iOS Safari
2. Navigate to /login
3. Enter credentials and click "Sign In"
4. Page crashes with white screen
"""


async def main():
    # TODO 1: Create a CopilotClient and start it
    # Hint: client = CopilotClient()

    # TODO 2: Create a session with the "gpt-4.1" model
    # Hint: session = await client.create_session({"model": "..."})

    # TODO 3: Send the issue to the model and ask it to summarize
    # Hint: response = await session.send_and_wait({"prompt": "..."})

    # TODO 4: Print the response content
    # Hint: print(response.data.content)

    # TODO 5: Clean up — destroy the session and stop the client
    pass


if __name__ == "__main__":
    asyncio.run(main())
