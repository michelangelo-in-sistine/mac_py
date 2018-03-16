# -*- coding: UTF-8 –*-

from PIL import Image
from PIL.ExifTags import TAGS
import os
import os.path
import shutil
import time

class ExifUtil:
    def __init__(self):
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
        ext = os.path.splitext(jpg_path)[-1][1:].lower()
        if ext in ('jpg', 'jpeg'):
            img = Image.open(jpg_path)
            exif_info = img._getexif()
            if exif_info is not None:
                return exif_info.get(0x9003, None)          # if get no date info, return None
        return None

    def get_original_year_month(self, jpg_path):
        exif_time = self.get_exif_date_time(jpg_path)
        if exif_time is None:
            ctime = time.strftime(r"%Y:%m:%d %H:%M:%S", time.gmtime(os.path.getctime(jpg_path))) # no exif, ctime is file create time
        else:
            ctime = str(exif_time)

        tmp = ctime.split(':')
        year = tmp[0]
        month = tmp[1]
        return year, month


class PhotoOrganizor():
    def __init__(self, debug_info=True):
        self.exif_util = ExifUtil()
        self.debug_info = debug_info

        self.total = 0                      # 处理文件数
        self.copied = 0                     # 复制文件数
        self.skipped = 0                    # 因重复而跳过的文件数
        self.conflicted = 0                 # 同名不同内容冲突文件数
        self.unsorted = 0                   # 未分类复制文件数

        self.conflicted_files = []
        self.archive_dir = None
        pass

    def reset(self):
        self.total = 0                      # 处理文件数
        self.copied = 0                     # 复制文件数
        self.skipped = 0                    # 因重复而跳过的文件数
        self.conflicted = 0                 # 同名不同内容冲突文件数
        self.unsorted = 0                   # 未分类复制文件数

        self.conflicted_files = []
        self.archive_dir = None
        pass


    def debug_out(self, debug_str):
        if self.debug_info:
            print debug_str

    def cp_file_to_target(self, source_file, target_dir):
        """ copy sourcefile to target folder,
            if same file existed, skip
            if a same name but different content file existed, rename file and copy it
        :param source_file:
        :param target_dir:
        :return:
            0: skiped
            1: copied
            2: rename copied
        """
        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
        target_file = target_dir + '/' + os.path.basename(source_file)
        if not os.path.exists(target_file):
            shutil.copy2(source_file, target_dir)
            result = 1
            self.debug_out('{} => {}'.format(source_file, target_dir))
        else:
            if os.path.getsize(target_file) == os.path.getsize(source_file):
                self.debug_out('target existed')
                self.debug_out('{} <====> {}'.format(source_file, target_file))
                result = 0
            else:
                # 新命名规则: 旧文件名_[1,2,3...]
                base, ext = os.path.splitext(target_file)
                i = 1
                while True:
                    new_target_file = base + '_{:d}'.format(i) + ext
                    if not os.path.exists(new_target_file):
                        shutil.copy2(source_file, new_target_file)
                        result = 2
                        break
                    else:
                        i += 1
        return result

    def stat_archive_result(self, result, item):
        if result == 0:
            self.skipped += 1
        elif result == 1:
            self.copied += 1
        else:
            self.conflicted += 1
            self.conflicted_files.append(item)

    def archive_jpg(self, source_file, archive_dir):
        # 获得jpg中的exif时间, 将文件存储到目标目录下的时间分类子目录
        # 如不存在exif, 则存储到unsorted目录
        # 冲突文件处理: 如文件大小一致, 名字一致, 则认为是重复文件, 不复制
        # 如不是重复文件, 则名称后加自然数序号

        tmp = self.exif_util.get_original_year_month(source_file)
        if tmp is not None:
            year, month = tmp
            target_dir = archive_dir + r'/{}-{}'.format(year, month)
        else:
            target_dir = archive_dir + r'/unsorted_pic'

        if not os.path.exists(target_dir):
            os.mkdir(target_dir)

        return self.cp_file_to_target(source_file, target_dir)

    def organize(self, src_dir, archive_dir, depth=10):
        """
        :param src_dir:
        :param archive_dir:
        :return:
        """
        self.reset()
        if archive_dir[-1] in (r'\/'):
            archive_dir = archive_dir[:-1]
        self.archive_dir = archive_dir

        all_files = os.listdir(src_dir)
        for f in all_files:
            item = src_dir + '/' + f
            if os.path.isdir(item):
                self.organize(item, archive_dir, depth-1)
            else:
                ext = os.path.splitext(item)[-1][1:].lower()
                if ext in ('jpg', 'jpeg', 'png', 'gif'):
                    result = self.archive_jpg(item, archive_dir)
                elif ext in ('mov', 'mp4'):
                    target_dir = archive_dir + r'/video'
                    # result = self.cp_file_to_target(item, target_dir)
                    result = self.archive_jpg(item, target_dir)             # 视频文件也按时间分类
                else:
                    target_dir = archive_dir + r'/misc'
                    result = self.cp_file_to_target(item, target_dir)
                self.stat_archive_result(result, item)

    def save_n_output(self, fid, output_str):
        fid.write(output_str)
        self.debug_out(output_str)

    def report(self):
        output_file = self.archive_dir + r'/archive_log_' + time.strftime('%Y-%m-%d %H-%M-%S') + '.txt'
        with open(output_file, 'w') as fid:
            self.save_n_output(fid, 'total processed files: {}\n'.format(self.total))
            self.save_n_output(fid, 'copied: {}\n'.format(self.copied))
            self.save_n_output(fid, 'skipped: {}\n'.format(self.skipped))
            self.save_n_output(fid, 'conflicted: {}\n'.format(self.conflicted))
            for f in self.conflicted_files:
                self.save_n_output(fid, f)


if __name__ == '__main__':
    org = PhotoOrganizor(debug_info=True)
    org.organize(r'e:\Users\Mac\Downloads\IPhone6_2017_12_03', r'\\192.168.1.251\main\test\org_mac')
    org.report()

    org.organize(r'e:\Users\Mac\Downloads\IPhone7_2017_12_03', r'\\192.168.1.251\main\test\org_joe')
    org.report()

