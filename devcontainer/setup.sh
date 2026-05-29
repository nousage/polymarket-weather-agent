#!/bin/bash
set -e

# Install Hermes Agent
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc

# Clone the four repos into the workspace
cd /workspaces/polymarket-weather-agent
git clone https://github.com/moltlaunch/cashclaw.git
git clone https://github.com/Alishahryar1/free-claude-code.git
git clone https://github.com/D4Vinci/Scrapling.git
git clone https://github.com/ruvnet/ruflo.git

# Install Python dependencies for Scrapling
pip install scrapling
scrapling install

# Install Node dependencies for each repo
cd cashclaw && npm install && cd ..
cd free-claude-code && npm install && cd ..
cd ruflo && npm install && cd ..

# Set up Hermes to use Modal backend (you'll be prompted for token later)
hermes setup terminal --non-interactive --backend modal || true

echo "✅ Setup complete. Run 'hermes' to start the agent."
