import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter.ttk import Progressbar
import librosa
import numpy as np
import joblib
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed
import soundfile as sf
import subprocess
import platform
from scipy.spatial.distance import euclidean, cosine
from feature_manager_gai import feature_manager_instance  # 导入 FeatureManager 实例
import multiprocessing

# 音频特征提取函数
def extract_features(file_path, stop_event):
    try:
        y, sr = librosa.load(file_path, sr=None)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        # tempo = librosa.beat.tempo(y=y, sr=sr)[0]
        return {
            'mfcc': mfcc_mean,
            'chroma': chroma_mean
        }
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None
    
# 特征缓存函数
def cache_audio_features(search_path, feature_file, progress_bar, progress_label, stop_event):
    audio_features = {}
    total_files = sum([len(files) for _, _, files in os.walk(search_path) if files])
    current_progress = 0
    
    for root, _, files in os.walk(search_path):
        if stop_event.is_set():
            break
        for file in files:
            if stop_event.is_set():
                break
            if file.endswith(('.mp3', '.wav', '.flac', '.ogg', '.wma')):
                file_path = os.path.join(root, file)
                features = extract_features(file_path, stop_event)
                if features is not None:
                    audio_features[file_path] = features

                # 更新进度条
                current_progress += 1
                progress_bar['value'] = (current_progress / total_files) * 100
                progress_label.config(text=f"Extracting features: {current_progress}/{total_files} files")
                progress_bar.update()
    
    if not stop_event.is_set():
        feature_manager_instance.set_feature_file(feature_file)
        feature_manager_instance.save_features(audio_features)
        messagebox.showinfo("Caching Complete", f"Cached features to {feature_file}")
        progress_label.config(text="Caching complete!")
    else:
        progress_label.config(text="Task cancelled!")

# 相似音频查找函数
def find_top_n_similar_audios(target_file, top_n, progress_bar, progress_label, stop_event, th_n):
    target_features = extract_features(target_file, stop_event)
    if target_features is None:
        return []
    
    cached_features = feature_manager_instance.load_features()
    total_files = len(cached_features)
    current_progress = 0
    
    similarities = []
    with ProcessPoolExecutor(max_workers=th_n) as executor:
        future_to_file = {executor.submit(calculate_similarity, file_path, target_features, features): file_path for file_path, features in cached_features.items()}
        
        for future in as_completed(future_to_file):
            if stop_event.is_set():
                break
            file_path = future_to_file[future]
            try:
                result = future.result()
                similarities.append(result)
            except Exception as exc:
                print(f'{file_path} generated an exception: {exc}')
            finally:
                # 更新进度条
                current_progress += 1
                progress_bar['value'] = (current_progress / total_files) * 100
                progress_label.config(text=f"Comparing files: {current_progress}/{total_files} files")
                progress_bar.update()

    if not stop_event.is_set():
        similarities.sort(key=lambda x: x[1])
        return similarities[:top_n]
    else:
        progress_label.config(text="Task cancelled!")
        return []

def calculate_similarity(file_path, target_features, features):
    target_mix = []
    source_mix = []
    similarity_scores = [] # 
    for feature in ['mfcc', 'chroma']:
        if feature in target_features and feature in features:
            # distance = np.linalg.norm(target_features[feature] - features[feature])
            distance = abs(1/(1 - cosine(target_features[feature], features[feature])))
            similarity_scores.append(distance)
    
    if similarity_scores:
        return file_path, np.mean(similarity_scores)
    else:
        return file_path, float('inf')

