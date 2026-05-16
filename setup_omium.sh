#!/bin/bash

echo "🚀 Installing Omium CLI..."
pip install omium

echo "⚙️ Initializing Omium project..."
omium init

echo "☁️ Syncing automation to the Omium dashboard..."
omium sync

echo "✅ Setup complete!"