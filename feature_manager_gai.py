import joblib
import json
import os

class FeatureManager:
    def __init__(self):
        self.feature_file = None
        self.setting_file = 'path_mappings.json'
        self.new_folder_path = self.load_folder_path_settings()
        self.new_root_name = self.load_root_name_settings()

    # 加载持久化设置
    def load_settings(self):
        if os.path.exists(self.setting_file):
            with open(self.setting_file, 'r') as f:
                return json.load(f)
        return {}
    
    # 加载持久化的路径设置
    def load_folder_path_settings(self):
        map = self.load_settings()
        return map.get('new_root_path',"")
    
    # 加载持久化的根目录设置
    def load_root_name_settings(self):
        map = self.load_settings()
        return map.get('root_folder_name',"")

    # 保存持久化设置
    def save_settings(self, root_name, new_root):
        settings = {"root_folder_name": root_name, "new_root_path": new_root}
        with open(self.setting_file, 'w') as f:
            json.dump(settings, f)

    # 保存持久化根目录名称设置
    def save_root_name_settings(self, root_name):
        self.new_root_name = root_name
        settings = {"root_folder_name": root_name, "new_root_path": self.new_folder_path}
        with open(self.setting_file, 'w') as f:
            json.dump(settings, f)

    # 保存持久化替换路径设置
    def save_new_folder_path_settings(self, folder_path):
        self.new_folder_path = folder_path
        settings = {"root_folder_name": self.new_root_name, "new_root_path": folder_path}
        with open(self.setting_file, 'w') as f:
            json.dump(settings, f)

    # 将 Windows 风格路径转换为 macOS/Linux 风格路径
    def convert_to_unix_path(self, path):
        return path.replace('\\', '/')

    # 将 macOS/Linux 风格路径转换为 Windows 风格路径
    def convert_to_windows_path(self, path):
        return path.replace('/', '\\')

    # 判断当前系统类型并执行路径格式转换
    def convert_path_for_platform(self, path):
        if os.name == 'posix':  # macOS 或 Linux
            return self.convert_to_unix_path(path)
        elif os.name == 'nt':  # Windows
            return self.convert_to_windows_path(path)
        return path
    
    # 重映射函数：替换路径中的根文件夹部分
    def remap_paths(self, old_path, root_folder_name, new_root_path):

        # 校验用户输入
        if not old_path or not root_folder_name or not new_root_path:
            print("输入错误", "请确保所有输入框已填写完整并选择了新的根路径")
            return

        # 处理输入路径，将 Windows 风格路径转换为 macOS/Linux 风格路径
        old_path = self.convert_path_for_platform(old_path)

        # 检查输入的路径是否包含指定的根文件夹名称
        if root_folder_name not in old_path:
            print("路径错误", "指定的根文件夹名称不在输入的路径中")
            return

        try:
            # 替换路径中的根文件夹为新的路径
            index = old_path.index(root_folder_name)
            new_path = os.path.join(new_root_path, old_path[index + len(root_folder_name):].lstrip(os.sep))

            # 根据当前平台，调整新路径的格式
            new_path = self.convert_path_for_platform(new_path)

            # 保存当前设置
            # self.save_settings(root_folder_name, new_root_path)

            # 更新当前设置显示
            # update_current_settings()

            # 显示重映射后的路径
            print("重映射成功", f"原路径:\n{old_path}\n\n新路径:\n{new_path}")
        except Exception as e:
            print("错误", f"发生错误: {str(e)}")

    def set_feature_file(self, feature_file):
        self.feature_file = feature_file

    def get_feature_file(self):
        return self.feature_file

    def save_features(self, features):
        if self.feature_file is not None:
            joblib.dump(features, self.feature_file)

    def load_features(self):
        if self.feature_file is not None and os.path.exists(self.feature_file):
            return joblib.load(self.feature_file)
        return {}

feature_manager_instance = FeatureManager()
