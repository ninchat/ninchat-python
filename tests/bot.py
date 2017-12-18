import logging
import sys
from glob import glob

sys.path = glob("build/lib.*/") + sys.path
sys.path.insert(0, "")

from ninchat.bot.asyncio.main import main

if __name__ == "__main__":
    main()
