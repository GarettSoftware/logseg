import os

from configparser import ConfigParser


def _override_config(config: ConfigParser) -> ConfigParser:
    """
    This function loads configurations from the system's environment variables to override the default values defined
    in conf.config.

    Args:
        config: A ConfigParser instance to load configurations into.

    Returns: A ConfigParser instance with updated configurations.

    """
    if 'LOGSEG_LOG_DIR' in os.environ:
        config['Logger']['log_dir'] = os.environ['LOGSEG_LOG_DIR']
    if 'LOGSEG_MAX_BYTES' in os.environ:
        config['Logger']['max_bytes'] = os.environ['LOGSEG_MAX_BYTES']
    if 'LOGSEG_BACKUP_COUNT' in os.environ:
        config['Logger']['backup_count'] = os.environ['LOGSEG_BACKUP_COUNT']
    if 'LOGSEG_PRE_PURGE' in os.environ:
        config['Logger']['pre_purge'] = os.environ['LOGSEG_PRE_PURGE']

    return config


def get_config() -> ConfigParser:
    """
    Determine and load the correct config file based on environment variables.
    """
    config = ConfigParser()

    config.read('logseg/configurations/conf.config')

    config = _override_config(config)

    return config
