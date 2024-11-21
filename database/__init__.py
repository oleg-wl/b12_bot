# модуль для управления back-end частью

from .db_tools import DBA_tools
from .sql import *

conf = DBA_tools()
engine = conf() 

version = "0.0.1"