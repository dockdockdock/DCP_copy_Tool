
import sys, os, platform, re
import subprocess, hashlib, threading
from PyQt5.QtCore import QTimer
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
system = platform.system()
source_dir = ""
destination_dir = ""

class DiskUtilityApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
     
    def init_ui(self):
        self.setWindowTitle('DCP-Tool-Win-v1.9')
        self.setGeometry(300,300,1000,600)

        self.select_label = QLabel('选择磁盘:', self)
        # self.progress_label = QLabel('目前进度:', self)

        self.disk_list = QTreeView(self)
        self.model = QStandardItemModel(self.disk_list)
        # self.model.setHorizontalHeaderLabels([            
        #     "磁盘名称",
        #     "卷名",
        #     "磁盘大小", 
        #     "磁盘描述", 
        #     "文件系统", 
        #     "剩余空间"
        # ])
        self.disk_list.setModel(self.model)
        self.scan_button = QPushButton('扫描磁盘',self)
        # self.format_button = QPushButton('格式化为NTFS',self)
        self.Source_button = QPushButton('文件路径',self)
        self.Target_button = QPushButton('拷贝路径',self)
        self.copy_and_verify_button = QPushButton('开始',self)
        # self.progress_bar = QProgressBar(self)

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
        # vbox.addWidget(self.progress_label)
        # vbox.addWidget(self.progress_bar)
        vbox.addWidget(self.copy_and_verify_button)

        v2 = QWidget()
        v1box = QVBoxLayout(v2)

        self.terminal = QTextEdit()
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

    def Byte2GBTB(self, size):
        ''' 将磁盘空间大小转换为可读的值 '''
        size_gb = size / (1024**3)
        if size_gb > 1000:
            size_tb = size_gb / 1024
            size_str = f"{size_tb:.2f} TB"
        else:
            size_str = f"{size_gb:.2f} GB"
        return(size_str)

    def scan_disks(self):
        '''扫描连接的磁盘并添加值QTGui'''
        self.model.clear()
        self.model.setHorizontalHeaderLabels([
            "磁盘名称",
            "卷名",
            "磁盘大小", 
            "磁盘描述", 
            "文件系统", 
            "剩余空间"           
        ])
        self.disk_list.setSelectionMode(QAbstractItemView.MultiSelection)
        command = "wmic logicaldisk get description,filesystem,freespace,name,size,volumename"
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
        lines = result.stdout.strip().split('\n')
        disks = lines[1:]

        for disk in disks:
            parts = re.split(r'\s{2,}', disk)
            if len(parts) >= 6:
                Description = parts[0]
                Filesystem = parts[1] if parts[1] else "无文件系统"
                freespace = int(parts[2]) if parts[4] else 0
                Name = parts[3]
                size = int(parts[4]) if parts[4] else 0
                Volumename = parts[5] if parts[5] else "无卷标"
                
                item_Description = QStandardItem(Description)
                item_Filesystem = QStandardItem(Filesystem)
                item_freespace = QStandardItem(str(self.Byte2GBTB(freespace)))
                item_Name = QStandardItem(Name)
                item_size = QStandardItem(str(self.Byte2GBTB(size)))
                item_Volumename = QStandardItem(Volumename)
                self.model.appendRow([
                    item_Volumename,
                    item_Name,
                    item_size,
                    item_Description, 
                    item_Filesystem, 
                    item_freespace, 
                ])
            else:
                continue

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
            if index.column() == 1: 
                disk_name = self.model.itemFromIndex(index).text()
                disk_name = disk_name + '\\'
                selected_disks.append(disk_name)

        if destination_dir is not None:
            selected_disks = []
            selected_disks.append(destination_dir)

        return selected_disks


    def copy_Thread(self, source, select_disks):
        '''根据选择磁盘的数量启动线程开始拷贝'''
        threads = []
        for dir in select_disks:
            thread = threading.Thread(target=self.copy, args=(source, dir))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        result = "所有拷贝操作完成，正在校验"
        self.update_terminal(result)


    def copy(self, source, destination):
        '''使用windows-robycopy进行拷贝'''
        destination = os.path.join(destination, os.path.basename(source))
        # subprocess.run(['robocopy', source, destination, '/MIR'], check=True)     #'/MIR'会删除目标目录中的文件，谨慎使用
        subprocess.run(['robocopy', source, destination, '/E'])

        # result = self.perform_md5_comparison(source, destination)
        # self.update_terminal(result)


    def copy_(self):
        '''开始拷贝的父函数，处理一些信息'''
        global source_dir
        dirs = self.target_select()
        if source_dir:
            source_path = source_dir
        else:
            source_path = self.source_select()
            source_dir = source_path
        # disk = ['C:\\copytest1', 'C:\\copytest2']
        self.copy_Thread(source_path, dirs)


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
    
    def update_terminal(self, text):
        '''将文本更新到terminal中'''
        self.terminal.append(text)

    
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



