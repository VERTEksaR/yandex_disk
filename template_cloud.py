import configparser
import logging
import os
import time
from typing import Dict
from datetime import datetime, timedelta

import requests
from requests import Response

import config_data

logging.basicConfig(level=logging.INFO, filename=config_data.PATH_TO_LOG_FILE,
                    filemode='a', format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


class FilesCloud:
    """
    Класс для базовых операций с файлами для облачных хранилищ

    Args:
        url: (str) Ссылка на URL облачного хранилища
        headers: (Dict[str: str]) Заголовки для подключения по URL через модуль request
        cloud_dir: (str) Название папки в облачном хранилище

    Methods:
        load(filename): Метод для загрузки файла на облачное хранилище
        reload(filename): Метод для перезаписи файла на облачное хранилище
        delete(filename): Метод для удаления файла с облачного хранилища
        get_info(filename): Метод для получения информации о папке или файле
        на облачном хранилище
        check_file_exists(file_path_cloud): Метод для проверки наличия файла
        в облачном хранилище
    """
    def __init__(self, url: str, headers: Dict[str, str], cloud_dir: str) -> None:
        self.url = url
        self.headers = headers
        self.cloud_dir = cloud_dir
        self.comp_dir = config_data.PATH_TO_SYNC_DIR
        self.time_sleep = config_data.PERIOD_OF_SYNC
        self.DISK_FILES = []
        self.COMP_FILES = []

        if os.path.exists('config.ini'):
            logger.info('Конфиг уже существует')
        else:
            self.__create_config()
            logger.info('Конфиг создан')

        is_folder_created = self.__check_folder_exists()

        if is_folder_created == 200:
            logger.info('Папка в ЯД уже существует')
        else:
            self.__create_folder()
            logger.info('Папка %s создана', self.cloud_dir)

    def load(self, filename: str) -> bool:
        """
        Метод загрузки файла на облачное хранилище
        :param filename: (str) Название добавляемого файла
        :return: bool
        """
        href = self.check_file_exists(f'{self.cloud_dir}/{filename}')

        if href:
            try:
                with open(os.path.join(
                        '\\', config_data.PATH_TO_SYNC_DIR, filename), 'rb') as add_file:
                    file = add_file.read()
                    upload_file = {'file': file}
                    requests.put(href, files=upload_file, timeout=15)
                    return True
            except FileNotFoundError:
                logger.error('Файл %s удалили сразу же, как только он был создан', filename)
        return False

    def reload(self, filename: str) -> None:
        """
        Метод для перезаписи файла на облачное хранилище
        :param filename: (str) Название перезаписываемого файла
        :return: None
        """
        self.delete(filename=filename)
        self.load(filename)
        logger.info('Файл %s перезаписан', filename)

    def delete(self, filename: str) -> None:
        """
        Метод для удаления файла с облачного хранилища
        :param filename: (str) Название удаляемого файла
        :return: None
        """
        params = {'path': f'{self.cloud_dir}/{filename}', 'permanently': 'true'}
        requests.delete(self.url, headers=self.headers, params=params, timeout=15)

    def get_info(self, filename='') -> Response:
        """
        Метод для получения информации о папке с файлами или определенного файла
        :param filename: (str) Название файла (если не менять, то выдаст инфу папки)
        :return: Response
        """
        if filename == '':
            params = {'path': self.cloud_dir}
        else:
            params = {'path': f'{self.cloud_dir}/{filename}'}

        result = requests.get(self.url, headers=self.headers, params=params, timeout=15)
        logger.info('Получена информация о %s', params['path'])
        return result

    def check_file_exists(self, file_path_cloud: str) -> str | bool:
        """
        Метод для проверки наличия файла в облачном хранилище
        :param file_path_cloud: (str) Путь до файла на ЯД
        :return: str | bool
        """
        params = {'path': file_path_cloud}
        result = requests.get(f'{self.url}/upload', headers=self.headers,
                              params=params, timeout=15)

        try:
            href = result.json()['href']
            return href
        except KeyError:
            return False

    def __get_list_all_files_disk(self) -> None:
        """
        Метод для добавления всех файлов на ЯД в отдельный список
        :return: None
        """
        result = requests.get(f'{self.url}/files', headers=self.headers,
                              timeout=15).json()

        for file in result['items']:
            self.DISK_FILES.append(file['name'])

    def __get_list_all_files_comp(self) -> None:
        """
        Метод для добавления всех файлов на компьютере в отдельный список
        :return: None
        """
        files = os.listdir(self.comp_dir)

        for file in files:
            if file not in self.COMP_FILES and os.path.isfile(
                os.path.join('\\', self.comp_dir, file)
            ):
                self.COMP_FILES.append(file)

    def __check_delete_diff_files(self) -> None:
        """
        Метод для удаления файлов с ЯД, если они были удалены
        до включения программы
        :return: None
        """
        diff = list(set(self.DISK_FILES) - set(self.COMP_FILES))

        if len(diff) != 0:
            for need_to_delete in diff:
                self.delete(need_to_delete)
                self.DISK_FILES.remove(need_to_delete)
                logger.info('Удален файл %s при инициализации приложения', need_to_delete)

    @staticmethod
    def __create_config() -> None:
        """
        Метод для создания config.ini
        :return: None
        """
        config = configparser.ConfigParser()
        config.add_section('Settings')
        config.set('Settings', 'path_to_sync_dir', config_data.PATH_TO_SYNC_DIR)
        config.set('Settings', 'dir_name_cloud', config_data.DIR_NAME_CLOUD)
        config.set('Settings', 'token_cloud', config_data.TOKEN_CLOUD)
        config.set('Settings', 'period_of_sync', config_data.PERIOD_OF_SYNC)
        config.set('Settings', 'path_to_log_file', config_data.PATH_TO_LOG_FILE)

        with open('config.ini', 'w', encoding='utf-8') as config_file:
            config.write(config_file)

    def __check_folder_exists(self) -> int:
        """
        Метод для проверки наличия файла в ЯД
        :return: (int) result.status_code
        """
        result = requests.get(f'{self.url}?path={self.cloud_dir}',
                              headers=self.headers, timeout=15)
        return result.status_code

    def __create_folder(self) -> None:
        """
        Метод для создания папки в ЯД
        :return: None
        """
        requests.put(f'{self.url}?path={self.cloud_dir}',
                     headers=self.headers, timeout=15)

    def __check_changes_in_file(self, path: str, time_file_comp: datetime) -> bool:
        """
        Метод для проверки последнего изменения файла на компьютере
        :param path: (str) Путь до проверяемого файла
        :param time_file_comp: (datetime) Время последнего изменения файла
        на компьютере
        :return: (bool) Yes - если файл изменялся | No - если файл не изменялся
        """
        params = {'path': path}
        result = requests.get(self.url, headers=self.headers,
                              params=params, timeout=15)
        mdate = datetime.strptime(result.json()['modified'].replace('T', ' ')[:-6],
                                  '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)
        return bool(time_file_comp > mdate)

    def run(self) -> None:
        """
        Основной метод работы приложения
        :return: None
        """
        self.__get_list_all_files_disk()
        self.__get_list_all_files_comp()
        self.__check_delete_diff_files()

        while True:
            try:
                self.__get_list_all_files_disk()
                self.__get_list_all_files_comp()

                for file in self.COMP_FILES:
                    path = os.path.join('\\', self.comp_dir, file)
                    href = self.check_file_exists(f'{self.cloud_dir}/{file}')

                    if href:
                        self.load(file)
                        logger.info('Файл %s добавлен в ЯД', file)

                    try:
                        mtime = os.path.getmtime(path)
                        mtime_readable = datetime.fromtimestamp(mtime)
                        result = self.__check_changes_in_file(f'{self.cloud_dir}/{file}',
                                                              mtime_readable)
                        if result:
                            self.reload(file)
                    except FileNotFoundError:
                        self.delete(file)
                        self.COMP_FILES.remove(file)
                        logger.info('Файл %s удален', file)
                time.sleep(int(self.time_sleep))
            except ConnectionError:
                logger.error('Проблема с подключением')
                time.sleep(int(self.time_sleep))
