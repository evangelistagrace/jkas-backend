import logging
from logging.config import fileConfig
import logging.handlers as handlers
from logging.handlers import SocketHandler
import time

fileConfig('logging_config.ini')
logger = logging.getLogger()
logger.setLevel(1)  # to send all records to cutelog
socket_handler = SocketHandler('127.0.0.1', 19996)  # default listening address
logger.addHandler(socket_handler)
# logger.info('Hello world!')