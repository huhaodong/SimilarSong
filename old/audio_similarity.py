import librosa
import numpy as np
import os
import pickle

def extract_features(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        return {
            'mfcc': mfcc_mean,
            'chroma': chroma_mean
        }
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def cache_features(audio_files, cache_file_path):
    features_cache = {}
    for file_path in audio_files:
        features = extract_features(file_path)
        if features is not None:
            features_cache[file_path] = features
    
    with open(cache_file_path, 'wb') as f:
        pickle.dump(features_cache, f)

def load_features_cache(cache_file_path):
    if os.path.exists(cache_file_path):
        with open(cache_file_path, 'rb') as f:
            return pickle.load(f)
    return {}

def calculate_similarity(features1, features2):
    similarity_scores = []
    for feature in ['mfcc', 'chroma']:
        if feature in features1 and feature in features2:
            distance = np.linalg.norm(features1[feature] - features2[feature])
            similarity_scores.append(distance)
    
    if similarity_scores:
        return np.mean(similarity_scores)
    else:
        return float('inf')

def find_top_n_similar_audios(target_file, audio_files, top_n, cache_file_path):
    target_features = extract_features(target_file)
    if target_features is None:
        return []
    
    features_cache = load_features_cache(cache_file_path)
    similarities = []
    
    for file_path in audio_files:
        features = features_cache.get(file_path) or extract_features(file_path)
        if features is not None:
            similarity = calculate_similarity(features, target_features)
            similarities.append((file_path, similarity))
    
    similarities.sort(key=lambda x: x[1])
    return similarities[:top_n]
