# Contains a character profile
class Character:
    name : str
    system : str
    icon : str
    channels : list[str]
    reminders : dict[int, str]

    def __init__(self, conf, name : str, icon : str, system : str):
        self.name = name
        self.system = system
        self.icon = icon
        self.channels = list()
        self.conf = conf
        self.reminders = {}

