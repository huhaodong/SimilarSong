import os
import numpy as np
import joblib
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

def calculate_similarity(file_path, target_features):
    features = cached_features[file_path]
    distance = np.linalg.norm(target_features - features)
    return file_path, distance

def extract_features(file_path):
    y, sr = librosa.load(file_path, sr=None)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = np.mean(mfcc, axis=1)
    return mfcc_mean

def find_top_n_similar_audios(target_file, cache_file='audio_features.pkl', top_n=10):
    target_features = extract_features(target_file)
    
    # 从缓存中加载音频特征
    global cached_features
    cached_features = joblib.load(cache_file)

    with ProcessPoolExecutor() as executor:
        futures = []
        for file_path in cached_features.keys():
            futures.append(executor.submit(calculate_similarity, file_path, target_features))
        
        similarities = [future.result() for future in tqdm(futures, desc="Comparing files", unit="file")]
    
    # 排序找到相似度最小的前 N 个文件（距离最小意味着相似度最高）
    similarities.sort(key=lambda x: x[1])
    return similarities[:top_n]

# 示例用法: 查找最相似的文件
target_audio = "E:\\FILES\\WorkSpace\\music_work\\SunoAI\\樱花列车\\工程\\output\\樱花列车.mp3"  # 输入音频文件路径
cache_file='E:\\Program Files\\bb\\RealTracks\\Data\\Style Demos Audio\\audio_features.pkl' # 缓存文件路径
top_n_similar_files = find_top_n_similar_audios(target_audio, cache_file, top_n=10)

print("Top 10 most similar files:")
for file_path, similarity in top_n_similar_files:
    print(f"File: {file_path}, Similarity (distance): {similarity:.4f}")
