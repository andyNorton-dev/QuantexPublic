import logging
import logging.config
import yaml
import os

class Logger:
    def __init__(self,
        default_path=None,
        default_level=logging.INFO,
        env_key='LOG_CFG'
    ):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        if default_path is None:
            default_path = os.path.join(base_dir, 'logging_config.yaml')

        path = os.getenv(env_key, default_path)

        log_dir = os.path.join(base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        if os.path.exists(path):
            with open(path, 'rt') as f:
                try:
                    config = yaml.safe_load(f)

                    for handler in ['debug_file', 'prod_file', 'error_file']:
                        if handler in config['handlers']:
                            config['handlers'][handler]['filename'] = os.path.join(log_dir, os.path.basename(config['handlers'][handler]['filename']))

                    logging.config.dictConfig(config)
                except Exception as e:
                    print(f"Ошибка загрузки конфигурации логирования: {e}")
                    logging.basicConfig(level=default_level)
        else:
            print(f"Файл {path} не найден. Используется стандартная конфигурация логирования.")
            logging.basicConfig(level=default_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        self.logger = logging.getLogger('my_app')

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs, stacklevel=2)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs, stacklevel=2)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs, stacklevel=2)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs, stacklevel=2)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs, stacklevel=2)

logger = Logger()
