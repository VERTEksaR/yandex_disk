import logging
import os
from typing import Dict

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
    def __init__(self, url: str, headers: Dict[str: str], cloud_dir: str) -> None:
        self.url = url
        self.headers = headers
        self.cloud_dir = cloud_dir

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
