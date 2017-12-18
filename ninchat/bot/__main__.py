import logging

from .asyncio.main import main

logging.basicConfig(level=logging.INFO)
try:
    main()
except KeyboardInterrupt:
    pass
