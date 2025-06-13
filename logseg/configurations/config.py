import os

from pathlib import Path

from typing import Union

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
        config['LOGSEG']['log_dir'] = os.environ['LOGSEG_LOG_DIR']
    if 'LOGSEG_MAX_BYTES' in os.environ:
        config['LOGSEG']['max_bytes'] = os.environ['LOGSEG_MAX_BYTES']
    if 'LOGSEG_BACKUP_COUNT' in os.environ:
        config['LOGSEG']['backup_count'] = os.environ['LOGSEG_BACKUP_COUNT']
    if 'LOGSEG_PRE_PURGE' in os.environ:
        config['LOGSEG']['pre_purge'] = os.environ['LOGSEG_PRE_PURGE']
    if 'LOGSEG_TIMEZONE' in os.environ:
        config['LOGSEG']['timezone'] = os.environ['LOGSEG_TIMEZONE']
    if 'LOGSEG_LOG_LEVEL' in os.environ:
        config['LOGSEG']['log_level'] = os.environ['LOGSEG_LOG_LEVEL']

    return config


def _default_config() -> ConfigParser:
    """
    This function generates a default configuration file.

    Returns:
        A ConfigParser instance with default configurations.
    """
    config = ConfigParser()
    config.add_section('LOGSEG')
    config.set('LOGSEG', 'log_dir', 'logs')
    config.set('LOGSEG', 'max_bytes', '10000000')
    config.set('LOGSEG', 'backup_count', '6')
    config.set('LOGSEG', 'pre_purge', 'true')
    config.set('LOGSEG', 'timezone', 'UTC')
    config.set('LOGSEG', 'log_level', 'INFO')
    return config


def get_config(config_file: Union[Path, str] = None) -> ConfigParser:
    """
    Determine and load the correct config file based on environment variables.

    Args:
        config_file: The path to the config file.

    Returns:
        A ConfigParser instance with the logger configuration.

    """
    config = _default_config()

    if config_file is not None:
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file {config_file} not found.")
        config.read(config_file)

    config = _override_config(config)

    return config
