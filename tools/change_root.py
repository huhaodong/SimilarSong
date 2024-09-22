import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox

# 持久化文件路径
SETTINGS_FILE = "path_mappings.json"

# 加载持久化设置
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

# 保存持久化设置
def save_settings(root_name, new_root):
    settings = {"root_folder_name": root_name, "new_root_path": new_root}
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

# 更新界面上的当前设置
def update_current_settings():
    root_name = entry_root.get().strip()
    new_root = new_root_folder.get()
    label_current_settings.config(text=f"当前设置：\n根目录名称: {root_name}\n新根目录: {new_root}")

# 将 Windows 风格路径转换为 macOS/Linux 风格路径
def convert_to_unix_path(path):
    return path.replace('\\', '/')

# 将 macOS/Linux 风格路径转换为 Windows 风格路径
def convert_to_windows_path(path):
    return path.replace('/', '\\')

# 判断当前系统类型并执行路径格式转换
def convert_path_for_platform(path):
    if os.name == 'posix':  # macOS 或 Linux
        return convert_to_unix_path(path)
    elif os.name == 'nt':  # Windows
        return convert_to_windows_path(path)
    return path

# 重映射函数：替换路径中的根文件夹部分
def remap_paths():
    # 获取用户输入的路径、原始根文件夹名称以及新的根路径
    old_path = entry_path.get().strip()
    root_folder_name = entry_root.get().strip()
    new_root_path = new_root_folder.get()

    # 校验用户输入
    if not old_path or not root_folder_name or not new_root_path:
        messagebox.showerror("输入错误", "请确保所有输入框已填写完整并选择了新的根路径")
        return

    # 处理输入路径，将 Windows 风格路径转换为 macOS/Linux 风格路径
    old_path = convert_path_for_platform(old_path)

    # 检查输入的路径是否包含指定的根文件夹名称
    if root_folder_name not in old_path:
        messagebox.showerror("路径错误", "指定的根文件夹名称不在输入的路径中")
        return

    try:
        # 替换路径中的根文件夹为新的路径
        index = old_path.index(root_folder_name)
        new_path = os.path.join(new_root_path, old_path[index + len(root_folder_name):].lstrip(os.sep))

        # 根据当前平台，调整新路径的格式
        new_path = convert_path_for_platform(new_path)

        # 保存当前设置
        save_settings(root_folder_name, new_root_path)

        # 更新当前设置显示
        update_current_settings()

        # 显示重映射后的路径
        messagebox.showinfo("重映射成功", f"原路径:\n{old_path}\n\n新路径:\n{new_path}")
    except Exception as e:
        messagebox.showerror("错误", f"发生错误: {str(e)}")

# 文件夹选择器函数
def select_new_root_folder():
    folder_selected = filedialog.askdirectory()
    new_root_folder.set(folder_selected)

# 创建主窗口
root = tk.Tk()
root.title("跨平台文件路径重映射工具")

# 加载已保存的设置
settings = load_settings()
root_folder_name_saved = settings.get("root_folder_name", "")
new_root_path_saved = settings.get("new_root_path", "")

# 创建用于输入原路径的框
tk.Label(root, text="输入需要重映射的文件路径:").grid(row=0, column=0, sticky=tk.W)
entry_path = tk.Entry(root, width=50)
entry_path.grid(row=0, column=1)

# 创建用于输入根文件夹名称的框
tk.Label(root, text="输入原路径中的根文件夹名称:").grid(row=1, column=0, sticky=tk.W)
entry_root = tk.Entry(root, width=50)
entry_root.grid(row=1, column=1)
entry_root.insert(0, root_folder_name_saved)  # 自动填入已保存的根文件夹名称

# 用于显示选择的新根文件夹路径
new_root_folder = tk.StringVar(value=new_root_path_saved)  # 自动填入已保存的新根文件夹路径
tk.Label(root, text="选择新的根文件夹路径:").grid(row=2, column=0, sticky=tk.W)
tk.Entry(root, textvariable=new_root_folder, width=50, state='readonly').grid(row=2, column=1)

# 创建按钮选择新的根文件夹路径
btn_select_folder = tk.Button(root, text="选择文件夹", command=select_new_root_folder)
btn_select_folder.grid(row=2, column=2)

# 创建按钮进行路径替换
btn_remap = tk.Button(root, text="开始替换", command=remap_paths)
btn_remap.grid(row=3, column=1, columnspan=2)

# 显示当前设置
label_current_settings = tk.Label(root, text=f"当前设置：\n根目录名称: {root_folder_name_saved}\n新根目录: {new_root_path_saved}")
label_current_settings.grid(row=4, column=0, columnspan=3)

# 运行主窗口
root.mainloop()
