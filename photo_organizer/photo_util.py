# -*- coding: UTF-8 –*-

from PIL import Image
from PIL.ExifTags import TAGS
import os
import os.path
import shutil

class ExifUtil:
    def __init__(self, ):
        pass

    @staticmethod
    def show_all_exif(jpg_path):
        # TAGS is a dict
        img = Image.open(jpg_path)
        exif = img._getexif()
        if exif is not None:
            for tag, value in exif.items():
                print(TAGS.get(tag, tag), value)         # D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None.

    @staticmethod
    def get_exif_date_time(jpg_path):
        # return time str if exif time exists, else None
        img = Image.open(jpg_path)
        exif_info = img._getexif()
        if exif_info is not None:
            return exif_info.get(0x9003, -1)
        return None

    def get_original_year_month(self, jpg_path):
        ctime = str(self.get_exif_date_time(jpg_path))
        if ctime is not None:
            tmp = ctime.split(':')
            year = tmp[0]
            month = tmp[1]
            return year, month


class PhotoOrganizor():
    def __init__(self,):
        self.exif_util = ExifUtil()
        pass

    def cp_file_to_archive_dir(self, base_file, archive_path):
        # 获得jpg中的exif时间, 将文件存储到目标目录下的时间分类子目录
        # 如不存在exif, 则存储到unsorted目录
        # 冲突文件处理: 如文件大小一致, 名字一致, 则认为是重复文件, 不复制
        # 如不是重复文件, 则名称后加自然数序号
        if archive_path[-1] in (r'\/'):
            archive_path = archive_path[:-1]

        tmp = self.exif_util.get_original_year_month(base_file)
        if tmp is not None:
            year, month = tmp
            target_dir = archive_path + r'\{}-{}'.format(year, month)
        else:
            target_dir = archive_path + r'\unsorted'

        if not os.path.exists(target_dir):
            os.mkdir(target_dir)

        target_file = target_dir + '\\' + os.path.basename(base_file)
        if not os.path.exists(target_file):
            shutil.copy2(base_file, target_dir)
        else:
            if os.path.getsize(target_file) == os.path.getsize(base_file):
                print 'conflicts'
                print base_file, '<====>', target_file
            else:
                # 新命名规则: 旧文件名_[1,2,3...]
                base, ext = os.path.splitext(target_file)
                i = 1
                while True:
                    new_target_file = base + '_{:d}'.format(i) + ext
                    if not os.path.exists(new_target_file):
                        shutil.copy2(base_file, new_target_file)
                        break
                    else:
                        i += 1

    def organize(self, src_dir, archive_dir):
        """
        :param src_dir:
        :param archive_dir:
        :return:
        """


if __name__ == '__main__':
    org = PhotoOrganizor()

    filename = r'E:\Users\Mac\Downloads\IPhone7_2017_12_03\DCIM\127APPLE\IMG_7540.JPG'
    org.cp_file_to_archive_dir(filename, r'e:\temp\\')

