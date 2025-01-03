import os
import pickle

class Settings(object):
    def __init__(self):
        # Be default, the home will be in the same folder as labelImg
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.data = {}
        self.path = os.path.join(current_directory, '.labelImgSettings.pkl')

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        if key in self.data:
            return self.data[key]
        return default

    def save(self):
        if self.path:
            with open(self.path, 'wb') as f:
                pickle.dump(self.data, f, pickle.HIGHEST_PROTOCOL)
                print(f"Settings successfully saved to {self.path}")
                return True
        return False

    def load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, 'rb') as f:
                    self.data = pickle.load(f)
                    print(f"Settings successfully loaded from {self.path}")
                    return True
        except (IOError, OSError) as e:
            print(f"Error loading settings: {e}. Resetting to defaults.")
            self.reset()
        return False

    def reset(self):
        if os.path.exists(self.path):
            os.remove(self.path)
            print('Remove setting pkl file ${0}'.format(self.path))
        self.data = {}
        self.path = None