# 打开文件的函数
def open_audio_file(file_path):
    if platform.system() == "Windows":
        os.startfile(file_path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.call(["open", file_path])
    else:  # Linux
        subprocess.call(["xdg-open", file_path])

# 复制到剪贴板函数
def copy_to_clipboard(text):
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()  # 刷新剪贴板
    root.destroy()  # 关闭窗口

# GUI 主界面
class AudioSimilarityApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Similarity Finder")
        self.geometry("550x780")

        # 任务取消事件
        self.stop_event = threading.Event()

        # Target Audio File Selection
        self.label_target = tk.Label(self, text="需要寻找的文件:")
        # self.label_target.grid(row=0, column=0, sticky=tk.N)
        self.label_target.pack(pady=5)
        self.entry_target = tk.Entry(self, width=50)
        # self.entry_target.grid(row=1, column=0, sticky=tk.N)
        self.entry_target.pack(pady=5)
        self.button_browse_target = tk.Button(self, text="选择文件", command=self.browse_target)
        # self.button_browse_target.grid(row=1, column=1, sticky=tk.N)
        self.button_browse_target.pack(pady=5)

        # Search Directory Selection
        self.label_dir = tk.Label(self, text="需要提取的文件夹根目录:")
        # self.label_dir.grid(row=2, column=0, sticky=tk.N)
        self.label_dir.pack(pady=5)
        self.entry_dir = tk.Entry(self, width=50)
        # self.entry_dir.grid(row=3, column=0, sticky=tk.N)
        self.entry_dir.pack(pady=5)
        self.button_browse_dir = tk.Button(self, text="选择目录", command=self.browse_directory)
        # self.button_browse_dir.grid(row=3, column=1, sticky=tk.N)
        self.button_browse_dir.pack(pady=5)

        # Progress Bar and Label
        self.progress_label = tk.Label(self, text="待机中")
        # self.progress_label.grid(row=4, column=0, columnspan=3, sticky=tk.N)
        self.progress_label.pack(pady=5)
        self.progress_bar = Progressbar(self, orient=tk.HORIZONTAL, length=400, mode='determinate')
        # self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=tk.N)
        self.progress_bar.pack(pady=5)

        # Cache Features Button
        self.button_cache = tk.Button(self, text="特征提取", command=self.cache_features)
        # self.button_cache.grid(row=6, column=0, columnspan=3, sticky=tk.N)
        self.button_cache.pack(pady=5)

        # Find Similar Audios Button
        self.button_find = tk.Button(self, text="寻找相似音频", command=self.find_similar_audios)
        # self.button_find.grid(row=7, column=0, columnspan=3, sticky=tk.N)
        self.button_find.pack(pady=5)

        # Cancel Task Button
        self.button_cancel = tk.Button(self, text="取消", command=self.cancel_task)
        # self.button_cancel.grid(row=8, column=0, columnspan=3, sticky=tk.N)
        self.button_cancel.pack(pady=5)

        # Set Feature File Button
        self.button_set_feature_file = tk.Button(self, text="设置特征文件", command=self.set_feature_file)
        # self.button_set_feature_file.grid(row=9, column=0, columnspan=3, sticky=tk.N)
        self.button_set_feature_file.pack(pady=5)

        # 替换根文件夹路径按钮
        self.button_set_root_path = tk.Button(self, text="设置替换的目标路径", command=self.select_new_root_path)
        # self.button_set_root_path.grid(row=10, column=0, columnspan=3, sticky=tk.N)
        self.button_set_root_path.pack(pady=5)

        # 选择原路径根目录文件夹
        self.button_set_root_name = tk.Button(self, text="设置源路径根目录名", command=self.select_new_root_name)
        # self.button_set_root_name.grid(row=11, column=0, columnspan=3, sticky=tk.N)
        self.button_set_root_name.pack(pady=5)

        # 当前替换路径
        self.label_current_new_folder_path = tk.Label(self, text=f"当前替换的目标路径: {feature_manager_instance.new_folder_path}")
        # self.label_current_new_folder_path.grid(row=12, column=0, columnspan=3, sticky=tk.N)
        self.label_current_new_folder_path.pack(pady=5)

        # 当前替换路径根目录
        self.label_current_root_name = tk.Label(self, text=f"需要替换的旧路径的根目录 : {feature_manager_instance.new_root_name}")
        # self.label_current_root_name.grid(row=13, column=0, columnspan=3, sticky=tk.N)
        self.label_current_root_name.pack(pady=5)

        # Feature File Display
        self.label_feature_file = tk.Label(self, text="当前使用的特征文件: Not set")
        # self.label_feature_file.grid(row=14, column=0, columnspan=3, sticky=tk.N)
        self.label_feature_file.pack(pady=5)

        # Result Display
        self.listbox_result = tk.Listbox(self, height=8, width=60)
        # self.listbox_result.grid(row=15, column=0, columnspan=3, sticky=tk.N)
        self.listbox_result.pack(pady=5)
        self.listbox_result.bind("<Double-1>", self.play_audio)
        self.listbox_result.bind("<Button-3>", self.show_context_menu)  # 右键点击事件

        # 创建右键菜单
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="复制", command=self.copy_file_name)

    # 选择需要替换的路径
    def select_new_root_path(self):
        folder_selected = filedialog.askdirectory()
        feature_manager_instance.save_new_folder_path_settings(folder_path=folder_selected)
        self.label_current_new_folder_path.config(text=f"当前替换的目标路径: {folder_selected}")
    
    # 选择原路径上的根目录名称
    def select_new_root_name(self):
        root_name = simpledialog.askstring("根目录名称", "输入旧路径中的根目录名称:")
        feature_manager_instance.save_root_name_settings(root_name=root_name)
        self.label_current_root_name.config(text=f"需要替换的旧路径的根目录 : {root_name}")

    def browse_target(self):
        target_file = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.flac *.ogg")])
        self.entry_target.delete(0, tk.END)
        self.entry_target.insert(0, target_file)

    def browse_directory(self):
        search_dir = filedialog.askdirectory()
        self.entry_dir.delete(0, tk.END)
        self.entry_dir.insert(0, search_dir)

    def cache_features(self):
        search_dir = self.entry_dir.get()
        if not search_dir:
            messagebox.showwarning("Input Error", "Please select a search directory.")
            return
        
        feature_file = filedialog.asksaveasfilename(defaultextension=".pkl", filetypes=[("Pickle Files", "*.pkl")])
        if not feature_file:
            messagebox.showwarning("Input Error", "Please specify the path to save the feature file.")
            return

        self.stop_event.clear()
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Starting feature extraction...")
        self.update()

        # 使用线程来执行特征提取任务
        threading.Thread(target=cache_audio_features, args=(search_dir, feature_file, self.progress_bar, self.progress_label, self.stop_event)).start()

    def find_similar_audios(self):
        target_file = self.entry_target.get()
        if not target_file:
            messagebox.showwarning("Input Error", "Please select a target audio file.")
            return
        
        if feature_manager_instance.feature_file is None:
            feature_file = filedialog.askopenfilename(filetypes=[("Pickle Files", "*.pkl")])
            if not feature_file:
                messagebox.showwarning("Input Error", "Please specify the feature file.")
                return
            feature_manager_instance.set_feature_file(feature_file)

        self.label_feature_file.config(text=f"Current Feature File: {feature_manager_instance.get_feature_file()}")

        top_n = simpledialog.askinteger("最相似的n个结果", "输入需要列出多少个相似结果:", initialvalue=10, minvalue=1, maxvalue=100)
        if not top_n:
            return
        
        # 设置线程个数
        th_n = simpledialog.askinteger("线程数", "输入线程个数:", initialvalue=15, minvalue=1, maxvalue=100)
        if not th_n:
            th_n = 15

        self.stop_event.clear()
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Starting audio comparison...")
        self.update()

        # 使用线程来执行音频匹配任务
        threading.Thread(target=self.find_similar_audios_in_thread, args=(target_file, top_n, th_n)).start()

    def find_similar_audios_in_thread(self, target_file, top_n, th_n):
        similarities = find_top_n_similar_audios(target_file, top_n, self.progress_bar, self.progress_label, self.stop_event, th_n)
        self.run_find_similar_continue(similarities)

    # 将原本的路径进行替换
    def remap_paths(self, path):
        # 获取用户输入的路径、原始根文件夹名称以及新的根路径
        old_path = path
        root_folder_name = feature_manager_instance.new_root_name
        new_root_path = feature_manager_instance.new_folder_path

        # 校验用户输入
        if new_root_path == "" or root_folder_name == "":
            print("没有设置替换路径或根文件夹名称")
            return path

        if not old_path or not root_folder_name or not new_root_path:
            print("输入错误", "请确保所有输入框已填写完整并选择了新的根路径")
            return path

        # 处理输入路径，将 Windows 风格路径转换为 macOS/Linux 风格路径
        old_path = feature_manager_instance.convert_path_for_platform(old_path)

        # 检查输入的路径是否包含指定的根文件夹名称
        if root_folder_name not in old_path:
            print("路径错误", "指定的根文件夹名称不在输入的路径中")
            return path

        try:
            # 替换路径中的根文件夹为新的路径
            index = old_path.index(root_folder_name)
            new_path = os.path.join(new_root_path, old_path[index + len(root_folder_name):].lstrip(os.sep))

            # 根据当前平台，调整新路径的格式
            new_path = feature_manager_instance.convert_path_for_platform(new_path)

            # 保存当前设置
            # save_settings(root_folder_name, new_root_path)

            # 更新当前设置显示
            # update_current_settings()

            # 显示重映射后的路径
            # messagebox.showinfo("重映射成功", f"原路径:\n{old_path}\n\n新路径:\n{new_path}")
        except Exception as e:
            print("错误", f"发生错误: {str(e)}")

        return new_path

    def run_find_similar_continue(self, top_n_similar_files):
        if not top_n_similar_files:
            self.progress_label.config(text="No similar files found.")
            return

        target_file = self.entry_target.get() # 原曲路径

        self.listbox_result.delete(0, tk.END)

        source_path = self.remap_paths(target_file)
        file_name = os.path.basename(source_path)  # 只显示文件名
        self.listbox_result.insert(tk.END, f">>> 双击我试听原音频 - {file_name}")
        self.listbox_result.insert(tk.END, source_path)  # 隐藏文件路径，用于打开文件
        self.listbox_result.itemconfig(tk.END, {'foreground': 'white'})  # 隐藏文本
        
        count = 1
        for file_path, similarity in top_n_similar_files:
            new_path = self.remap_paths(file_path)
            file_name = os.path.basename(new_path)  # 只显示文件名
            self.listbox_result.insert(tk.END, f"[{count}] {file_name} - Distence: {similarity:.4f}")
            self.listbox_result.insert(tk.END, new_path)  # 隐藏文件路径，用于打开文件
            self.listbox_result.itemconfig(tk.END, {'foreground': 'white'})  # 隐藏文本
            count += 1

        self.progress_label.config(text="Comparison complete!")

    def cancel_task(self):
        self.stop_event.set()
        self.progress_label.config(text="Cancelling task...")

    def play_audio(self, event):
        selected_item = self.listbox_result.curselection()
        if selected_item:
            file_path_index = selected_item[0] + 1  # 获取隐藏的路径行
            if "Distence" in self.listbox_result.get(selected_item):  # 确保选择的是显示相似度的行
                file_path = self.listbox_result.get(file_path_index)
                open_audio_file(file_path)
            elif ">>> 双击我试听原音频" in self.listbox_result.get(selected_item):
                file_path = self.listbox_result.get(file_path_index)
                open_audio_file(file_path)

    def set_feature_file(self):
        feature_file = filedialog.askopenfilename(defaultextension=".pkl", filetypes=[("Pickle Files", "*.pkl")])
        if feature_file:
            feature_manager_instance.set_feature_file(feature_file)
            self.label_feature_file.config(text=f"Current Feature File: {feature_file}")
            messagebox.showinfo("Feature File Set", f"Feature file set to {feature_file}")

    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def copy_file_name(self):
        selected_item = self.listbox_result.get(self.listbox_result.curselection())
        if selected_item.startswith('['):
            file_name = selected_item.split(" - ")[0]
            file_name = file_name.split('.')[0]
            file_name = file_name.split(']')[1].strip()
        else:
            file_name = selected_item
        copy_to_clipboard(file_name)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = AudioSimilarityApp()
    app.mainloop()

