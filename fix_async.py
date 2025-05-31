#!/usr/bin/env python3
"""Quick fix for async calls in CLI"""

import re

# Read the CLI file
with open('src/backtesting/cli.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all remaining async calls
content = re.sub(
    r'data = provider\.get_historical_data\(',
    'data = asyncio.run(provider.get_historical_data(',
    content
)

# Write back
with open('src/backtesting/cli.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed async calls in CLI")
