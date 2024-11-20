# модуль для управления back-end частью

from .init_db import DBA_tools #импортируем нужный класс для управления базой данных

db = DBA_tools()
from sql import *

version = "0.0.1"