import requests
from PIL import Image
import os
import math
import shutil
from typing import List, Tuple
from loguru import logger

PUBLIC_KEY = 'https://disk.yandex.ru/d/V47MEP5hZ3U1kg'
SAVE_TO_LINK = 'images'


class DownloadFromYandexDisk:
    def __init__(self, public_key):
        logger.success("Successful initialization DownloadFromYandexDisk")
        self._public_key: str = public_key
        self.folders_list = public_key

    def get_link_to_download(self, path_to_folder: str) -> str:
        """Получение ссылки для скачивания папки"""
        try:
            full_url = (f'https://cloud-api.yandex.net/v1/disk/public/resources/download'
                        f'?public_key={self._public_key}&path=/{path_to_folder}')
            response = requests.get(full_url)
            logger.info(f"query response from {full_url}")
            data = response.json()
            logger.info(f"get json data from response:{response}")
            link_for_download = data['href']
            logger.info(f"get downloaded link: {link_for_download}")
            return link_for_download
        except Exception as e:
            logger.error(f"error during running func get_link_to_download, error:{e}")

    @staticmethod
    def save_folder_to_zip(folder_name: str, link: str) -> None:
        """Запись папки в виде zip архива"""
        try:
            response = requests.get(link)
            logger.info(f"downloaded file from path:{link}")
            with open(f'{folder_name}.zip', 'wb') as zip_writer:
                zip_writer.write(response.content)
                logger.info(f"write {folder_name} file in zip {folder_name}.zip")
        except Exception as e:
            logger.error(f"error during save folder to zip,\n folder_name:{folder_name}\nlink:{link} \n error:{e} ")


class FolderDownloader:
    def __init__(self, yandex_disk_downloader: DownloadFromYandexDisk, folders_list: list[str]):
        logger.success("Successful initialization FolderDownloader")
        self.yandex_disk_downloader = yandex_disk_downloader
        self.folders_list = folders_list

    def download_folders(self):
        """Сохранение всех папок из списка"""
        try:
            logger.info(f"download folder from folder lost {self.folders_list}")
            for folder in self.folders_list:
                downloaded_link = self.yandex_disk_downloader.get_link_to_download(folder)
                self.yandex_disk_downloader.save_folder_to_zip(folder, downloaded_link)
                logger.info(f"download folder:{folder}")
        except Exception as e:
            logger.error(f"error during running func: download_folders , error:{e} ")


class ZipConverter:
    def __init__(self, files_list):
        self.files_list = files_list
        self.save_to_link = SAVE_TO_LINK
        logger.success("Successful initialization ZipConverter")

    def unpack_archive(self, zip_link):
        try:
            shutil.unpack_archive(zip_link, self.save_to_link)
            logger.info(f"unpack archive from path: {zip_link} to folder {self.save_to_link}")
        except Exception as e:
            logger.error(f"error during unpack archive from link:{zip_link},error:{e}")

    def unpack_all_archive(self):
        logger.info("start unpack all archive ")
        for archive in self.files_list:
            self.unpack_archive(archive + '.zip')
            logger.info(f"unpack archive {archive}.zip ")


class TifConverter:
    def __init__(self, images_folders):
        self.all_images = []
        self.images_folders = images_folders
        logger.success("Successful initialization TifConverter")

    def _set_images_from_all_folders_in_one_list(self):
        try:
            for folder in self.images_folders:
                folder = folder.replace("%20", " ")
                list = os.listdir(f'images/{folder}')
                logger.info(f"get list with files from folder{list}, folder:{folder}")
                list_1 = ['images/' + folder + '/' + file_name for file_name in list]
                logger.info(f"get list with absolute path from folder{list_1}")
                self.all_images += list_1
                logger.info(f"add {list_1} to {self.all_images}")
        except Exception as e:
            logger.error(f"error during adding all files to one list,error{e} ")

    def result_tif_file(self):
        self._set_images_from_all_folders_in_one_list()
        logger.info(f"set all images from folders in one list,one list:{self.all_images}")
        collage_creator = ImageCollageCreator(self.all_images)
        collage_creator.create_and_save_collage('result.tif')
        logger.info("create result.tif file")


