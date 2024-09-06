import joblib
import os

class FeatureManager:
    def __init__(self):
        self.feature_file = None

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
