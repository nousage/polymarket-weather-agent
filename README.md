# Polymarket Weather Agent – Bootstrapped

1. Click "Code" → "Codespaces" → "Create codespace on main"
2. Wait for the setup to finish (2‑3 minutes)
3. Run `hermes setup terminal` and choose Modal (provide your Modal token)
4. Run `hermes` and give this instruction:

**"Build a fully autonomous Polymarket weather trading bot using the four repos in this workspace: Scrapling for live weather, Ruflo for swarm coordination, free‑claude‑code for AI decisions, and CashClaw for execution. The bot should trade temperature markets for 20 cities, use ensemble forecasts (ECMWF+GFS), compute EV and Kelly, and deploy itself on Modal with an hourly cron schedule. Write all code in a folder called 'polybot' and deploy it. After deployment, test it and show me the logs."**

5. Watch Hermes write, test, and deploy the bot. No further manual coding required.
