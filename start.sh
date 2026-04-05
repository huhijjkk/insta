#!/bin/bash
#!/bin/bash

pip install -r requirements.txt

export PLAYWRIGHT_BROWSERS_PATH=0
playwright install --with-deps
playwright install chromium

python bot.py
apt-get update
apt-get install -y libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libpangocairo-1.0-0 libasound2 libatspi2.0-0 libgtk-3-0

pip install -r requirements.txt

playwright install chromium
apt-get install -y xvfb
python bot.py
