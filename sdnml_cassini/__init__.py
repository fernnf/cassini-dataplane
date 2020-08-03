import logging

def init_logger(name, level=logging.INFO):
	log = logging.getLogger(name)
	log.setLevel(level)
	ch = logging.StreamHandler()
	ch.setLevel(level)
	formatter = logging.Formatter('[%(asctime)s] [%(name)s:%(lineno)d] [%(levelname)s] - %(message)s')
	ch.setFormatter(formatter)
	log.addHandler(ch)
	return log