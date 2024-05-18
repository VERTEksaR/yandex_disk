import configparser
import logging
import os
import time
import requests

from datetime import datetime, timedelta
from requests import ConnectionError

import config_data

from template_cloud import FilesCloud

logging.basicConfig(level=logging.INFO, filename=config_data.PATH_TO_LOG_FILE,
                    filemode='a', format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

DISK_FILES, COMP_FILES = [], []


def create_config() -> None:
    """
    Функция для создания config.ini
    :return: None
    """
    # Создание конфигурации
    config = configparser.ConfigParser()
    config.add_section('Settings')
    config.set('Settings', 'path_to_sync_dir', config_data.PATH_TO_SYNC_DIR)
    config.set('Settings', 'dir_name_cloud', config_data.DIR_NAME_CLOUD)
    config.set('Settings', 'token_cloud', config_data.TOKEN_CLOUD)
    config.set('Settings', 'period_of_sync', config_data.PERIOD_OF_SYNC)
    config.set('Settings', 'path_to_log_file', config_data.PATH_TO_LOG_FILE)

    # Сохранение конфигурации в файл
    with open('config.ini', 'w', encoding='utf-8') as config_file:
        config.write(config_file)


def create_folder(path: str) -> None:
    """
    Функция для создания папки в ЯД
    :param path: (str) Путь создания папки
    :return: None
    """
    requests.put(f'https://cloud-api.yandex.net/v1/disk/resources?path={path}',
                 headers={'Authorization': f'OAuth {config_data.TOKEN_CLOUD}'},
                 timeout=15)


def check_folder_exists(path: str) -> int:
    """
    Функция для проверки наличия файла в ЯД
    :param path: (str) Путь до проверяемой папки
    :return: (int) result.status_code
    """
    result = requests.get(f'https://cloud-api.yandex.net/v1/disk/resources?path={path}',
                          headers={'Authorization': f'OAuth {config_data.TOKEN_CLOUD}'},
                          timeout=15)
    return result.status_code


def check_changes_in_file(path: str, time_file_comp: datetime) -> bool:
    """
    Функция для проверки последнего изменения файла на компьютере
    :param path: (str) Путь до проверяемого файла
    :param time_file_comp: (datetime) Время последнего изменения файла
    на компьютере
    :return: (bool) Yes - если файл изменялся | No - если файл не изменялся
    """
    params = {'path': path}
    result = requests.get('https://cloud-api.yandex.net/v1/disk/resources',
                          headers={'Authorization': f'OAuth {config_data.TOKEN_CLOUD}'},
                          params=params, timeout=15)
    mdate = datetime.strptime(result.json()['modified'].replace('T', ' ')[:-6],
                              '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)

    return bool(time_file_comp > mdate)


def get_list_all_files_disk() -> None:
    """
    Функция для добавления всех файлов на ЯД в отдельный список
    :return: None
    """
    result = requests.get('https://cloud-api.yandex.net/v1/disk/resources/files',
                          headers={'Authorization': f'OAuth {config_data.TOKEN_CLOUD}'},
                          timeout=15).json()

    for file in result['items']:
        DISK_FILES.append(file['name'])


def get_list_all_files_comp() -> None:
    """
    Функция для добавления всех файлов на компьютере в отдельный список
    :return: None
    """
    files = os.listdir(config_data.PATH_TO_SYNC_DIR)

    for comp_file in files:
        if comp_file not in COMP_FILES and os.path.isfile(
                os.path.join('\\', config_data.PATH_TO_SYNC_DIR, comp_file)):
            COMP_FILES.append(comp_file)


def first_settings() -> None:
    """
    Функция для первостепенной настройки программы
    :return: None
    """
    # проверка наличия конфиг-файла
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
        logger.info('Папка %s создана', config_data.DIR_NAME_CLOUD)


def check_delete_diff_files(disk_class: FilesCloud) -> None:
    """
    Функция для удаления файлов с ЯД, если они были удалены
    до включения программы
    :param disk_class: (FilesCloud) Переменная класса
    :return: None
    """
    diff = list(set(DISK_FILES) - set(COMP_FILES))

    if len(diff) != 0:
        for need_to_delete in diff:
            disk_class.delete(need_to_delete)
            DISK_FILES.remove(need_to_delete)
            logger.info('Удален файл %s при инициализации приложения', need_to_delete)


def main(disk_class: FilesCloud) -> None:
    """
    Основная функция работы приложения
    :param disk_class: (FilesCloud) Переменная класса
    :return: None
    """
    get_list_all_files_disk()
    get_list_all_files_comp()

    for file in COMP_FILES:
        path = os.path.join('\\', config_data.PATH_TO_SYNC_DIR, file)
        href = disk_class.check_file_exists(f'{config_data.DIR_NAME_CLOUD}/{file}')

        if href:
            disk_class.load(file)
            logger.info('Файл %s добавлен в ЯД', file)

        try:
            mtime = os.path.getmtime(path)
            mtime_readable = datetime.fromtimestamp(mtime)
            result = check_changes_in_file(f'{config_data.DIR_NAME_CLOUD}/{file}',
                                           mtime_readable)

            if result:
                disk_class.reload(file)
        except FileNotFoundError:
            disk_class.delete(file)
            COMP_FILES.remove(file)
            logger.info('Файл %s удален', file)


if __name__ == '__main__':
    disk = FilesCloud(url='https://cloud-api.yandex.net/v1/disk/resources',
                      headers={'Authorization': f'OAuth {config_data.TOKEN_CLOUD}'},
                      cloud_dir=config_data.DIR_NAME_CLOUD)

    first_settings()
    get_list_all_files_disk()
    get_list_all_files_comp()
    check_delete_diff_files(disk_class=disk)

    while True:
        try:
            main(disk_class=disk)
            time.sleep(int(config_data.PERIOD_OF_SYNC))
        except ConnectionError:
            logger.error('Проблема с подключением')
            time.sleep(int(config_data.PERIOD_OF_SYNC))
