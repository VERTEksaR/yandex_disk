import configparser
import os
import time
import requests
import logging

from datetime import datetime, timedelta
from requests import ConnectionError

import config_data

URL = 'https://cloud-api.yandex.net/v1/disk/resources'
TOKEN = config_data.TOKEN_CLOUD
HEADERS = {'Authorization': f'OAuth {TOKEN}'}

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

FILE_TIME = {}
DISK_FILES, COMP_FILES = [], []


def create_config():
    # Создание конфигурации
    config = configparser.ConfigParser()
    config.add_section('Settings')
    config.set('Settings', 'path_to_sync_dir', config_data.PATH_TO_SYNC_DIR)
    config.set('Settings', 'dir_name_cloud', config_data.DIR_NAME_CLOUD)
    config.set('Settings', 'token_cloud', TOKEN)
    config.set('Settings', 'period_of_sync', config_data.PERIOD_OF_SYNC)
    config.set('Settings', 'path_to_log_file', config_data.PATH_TO_LOG_FILE)

    # Сохранение конфигурации в файл
    with open('config.ini', 'w') as config_file:
        config.write(config_file)


def create_folder(path):
    requests.put(f'{URL}?path={path}', headers=HEADERS)


def check_folder_exists(path):
    result = requests.get(f'{URL}?path={path}', headers=HEADERS)
    return result.status_code


def post_file_to_disk(path, path_from_get, file=''):
    try:
        upload_file = {'file': open(path, 'rb')}
        requests.put(path_from_get, files=upload_file)
        return True
    except FileNotFoundError:
        logger.error(f'Файл {file} удалили сразу же, как только он был создан')


def check_file_if_not_exists(cloud_path):
    params = {'path': cloud_path}
    result = requests.get(f'{URL}/upload', headers=HEADERS, params=params)

    try:
        href = result.json()['href']
        return href
    except KeyError:
        return False


def check_changes_in_file(path, time_file_comp):
    params = {'path': path}
    result = requests.get(URL, headers=HEADERS, params=params)
    mdate = datetime.strptime(result.json()['modified'].replace('T', ' ')[:-6], '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)

    if time_file_comp > mdate:
        return True
    else:
        return False


def delete_file(path):
    params = {'path': path, 'permanently': 'true'}
    requests.delete(URL, headers=HEADERS, params=params)


def get_list_all_files_disk():
    result = requests.get(f'{URL}/files', headers=HEADERS).json()

    for file in result['items']:
        DISK_FILES.append(file['name'])


def get_list_all_files_comp():
    files = os.listdir(config_data.PATH_TO_SYNC_DIR)

    for comp_file in files:
        if comp_file not in COMP_FILES:
            COMP_FILES.append(comp_file)


def first_settings():
    # Проверка наличия конфиг-файла
    if os.path.exists('config.ini'):
        logger.info('Конфиг уже существует')
    else:
        create_config()
        logger.info('Конфиг создан')

    # Проверка на наличие папки на ЯД
    is_folder_created = check_folder_exists(config_data.DIR_NAME_CLOUD)

    if is_folder_created == 200:
        logger.info('Папка в ЯД уже существует')
    else:
        # Создание папки на ЯД
        create_folder(config_data.DIR_NAME_CLOUD)
        logger.info(f'Папка {config_data.DIR_NAME_CLOUD} создана')


def rewrite_file(path, file):
    delete_file(f'{config_data.DIR_NAME_CLOUD}/{file}')
    href_reload = check_file_if_not_exists(f'{config_data.DIR_NAME_CLOUD}/{file}')
    post_file_to_disk(path, href_reload)
    logger.info(f'Файл {file} перезаписан')


def check_delete_diff_files():
    diff = list(set(DISK_FILES) - set(COMP_FILES))

    if len(diff) != 0:
        for need_to_delete in diff:
            delete_file(f'{config_data.DIR_NAME_CLOUD}/{need_to_delete}')
            DISK_FILES.remove(need_to_delete)
            logger.info(f'Удален файл {need_to_delete} при инициализации приложения')


def main():
    get_list_all_files_disk()
    get_list_all_files_comp()

    for file in COMP_FILES:
        path = os.path.join('\\', config_data.PATH_TO_SYNC_DIR, file)
        href = check_file_if_not_exists(f'{config_data.DIR_NAME_CLOUD}/{file}')

        if href:
            post_file_to_disk(path, href, file)
            logger.info(f'Файл {file} добавлен в ЯД')

        try:
            mtime = os.path.getmtime(path)
            mtime_readable = datetime.fromtimestamp(mtime)
            result = check_changes_in_file(f'{config_data.DIR_NAME_CLOUD}/{file}', mtime_readable)

            if result:
                rewrite_file(path, file)
        except FileNotFoundError:
            delete_file(f'{config_data.DIR_NAME_CLOUD}/{file}')
            COMP_FILES.remove(file)
            logger.info(f'Файл {file} удален')


if __name__ == '__main__':
    first_settings()
    get_list_all_files_disk()
    get_list_all_files_comp()
    check_delete_diff_files()
    while True:
        try:
            main()
            time.sleep(int(config_data.PERIOD_OF_SYNC))
        except ConnectionError:
            logger.error('Проблема с подкючением')
            time.sleep(int(config_data.PERIOD_OF_SYNC))

