# feature_manager.py

import os
import joblib

class FeatureManager:
    def __init__(self):
        self.feature_file = None

    def set_feature_file(self, feature_file_path):
        self.feature_file = feature_file_path

    def get_feature_file(self):
        if self.feature_file is None or not os.path.exists(self.feature_file):
            raise FileNotFoundError("Feature file is not set or does not exist.")
        return self.feature_file

    def load_features(self):
        feature_file = self.get_feature_file()
        return joblib.load(feature_file)

    def save_features(self, features):
        if self.feature_file is None:
            raise FileNotFoundError("Feature file is not set.")
        joblib.dump(features, self.feature_file)

# 初始化一个 FeatureManager 实例
feature_manager_instance = FeatureManager()
