import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import librosa
import numpy as np
import joblib
from concurrent.futures import ProcessPoolExecutor, as_completed
from tkinter.ttk import Progressbar

# 音频特征提取函数
def extract_features(file_path):
    y, sr = librosa.load(file_path, sr=None)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = np.mean(mfcc, axis=1)
    return mfcc_mean

# 特征缓存函数
def cache_audio_features(search_path, cache_file, progress_bar, progress_label):
    audio_features = {}
    total_files = sum([len(files) for _, _, files in os.walk(search_path) if files])
    current_progress = 0
    
    for root, _, files in os.walk(search_path):
        for file in files:
            if file.endswith(('.mp3', '.wav', '.flac', '.ogg', '.wma')):
                file_path = os.path.join(root, file)
                features = extract_features(file_path)
                audio_features[file_path] = features

                # 更新进度条
                current_progress += 1
                progress_bar['value'] = (current_progress / total_files) * 100
                progress_label.config(text=f"Extracting features: {current_progress}/{total_files} files")
                progress_bar.update()

    joblib.dump(audio_features, cache_file)
    messagebox.showinfo("Caching Complete", f"Cached features to {cache_file}")
    progress_label.config(text="Caching complete!")

# 相似音频查找函数
def find_top_n_similar_audios(target_file, cache_file, top_n, progress_bar, progress_label):
    target_features = extract_features(target_file)
    cached_features = joblib.load(cache_file)
    total_files = len(cached_features)
    current_progress = 0
    
    similarities = []
    with ProcessPoolExecutor() as executor:
        future_to_file = {executor.submit(calculate_similarity, file_path, target_features, features): file_path for file_path, features in cached_features.items()}
        
        for future in as_completed(future_to_file):
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
    
    # 排序并选择前 top_n 个文件
    similarities.sort(key=lambda x: x[1])
    return similarities[:top_n]

def calculate_similarity(file_path, target_features, features):
    distance = np.linalg.norm(target_features - features)
    return file_path, distance

# GUI 主界面
class AudioSimilarityApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Similarity Finder")
        self.geometry("500x400")

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

        # Result Display
        self.text_result = tk.Text(self, height=8, width=60)
        self.text_result.pack(pady=5)

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
        cache_file = filedialog.asksaveasfilename(defaultextension=".pkl", filetypes=[("Pickle Files", "*.pkl")], title="Save Cache File As")
        if not cache_file:
            return
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Starting feature extraction...")
        self.update()
        cache_audio_features(search_dir, cache_file, self.progress_bar, self.progress_label)

    def find_similar_audios(self):
        target_file = self.entry_target.get()
        if not target_file:
            messagebox.showwarning("Input Error", "Please select a target audio file.")
            return
        
        cache_file = filedialog.askopenfilename(title="Select Cache File", filetypes=[("Pickle Files", "*.pkl")])
        if not cache_file:
            return
        
        top_n = simpledialog.askinteger("Top N", "Enter the number of top similar files to find:", initialvalue=10, minvalue=1, maxvalue=100)
        if not top_n:
            return

        self.progress_bar['value'] = 0
        self.progress_label.config(text="Starting comparison...")
        self.update()
        
        top_n_similar_files = find_top_n_similar_audios(target_file, cache_file, top_n, self.progress_bar, self.progress_label)

        self.text_result.delete(1.0, tk.END)
        self.text_result.insert(tk.END, "Top similar files:\n")
        for file_path, similarity in top_n_similar_files:
            self.text_result.insert(tk.END, f"{file_path} - Similarity (distance): {similarity:.4f}\n")
        self.progress_label.config(text="Comparison complete!")

if __name__ == "__main__":
    app = AudioSimilarityApp()
    app.mainloop()
