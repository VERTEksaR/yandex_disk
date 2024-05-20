import config_data

from template_cloud import FilesCloud


if __name__ == '__main__':
    disk = FilesCloud(url='https://cloud-api.yandex.net/v1/disk/resources',
                      headers={'Authorization': f'OAuth {config_data.TOKEN_CLOUD}'},
                      cloud_dir=config_data.DIR_NAME_CLOUD)

    disk.run()
