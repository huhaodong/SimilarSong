import os
import librosa
import numpy as np
import joblib
from tqdm import tqdm

def extract_features(file_path):
    y, sr = librosa.load(file_path, sr=None)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = np.mean(mfcc, axis=1)
    return mfcc_mean

def cache_audio_features(search_path, cache_file='audio_features.pkl'):
    audio_features = {}
    
    for root, _, files in os.walk(search_path):
        for file in tqdm(files, desc="Extracting features", unit="file"):
            if file.endswith(('.mp3', '.wav', '.flac', '.ogg', '.wma')):
                file_path = os.path.join(root, file)
                features = extract_features(file_path)
                audio_features[file_path] = features
    
    # 使用joblib缓存特征到文件
    joblib.dump(audio_features, cache_file)
    print(f"Cached features to {cache_file}")

# 示例用法: 预计算和缓存特征
search_directory = 'E:\\Program Files\\bb\\RealTracks\\Data\\Style Demos Audio'  # 搜索目录路径
cache_file = 'E:\\Program Files\\bb\\RealTracks\\Data\\Style Demos Audio\\audio_features.pkl'  # 缓存文件路径
cache_audio_features(search_directory, cache_file)
