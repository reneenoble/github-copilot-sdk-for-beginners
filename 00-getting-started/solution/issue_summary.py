"""
Chapter 0 — Getting Started: Solution
GitHub Copilot SDK for Beginners

A simple CLI tool that summarizes a GitHub issue using the Copilot SDK.
"""

import asyncio
from copilot import CopilotClient


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
    # Step 1: Create a client and start it
    client = CopilotClient()
    await client.start()

    # Step 2: Create a session with a model
    session = await client.create_session({"model": "gpt-4.1"})

    # Step 3: Send the issue and ask for a summary
    response = await session.send_and_wait({
        "prompt": f"Summarize this GitHub issue in 2-3 sentences:\n\n{SAMPLE_ISSUE}"
    })

    # Step 4: Print the response
    print("Issue Summary:")
    print(response.data.content)

    # Step 5: Clean up
    await session.destroy()
    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
