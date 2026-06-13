#!/bin/bash
set -e

# Use PORT env var from Hugging Face Docker Spaces; default to 7860
PORT="${PORT:-7860}"

# Patch the nginx port placeholder with the actual PORT value
sed -i "s/__PORT__/${PORT}/g" /etc/nginx/sites-available/default

# Validate nginx configuration before starting
nginx -t

# Start supervisor — manages both uvicorn (background) and nginx (foreground)
exec supervisord -c /etc/supervisor/conf.d/workbench.conf
