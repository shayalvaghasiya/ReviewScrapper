import logging as log

def getLog(nm):
    # Creating custom logger
    logger = log.getLogger(nm)
    # reading contents from properties file
    f = open("properties.txt", 'r')
    if f.mode == "r":
        loglevel = f.read()
    if loglevel == "ERROR":
        logger.setLevel(log.ERROR)
    elif loglevel == "DEBUG":
        logger.setLevel(log.DEBUG)
    # Creating Formatters
    formatter = log.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    # Creating Handlers
    file_handler = log.FileHandler('logs.log')
    # Adding Formatters to Handlers
    file_handler.setFormatter(formatter)
    # Adding Handlers to logger
    logger.addHandler(file_handler)
    return logger
