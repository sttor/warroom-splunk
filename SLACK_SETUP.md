# 🤖 Slack App Setup Guide

To connect WarRoom AI to your Slack workspace, you need to create a custom Slack App and enable **Socket Mode**. Socket Mode allows WarRoom AI to securely connect to Slack via WebSockets, meaning you don't need to expose any public URLs or Webhooks.

## Step 1: Create the App
1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App**.
2. Choose **From scratch**.
3. Name it **WarRoom AI** (or anything you like) and select your workspace.

## Step 2: Enable Socket Mode & Get App Token
1. In the left sidebar, click on **Socket Mode**.
2. Toggle the switch to **Enable Socket Mode**.
3. It will prompt you to create an **App-Level Token**. 
   - Name the token something like `socket-token`.
   - Add the scope `connections:write`.
   - Click **Generate**.
4. Copy the token that starts with `xapp-...` and paste it into your `.env` file as `SLACK_APP_TOKEN`.

## Step 3: Configure Bot Permissions (Scopes)
1. In the left sidebar, click on **OAuth & Permissions**.
2. Scroll down to the **Scopes** section, under **Bot Token Scopes**, and click **Add an OAuth Scope**.
3. Add the following scopes:
   - `app_mentions:read` (Allows the bot to know when you @tag it)
   - `channels:history` (Allows the bot to read public channels)
   - `channels:read` (Allows the bot to see channel info)
   - `chat:write` (Allows the bot to send messages)
   - `im:history` (Allows the bot to read direct messages)
   - `im:write` (Allows the bot to send direct messages)

## Step 4: Enable Event Subscriptions
1. In the left sidebar, click on **Event Subscriptions**.
2. Toggle **Enable Events** to **On**.
3. Scroll down to **Subscribe to bot events** and click **Add Bot User Event**.
4. Add the following events:
   - `app_mention`
   - `message.channels` *(Crucial for the silent ingestion feature!)*
   - `message.im`
5. Click **Save Changes** at the bottom of the page.

## Step 5: Install the App & Get Bot Token
1. Go back to **OAuth & Permissions** (or click **Install App** in the left sidebar).
2. Click **Install to Workspace** and authorize the app.
3. Once installed, copy the **Bot User OAuth Token** that starts with `xoxb-...` and paste it into your `.env` file as `SLACK_BOT_TOKEN`.

## Step 6: Invite the Bot to your Channels
1. Open your Slack app.
2. Go to the channel where you want WarRoom AI to listen (e.g., `#incident-warroom`).
3. Type `@WarRoom AI` and hit enter. Slack will ask if you want to add the bot to the channel. Click **Add to Channel**.

You're done! Now run `python3 slack_bot.py` and the bot will spring to life.