# f = DownloadFromYandexDisk(['1369_12_Наклейки%203-D_3'])
# f.download_folders_in_list()


class ImageLoader:
    """Класс для загрузки изображений."""

    def load_images(self, file_paths: List[str]) -> List[Image.Image]:
        images_list = [Image.open(file_path) for file_path in file_paths]
        logger.info(f"convert all files from {file_paths} to Image type")
        return images_list


class ImageCollage:
    """Класс для создания коллажа изображений."""

    def __init__(self, images: List[Image.Image], spacing: int = 10, margin: int = 20):
        self.images = images
        self.spacing = spacing
        self.margin = margin
        self.num_rows = 2
        self.num_columns = self._calculate_columns()
        logger.success("Successful initialization ImageCollage")

    def _calculate_columns(self) -> int:
        column_count = math.ceil(len(self.images) / self.num_rows)
        logger.info(f"get amount column in _calculate_columns func,amount: {column_count}")
        return column_count

    def _get_image_size(self) -> Tuple[int, int]:
        image_size = self.images[0].size
        logger.info(f"get size image,{image_size}")
        return image_size

    def _calculate_collage_size(self) -> Tuple[int, int]:
        img_width, img_height = self._get_image_size()
        logger.info(f"get size one image")
        total_width = self.num_columns * img_width + (self.num_columns - 1) * self.spacing + 2 * self.margin
        total_height = self.num_rows * img_height + (self.num_rows - 1) * self.spacing + 2 * self.margin
        logger.info(f"set total image size {total_width}x{total_height}")
        return total_width, total_height

    def create_collage(self) -> Image.Image:
        total_width, total_height = self._calculate_collage_size()
        collage = Image.new('RGB', (total_width, total_height), (255, 255, 255))
        logger.info("final tif image creation")

        for index, img in enumerate(self.images):
            col = index // self.num_rows
            row = index % self.num_rows
            x_offset = col * (img.width + self.spacing) + self.margin
            y_offset = row * (img.height + self.spacing) + self.margin
            collage.paste(img, (x_offset, y_offset))
        logger.info("Collage created")

        return collage


class CollageSaver:
    """Класс для сохранения коллажа изображений."""

    def save(self, collage: Image.Image, output_path: str, format: str = 'TIFF') -> None:
        logger.debug("save called with output_path: {} format: {}", output_path, format)
        collage.save(output_path, format=format)
        logger.info("Collage saved as {} in format {}", output_path, format)


class ImageCollageCreator:
    """Фасад для создания и сохранения коллажа изображений."""

    def __init__(self, file_paths: List[str], spacing: int = 10, margin: int = 20):
        logger.success("Successful initialization ImageCollageCreator with file_paths: {} spacing: {} margin: {}", file_paths, spacing, margin)
        self.file_paths = file_paths
        self.spacing = spacing
        self.margin = margin

    def create_and_save_collage(self, output_path: str) -> None:
        logger.debug("create_and_save_collage called with output_path: {}", output_path)
        loader = ImageLoader()
        images = loader.load_images(self.file_paths)

        collage_creator = ImageCollage(images, self.spacing, self.margin)
        collage = collage_creator.create_collage()

        saver = CollageSaver()
        saver.save(collage, output_path)
        logger.info("Collage created and saved at {}", output_path)


def clean_after_work():
    shutil.rmtree(SAVE_TO_LINK)
    for file_name in os.listdir(os.getcwd()):
        if file_name[-4:] == '.zip':
            os.remove(file_name)


folders_list = input("Введите все папки которые вам нужно скачать с Яндекс диска через пробел").split()

yandex_disk_downloader = DownloadFromYandexDisk(PUBLIC_KEY)
folder_downloader = FolderDownloader(yandex_disk_downloader, folders_list)
folder_downloader.download_folders()

zip_converter = ZipConverter(folders_list)
zip_converter.unpack_all_archive()

tif_converter = TifConverter(folders_list)
tif_converter.result_tif_file()



clean_after_work()
'1388_2_Наклейки%203-D_1'
'1369_12_Наклейки%203-D_3'
'1388_12_Наклейки%203-D_3'
'1388_6_Наклейки%203-D_2'
