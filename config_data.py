import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit('Переменные окружения не загружены, т.к. отсутствует файл .env')
else:
    load_dotenv()


PATH_TO_SYNC_DIR = os.getenv('PATH_TO_SYNC_DIR')
DIR_NAME_CLOUD = os.getenv('DIR_NAME_CLOUD')
TOKEN_CLOUD = os.getenv('TOKEN_CLOUD')
PERIOD_OF_SYNC = os.getenv('PERIOD_OF_SYNC')
PATH_TO_LOG_FILE = os.getenv('PATH_TO_LOG_FILE')
