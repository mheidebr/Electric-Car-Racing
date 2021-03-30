import logging
import logging.handlers


def configure_logging():
    """Configures the logging for our custom logging setup.

    Args:
        display_level (int): the logging display level, levels defined in logging, DEBUG, INFO, etc.
        log_dir (string): the directory location where to store the log files
    """
    # for now all logging is going to come from the root logger. In the future this
    # could change, but it makes life a little easier for now.
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('{levelname:.1s}, {sim_index}, {message}, {funcName}, {module}', style='{',)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)

    consoleHandler.setFormatter(formatter)

    logger.addHandler(consoleHandler)

    fileHandler = logging.FileHandler('./results/logging_output/example.log')
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(logging.INFO)

    logger.addHandler(fileHandler)
