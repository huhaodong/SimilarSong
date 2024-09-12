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
def find_top_n_similar_audios(target_file, top_n, progress_bar, progress_label, stop_event):
    target_features = extract_features(target_file, stop_event)
    if target_features is None:
        return []
    
    cached_features = feature_manager_instance.load_features()
    total_files = len(cached_features)
    current_progress = 0
    
    similarities = []
    with ProcessPoolExecutor(max_workers=15) as executor:
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
        self.geometry("500x680")

        # 任务取消事件
        self.stop_event = threading.Event()

        # Target Audio File Selection
        self.label_target = tk.Label(self, text="Target Audio File:")
        self.label_target.pack(pady=5)
        self.entry_target = tk.Entry(self, width=50)
        self.entry_target.pack(pady=5)
        self.button_browse_target = tk.Button(self, text="Browse", command=self.browse_target)
        self.button_browse_target.pack(pady=5)

        # Search Directory Selection
        self.label_dir = tk.Label(self, text="Search Directory:")
        self.label_dir.pack(pady=5)
        self.entry_dir = tk.Entry(self, width=50)
        self.entry_dir.pack(pady=5)
        self.button_browse_dir = tk.Button(self, text="Browse", command=self.browse_directory)
        self.button_browse_dir.pack(pady=5)

        # Progress Bar and Label
        self.progress_label = tk.Label(self, text="")
        self.progress_label.pack(pady=5)
        self.progress_bar = Progressbar(self, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress_bar.pack(pady=5)

        # Cache Features Button
        self.button_cache = tk.Button(self, text="Cache Audio Features", command=self.cache_features)
        self.button_cache.pack(pady=10)

        # Find Similar Audios Button
        self.button_find = tk.Button(self, text="Find Similar Audios", command=self.find_similar_audios)
        self.button_find.pack(pady=10)

        # Cancel Task Button
        self.button_cancel = tk.Button(self, text="Cancel Task", command=self.cancel_task)
        self.button_cancel.pack(pady=10)

        # Set Feature File Button
        self.button_set_feature_file = tk.Button(self, text="Set Feature File", command=self.set_feature_file)
        self.button_set_feature_file.pack(pady=10)

        # Feature File Display
        self.label_feature_file = tk.Label(self, text="Current Feature File: Not set")
        self.label_feature_file.pack(pady=5)

        # Result Display
        self.listbox_result = tk.Listbox(self, height=8, width=60)
        self.listbox_result.pack(pady=5)
        self.listbox_result.bind("<Double-1>", self.play_audio)
        self.listbox_result.bind("<Button-3>", self.show_context_menu)  # 右键点击事件

        # 创建右键菜单
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Copy File Name", command=self.copy_file_name)

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

        top_n = simpledialog.askinteger("Top N", "Enter the number of top similar files to find:", initialvalue=10, minvalue=1, maxvalue=100)
        if not top_n:
            return

        self.stop_event.clear()
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Starting audio comparison...")
        self.update()

        # 使用线程来执行音频匹配任务
        threading.Thread(target=self.find_similar_audios_in_thread, args=(target_file, top_n)).start()

    def find_similar_audios_in_thread(self, target_file, top_n):
        similarities = find_top_n_similar_audios(target_file, top_n, self.progress_bar, self.progress_label, self.stop_event)
        self.run_find_similar_continue(similarities)

    def run_find_similar_continue(self, top_n_similar_files):
        if not top_n_similar_files:
            self.progress_label.config(text="No similar files found.")
            return

        self.listbox_result.delete(0, tk.END)
        count = 1
        for file_path, similarity in top_n_similar_files:
            file_name = os.path.basename(file_path)  # 只显示文件名
            self.listbox_result.insert(tk.END, f"[{count}] {file_name} - Distence: {similarity:.4f}")
            self.listbox_result.insert(tk.END, file_path)  # 隐藏文件路径，用于打开文件
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

