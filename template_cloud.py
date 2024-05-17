import logging
import os
import requests

import config_data

logging.basicConfig(level=logging.INFO, filename=config_data.PATH_TO_LOG_FILE,
                    filemode='a', format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


class FilesCloud:
    def __init__(self, url, headers, cloud_dir):
        self.url = url
        self.headers = headers
        self.cloud_dir = cloud_dir

    def load(self, filename):
        href = self.check_file_exists(f'{self.cloud_dir}/{filename}')

        if href:
            try:
                upload_file = {'file': open(os.path.join('\\', config_data.PATH_TO_SYNC_DIR, filename), 'rb')}
                requests.put(href, files=upload_file)
                return True
            except FileNotFoundError:
                logger.error(f'Файл {filename} удалили сразу же, как только он был создан')

    def reload(self, filename):
        self.delete(filename=filename)
        self.load(filename)
        logger.info(f'Файл {filename} перезаписан')

    def delete(self, filename):
        params = {'path': f'{self.cloud_dir}/{filename}', 'permanently': 'true'}
        requests.delete(self.url, headers=self.headers, params=params)

    def get_info(self, filename=''):
        if filename == '':
            params = {'path': self.cloud_dir}
        else:
            params = {'path': f'{self.cloud_dir}/{filename}'}

        result = requests.get(self.url, headers=self.headers, params=params)
        logger.info(f'Получена информация о {params["path"]}')
        return result

    def check_file_exists(self, file_path_cloud):
        params = {'path': file_path_cloud}
        result = requests.get(f'{self.url}/upload', headers=self.headers, params=params)

        try:
            href = result.json()['href']
            return href
        except KeyError:
            return False
