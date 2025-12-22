import os
import multiprocessing

# Calculate optimal number of workers: (CPU cores * 2) + 1
# workers = multiprocessing.cpu_count() * 2 + 1

# Use a fixed, low number of workers for low-memory environments
# On small Azure App Service plans, each worker is a full Python process.
# Reducing to 1 worker minimizes memory usage and avoids OOM kills.
# Increase this if you move to a larger plan with more RAM.
# NOTE: For SQLite, use 1 worker to avoid "database is locked" errors.
workers = 1

# Use Uvicorn's ASGI worker class for FastAPI
worker_class = "uvicorn.workers.UvicornWorker"

# Bind to the port Azure provides (default 8000 locally)
# bind = "0.0.0.0:8000"
# Dynamically bind to Azure's injected port
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Keep-alive settings for WebSockets
keepalive = 30  # seconds to keep idle connections alive
timeout = 120   # seconds before killing a worker

# Logging
accesslog = "-"  # log to stdout
errorlog = "-"   # log to stderr
loglevel = "info"

# Graceful worker restart settings
graceful_timeout = 30
reload = False  # set True for local dev auto-reload

# Preload app for faster worker start (good for prod)
preload_app = True
