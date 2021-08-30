class Settings:

    def __init__(self, addon):
        self.addon = addon

    def get(self, id):
        return self.addon.getSetting(id)

    def set(self, id, value):
        return self.addon.setSetting(id, value)