from sys import platform

if platform == "linux" or platform == "linux2":
    ROOT_PATH = "/home/admin/Projects/ravil_bot/preacher_telegram_bot/"
elif platform == "win32":
    ROOT_PATH = ""
