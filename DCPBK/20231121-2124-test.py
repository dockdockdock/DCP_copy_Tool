
import sys, os, platform, re, json, time
import subprocess, hashlib, threading
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QSplitter,
    QTextEdit,
    QWidget,
    QLabel,
    QListWidget,
    QPushButton,
    QBoxLayout,
    QAbstractItemView,
    QVBoxLayout,
    QTreeView,
    QFrame,
    QProgressBar,
)

# Note Here
# system = platform.system()
source_dir = ""
destination_dir = ""

class DiskUtilityApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui() 
        self.copy_thread = None
     
    def init_ui(self):
        self.setWindowTitle('DCP-Tool-v1.9')
        self.setGeometry(300,300,1000,600)

        self.select_label = QLabel('选择磁盘:', self)
        self.progress_label = QLabel('目前进度:', self)

        self.disk_list = QTreeView(self)
        self.model = QStandardItemModel(self.disk_list)
        self.model.setHorizontalHeaderLabels([            
            "磁盘名称",
            "卷名",
            "文件系统",   
            "磁盘大小",
            "是否挂载"
        ])
        self.disk_list.setModel(self.model)

        self.scan_button = QPushButton('扫描磁盘',self)
        # self.format_button = QPushButton('格式化为EXT3',self)
        self.Source_button = QPushButton('文件路径',self)
        self.Target_button = QPushButton('拷贝路径',self)
        self.copy_and_verify_button = QPushButton('开始',self)
        self.progress_bar = QProgressBar(self)

        h1_line = QFrame()
        h1_line.setFrameShape(QFrame.HLine)
        h1_line.setFrameShadow(QFrame.Sunken)
        h2_line = QFrame()
        h2_line.setFrameShape(QFrame.HLine)
        h2_line.setFrameShadow(QFrame.Sunken)

        v1 = QWidget()
        vbox = QVBoxLayout(v1)
        vbox.addWidget(self.select_label)
        vbox.addWidget(self.disk_list)
        vbox.addWidget(self.scan_button)
        # vbox.addWidget(self.format_button)
        vbox.addWidget(h1_line)
        vbox.addWidget(self.Source_button)
        vbox.addWidget(self.Target_button)
        vbox.addWidget(h2_line)
        vbox.addWidget(self.progress_label)
        vbox.addWidget(self.progress_bar)
        vbox.addWidget(self.copy_and_verify_button)

        v2 = QWidget()
        v1box = QVBoxLayout(v2)

        self.termianal_label = QLabel('操作提示:', self)

        self.terminal = QTextEdit()
        v1box.addWidget(self.termianal_label)
        v1box.addWidget(self.terminal)


        splitter = QSplitter()
        splitter.addWidget(v1)
        splitter.addWidget(v2)
        
        

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(splitter)
        # self.setLayout(vbox)
        self.scan_button.clicked.connect(self.scan_disks)
        self.Source_button.clicked.connect(self.source_select)
        self.Target_button.clicked.connect(self.destination_select)
        self.copy_and_verify_button.clicked.connect(self.copy_)
        
        # self.copy_and_verify_button.clicked.connect(self.start_progress)

    def update_terminal(self, text):
        '''将文本更新到terminal中'''
        self.terminal.append(text)
    
    def get_disk_label(self, disk_name):
        try:
            result = subprocess.run(['lsblk', '-o', 'NAME,LABEL,MOUNTPOINT'], stdout=subprocess.PIPE, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:
                parts = re.split(r'\s{2,}', line)
                if len(parts) > 1:
                    name, label = parts[0], parts[1]
                    if disk_name in name:
                        return label if label else '没有卷名'
            return 'NONE'
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return None

    def get_disk_filesystem(self, disk_name):
        try:
            result = subprocess.run(['lsblk', '-o', 'NAME,FSTYPE'], stdout=subprocess.PIPE, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:
                parts = re.split(r'\s{2,}', line)
                if len(parts) > 1:
                    name, fstype = parts[0], parts[1]
                    if disk_name in name:
                        return fstype if fstype else '无文件系统'
            return '无文件系统'
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return None

    def get_mount_point(self, disk_name):
        try:
            result = subprocess.run(['lsblk', '-o', 'NAME,MOUNTPOINT'], stdout=subprocess.PIPE, text=True, check=True)
            lines = result.stdout.strip().split('\n')

            for line in lines[1:]:
                # 移除行中的图形字符
                clean_line = re.sub(r'[^a-zA-Z0-9/\-\s]', '', line)
                parts = clean_line.split()

                if len(parts) > 1:
                    name, mountpoint = parts[0], parts[1]
                    # 检查名称是否匹配
                    if name == disk_name:
                        return mountpoint if mountpoint else '未挂载'

            return '磁盘不存在'
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return None
    
    def check_mount_point(self, disk_name):
        if self.get_mount_point(disk_name) == '未挂载':
            return '未挂载'
        elif self.get_mount_point(disk_name) == '磁盘不存在':
            return '未挂载'
        elif self.get_mount_point(disk_name) == None:
            return '未挂载'
        else:
            return '已挂载'
            
    def get_disk_info(self):
        result = subprocess.run(['lsblk', '-J'], stdout=subprocess.PIPE)
        lsblk_output = json.loads(result.stdout)

        disks = []

        def process_device(device):
            disk_info = [
                device['name'],
                self.get_disk_label(device['name']),
                self.get_disk_filesystem(device['name']),
                device['size'],
                self.check_mount_point(device['name'])
            ]
            disks.append(disk_info)
            for child in device.get('children', []):
                process_device(child)

        for device in lsblk_output['blockdevices']:
            process_device(device)

        return disks

    def filter_disks(self, disks):
        pattern = re.compile(r'sd[a-z](\d+)?$')

        filtered_disks = []
        for disk in disks:
            if pattern.match(disk[0]):
                filtered_disks.append(disk)

        return filtered_disks

    def scan_disks(self):
        '''扫描连接的磁盘并添加值QTGui'''
        self.model.clear()
        self.model.setHorizontalHeaderLabels([
            "磁盘名称",
            "卷名",
            "文件系统",   
            "磁盘大小",
            "是否挂载"
        ])
        self.disk_list.setSelectionMode(QAbstractItemView.MultiSelection)

        disk_info = self.get_disk_info()
        filtered_disk_info = self.filter_disks(disk_info)
        if filtered_disk_info == []:
            self.update_terminal("没有连接磁盘,或Linux无法挂载当前磁盘的文件系统.请尝试格式化")

        for disk in filtered_disk_info:
            item_Name = QStandardItem(disk[0])
            item_Volumename = QStandardItem(disk[1])
            item_Filesystem = QStandardItem(disk[2])
            item_size = QStandardItem(disk[3])
            item_Mount = QStandardItem(disk[4])
                 
            self.model.appendRow([
                item_Name,
                item_Volumename,
                item_Filesystem, 
                item_size,
                item_Mount
            ])

    def source_select(self):
        '''选择需要拷贝的目录'''
        global source_dir
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            # self.pathLabel.setText(folder_path)
            source_dir = folder_path
        else:
            pass

    def destination_select(self):
        '''选择目标目录'''
        global destination_dir
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            # self.pathLabel.setText(folder_path)
            destination_dir = folder_path
        else:
            pass
           
    def target_select(self):
        '''将选中的磁盘作为目标路径'''
        global destination_dir
        selected_indexes = self.disk_list.selectedIndexes()
        selected_disks = []

        for index in selected_indexes:
            if index.column() == 0: 
                disk_name = self.model.itemFromIndex(index).text()
                disk_name = self.get_mount_point(disk_name)
                selected_disks.append(disk_name)

        if destination_dir != "":
            selected_disks = []
            selected_disks.append(destination_dir)

        return selected_disks

    def copy_Thread(self, source, select_disks):
        for dir in select_disks:
            self.copy_thread = CopyThread(source, dir)
            self.copy_thread.update_terminal_signal.connect(self.update_terminal)
            self.copy_thread.start()

    def copy_(self):
        '''开始拷贝的父函数，处理一些信息'''
        global source_dir
        dirs = self.target_select()
        if source_dir:
            source_path = source_dir
        else:
            self.source_select()
            source_path = source_dir

        if dirs == []:
            self.update_terminal("没有选择拷贝磁盘，单选/多选磁盘框中的磁盘或是选择拷贝路径")
            return

        self.copy_Thread(source_path, dirs)


class CopyThread(QThread):
    update_terminal_signal = pyqtSignal(str)

    def __init__(self, source, destination):
        super().__init__()
        self.source = source
        self.destination = destination

    def run(self):
    # 在这里执行复制操作
        try:
            # 运行 rsync 命令
            self.update_terminal_signal.emit(f"开始复制: {self.source} 到 {self.destination}")
            process = subprocess.run(['rsync', '-avrchELP', self.source, self.destination], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if process.returncode != 0:
                # 如果 rsync 返回错误码，打印错误信息并返回
                error_msg = f"rsync 失败，错误码: {process.returncode}, 错误信息: {process.stderr.decode('utf-8')}"
                self.update_terminal_signal.emit(error_msg)
                return
            elif process.returncode == 0:
                self.update_terminal_signal.emit("拷贝完成，正在校验...")

            # 如果 rsync 成功，继续后续操作
            destination_path = os.path.join(self.destination, os.path.basename(self.source))
            result = self.perform_md5_comparison(self.source, destination_path)
            self.update_terminal_signal.emit(result)

        except subprocess.CalledProcessError as e:
            # 捕获并处理 subprocess 运行时的错误
            self.update_terminal_signal.emit(f"拷贝过程中发生错误: {str(e)}")

    def get_all_file_paths(self, directory):
        file_paths = []
        for root, directories, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                file_paths.append(filepath)
        return file_paths

    def calculate_md5_of_files(self, file_paths):
        md5_values = {}
        for file_path in file_paths:
            md5_values[file_path] = self.calculate_md5(file_path)
        return md5_values

    def calculate_md5(self, file_path):
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        except IOError as e:
            return f"Error reading file {file_path}: {e}"

        return hash_md5.hexdigest()

    def compare_md5_values(self, source_md5, destination_md5, source_base_path, destination_base_path):
        mismatched_files = []
        missing_files = []

        for file_path, md5_value in source_md5.items():
            relative_path = os.path.relpath(file_path, start=source_base_path)
            dest_file_path = os.path.join(destination_base_path, relative_path)

            if dest_file_path not in destination_md5:
                missing_files.append(relative_path)
            elif md5_value != destination_md5[dest_file_path]:
                mismatched_files.append(relative_path)

        return mismatched_files, missing_files

    def perform_md5_comparison(self, source, destination):
        source_files = self.get_all_file_paths(source)
        destination_files = self.get_all_file_paths(destination)

        source_md5 = self.calculate_md5_of_files(source_files)
        destination_md5 = self.calculate_md5_of_files(destination_files)

        mismatched_files, missing_files = self.compare_md5_values(source_md5, destination_md5, source, destination)


        if not mismatched_files and not missing_files:
            return "所有文件MD5校验匹配。"
        else:
            result_message = "MD5校验不匹配或文件缺失。\n"
            if mismatched_files:
                result_message += "MD5不匹配的文件: " + ", ".join(mismatched_files) + "\n"
            if missing_files:
                result_message += "目标目录中缺失的文件: " + ", ".join(missing_files)
            return result_message


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DiskUtilityApp()
    ex.show()
    sys.exit(app.exec_())


