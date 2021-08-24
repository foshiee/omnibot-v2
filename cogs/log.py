import time


def log(log: str):
	print("<" + str(time.strftime("%d %b %Y - %H:%M:%S")) + "> " + log)
