import configparser
import os
import requests
import yadisk

import config_data

URL = 'https://cloud-api.yandex.net/v1/disk/resources'
TOKEN = config_data.TOKEN_CLOUD
HEADERS = {'Content-Type': 'application/json',
           'Accept': 'application/json',
           'Authorization': f'OAuth {TOKEN}'}


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


def post_file_to_disk(path, path_from_get):
    result = requests.put(f'{URL}/upload?path=/Ddhdtgata/aaa.txt&url={path_from_get}', headers=HEADERS)
    print(result)


def check_file_is_not_exists(cloud_path):
    result = requests.get(f'{URL}/upload?path={cloud_path}&overwrite=false', headers=HEADERS).json()

    if result['href']:
        print('Get link to upload file')
        href = result['href']
        return href

    print('File already exists')
    return False


if __name__ == '__main__':
    # Проверка наличия конфиг-файла
    if os.path.exists('config.ini'):
        print('Config already exists')
    else:
        print('Creating config file')
        create_config()
        print('Config file was created')

    # Проверка на наличие папки на ЯД
    is_folder_created = check_folder_exists(config_data.DIR_NAME_CLOUD)

    if is_folder_created == 200:
        print('Folder exists')
    else:
        print("Folder doesn't exist")
        # Создание папки на ЯД
        print(f'Staring to create folder with name {config_data.DIR_NAME_CLOUD}')
        create_folder(config_data.DIR_NAME_CLOUD)
        print(f'Folder {config_data.DIR_NAME_CLOUD} was created')

    files = []

    for file in os.listdir(config_data.PATH_TO_SYNC_DIR):
        print('Print file from folder')
        files.append(file)
        path = os.path.join('\\', config_data.DIR_NAME_CLOUD, file)
        href = check_file_is_not_exists(path)
        print(href)
        post_file_to_disk(config_data.DIR_NAME_CLOUD, href)

