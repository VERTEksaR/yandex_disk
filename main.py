import logging

import config_data

from template_cloud import FilesCloud

logging.basicConfig(level=logging.INFO, filename=config_data.PATH_TO_LOG_FILE,
                    filemode='a', format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

DISK_FILES, COMP_FILES = [], []


if __name__ == '__main__':
    disk = FilesCloud(url='https://cloud-api.yandex.net/v1/disk/resources',
                      headers={'Authorization': f'OAuth {config_data.TOKEN_CLOUD}'},
                      cloud_dir=config_data.DIR_NAME_CLOUD)

    disk.run()
