import logging
from logging.config import fileConfig
import logging.handlers as handlers
import time

fileConfig('logging_config.ini')
logger = logging.getLogger()