import logging
import sys

import click
import coloredlogs
from colorama import Fore, Style
from keycloak_sync.model.csvloader import CSVLoader
from keycloak_sync.model.kc import Keycloak
from keycloak_sync.model.kcuser import KCUser
from keycloak_sync import __version__
from pathlib import Path
logger = logging.getLogger(__name__)


class Arguments:
    VERBOSE = 'verbose'
    LOG_LEVEL = ['ERROR', 'WARNING', 'INFO', 'DEBUG']
    DROP_ALL = 'DELETE'
    BUCKET = 'bucket'
    BUCKET_PATH = 'bucket_path'
    BUCKET_NAME = 'bucket_name'
    KEYCLOAK_SERVER_URL = 'keycloak_server_url'
    KEYCLOAK_CLIENT_ID = 'keycloak_client_id'
    KEYCLOAK_REALM_NAME = 'keycloak_realm_name'
    KEYCLOAK_CLIENT_SECRET = 'keycloak_client_secret'
    CSV_FILE_NAME = 'csv_file_name'
    CSV_FILE_TEMPLATE = 'csv_file_template'
    OUTPUT_FILE_PATH = 'output_file_path'


def set_log(verbose: int):
    level = Arguments.LOG_LEVEL[verbose]
    coloredlogs.install(level=level, logger=logger)
    Keycloak.set_log_level(level)
    KCUser.set_log_level(level)
    CSVLoader.set_log_level(level)


@click.group()
@click.version_option(version=__version__)
def kcctl():
    """Keycloak command line tool"""


@kcctl.command()
@click.option('--kc-url', Arguments.KEYCLOAK_SERVER_URL, envvar=Arguments.KEYCLOAK_SERVER_URL.upper(), required=True, help='Keycloak server url')
@click.option('--kc-realm', Arguments.KEYCLOAK_REALM_NAME, envvar=Arguments.KEYCLOAK_REALM_NAME.upper(), required=True, help='Keycloak realm name')
@click.option('--kc-clt', Arguments.KEYCLOAK_CLIENT_ID, envvar=Arguments.KEYCLOAK_CLIENT_ID.upper(), required=True, help='keycloak client name')
@click.option('--kc-clt-sct', Arguments.KEYCLOAK_CLIENT_SECRET, envvar=Arguments.KEYCLOAK_CLIENT_SECRET.upper(), required=True, help='Keycloak client secret')
@click.option('-f', '--file', Arguments.CSV_FILE_NAME, envvar=Arguments.CSV_FILE_NAME.upper(), required=True, help='Csv file path')
@click.option('-t', '--template', Arguments.CSV_FILE_TEMPLATE, envvar=Arguments.CSV_FILE_TEMPLATE.upper(), required=True, help='Custom template file')
@click.option('-v', '--verbose', count=True)
def sync(**kwargs):
    """Synchronize users from CSV file to keycloak"""
    set_log(int(kwargs.get(Arguments.VERBOSE)))
    try:
        csvloader = CSVLoader(template=Path(kwargs.get(
            Arguments.CSV_FILE_TEMPLATE)), csvfile=Path(kwargs.get(Arguments.CSV_FILE_NAME)))
        csvloader.validate()
        logger.info(f"CSV file is valid")
        list_users = KCUser.create_list_users(csvloader)
        logger.info(f"Finish creating User Object")
        kc = Keycloak(server_url=kwargs.get(Arguments.KEYCLOAK_SERVER_URL),
                      client_id=kwargs.get(Arguments.KEYCLOAK_CLIENT_ID),
                      realm_name=kwargs.get(Arguments.KEYCLOAK_REALM_NAME),
                      client_secret_key=kwargs.get(Arguments.KEYCLOAK_CLIENT_SECRET))
        kc.add_users(list_users)
        click.echo(f'Total update/add users: {len(list_users)}')
    except (CSVLoader.CSVLoaderError, KCUser.KCUserError, Keycloak.KeycloakError) as error:
        logger.error(error)
        sys.exit(1)


@kcctl.command()
@click.option('--kc-url', Arguments.KEYCLOAK_SERVER_URL, envvar=Arguments.KEYCLOAK_SERVER_URL.upper(), required=True, help='Keycloak server url')
@click.option('--kc-realm', Arguments.KEYCLOAK_REALM_NAME, envvar=Arguments.KEYCLOAK_REALM_NAME.upper(), required=True, help='Keycloak realm name')
@click.option('--kc-clt', Arguments.KEYCLOAK_CLIENT_ID, envvar=Arguments.KEYCLOAK_CLIENT_ID.upper(), required=True, help='keycloak client name')
@click.option('--kc-clt-sct', Arguments.KEYCLOAK_CLIENT_SECRET, envvar=Arguments.KEYCLOAK_CLIENT_SECRET.upper(), required=True, help='Keycloak client secret')
@click.option('-t', '--template', Arguments.CSV_FILE_TEMPLATE, envvar=Arguments.CSV_FILE_TEMPLATE.upper(), required=True, help='Custom template file defining export rules')
@click.option('-o', '--output', Arguments.OUTPUT_FILE_PATH, envvar=Arguments.OUTPUT_FILE_PATH.upper(), required=True, help='Output file path')
@click.option('-v', '--verbose', count=True)
def export(**kwargs):
    """Export users from keycloak"""
    set_log(int(kwargs.get(Arguments.VERBOSE)))
    try:
        csvloader = CSVLoader(template=Path(kwargs.get(
            Arguments.CSV_FILE_TEMPLATE)), csvfile=None)
        kc = Keycloak(server_url=kwargs.get(Arguments.KEYCLOAK_SERVER_URL),
                      client_id=kwargs.get(Arguments.KEYCLOAK_CLIENT_ID),
                      realm_name=kwargs.get(Arguments.KEYCLOAK_REALM_NAME),
                      client_secret_key=kwargs.get(Arguments.KEYCLOAK_CLIENT_SECRET))
        list_users = kc.get_users(csvloader=csvloader, rule='export_rules')
        logger.info(f"Finishing get all list of Users Object")
        csvloader.export_users_to_csv(
            list_users=list_users, export_path=kwargs.get(Arguments.OUTPUT_FILE_PATH))
        logger.info(f"Export list of Users Object to CSV file")
        click.echo(
            f'Export users to file: {kwargs.get(Arguments.OUTPUT_FILE_PATH)}')
    except (CSVLoader.CSVLoaderError, KCUser.KCUserError, Keycloak.KeycloakError) as error:
        logger.error(error)
        sys.exit(1)


@kcctl.command()
@click.option('--kc-url', Arguments.KEYCLOAK_SERVER_URL, envvar=Arguments.KEYCLOAK_SERVER_URL.upper(), required=True, help='Keycloak server url')
@click.option('--kc-realm', Arguments.KEYCLOAK_REALM_NAME, envvar=Arguments.KEYCLOAK_REALM_NAME.upper(), required=True, help='Keycloak realm name')
@click.option('--kc-clt', Arguments.KEYCLOAK_CLIENT_ID, envvar=Arguments.KEYCLOAK_CLIENT_ID.upper(), required=True, help='keycloak client name')
@click.option('--kc-clt-sct', Arguments.KEYCLOAK_CLIENT_SECRET, envvar=Arguments.KEYCLOAK_CLIENT_SECRET.upper(), required=True, help='Keycloak client secret')
@click.option('-v', '--verbose', count=True)
@click.confirmation_option(prompt='Are you sure you want to drop all users on keycloak?')
def dropall(**kwargs):
    """Drop all users on keycloak"""
    set_log(int(kwargs.get(Arguments.VERBOSE)))
    confirm = click.prompt('Please enter a DELETE', type=str)
    if confirm == Arguments.DROP_ALL:
        try:
            kc = Keycloak(server_url=kwargs.get(Arguments.KEYCLOAK_SERVER_URL),
                          client_id=kwargs.get(Arguments.KEYCLOAK_CLIENT_ID),
                          realm_name=kwargs.get(Arguments.KEYCLOAK_REALM_NAME),
                          client_secret_key=kwargs.get(Arguments.KEYCLOAK_CLIENT_SECRET))
            kc.delete_all_users()
            logger.info(
                f"Droped all user on realm :{kwargs.get(Arguments.KEYCLOAK_REALM_NAME)}")
            click.echo(
                f'Droped all user on realm :{kwargs.get(Arguments.KEYCLOAK_REALM_NAME)}')
        except Keycloak.KeycloakError as error:
            logger.error(error)
            sys.exit(1)
    else:
        click.echo('Aborted!')
        sys.exit(1)


@kcctl.command()
@click.option('--kc-url', Arguments.KEYCLOAK_SERVER_URL, envvar=Arguments.KEYCLOAK_SERVER_URL.upper(), required=True, help='Keycloak server url')
@click.option('--kc-realm', Arguments.KEYCLOAK_REALM_NAME, envvar=Arguments.KEYCLOAK_REALM_NAME.upper(), required=True, help='Keycloak realm name')
@click.option('--kc-clt', Arguments.KEYCLOAK_CLIENT_ID, envvar=Arguments.KEYCLOAK_CLIENT_ID.upper(), required=True, help='keycloak client name')
@click.option('--kc-clt-sct', Arguments.KEYCLOAK_CLIENT_SECRET, envvar=Arguments.KEYCLOAK_CLIENT_SECRET.upper(), required=True, help='Keycloak client secret')
@click.option('-t', '--template', Arguments.CSV_FILE_TEMPLATE, envvar=Arguments.CSV_FILE_TEMPLATE.upper(), required=True, help='Custom template file')
@click.option('-v', '--verbose', count=True)
def delete(**kwargs):
    """Delete users by giving fliter conditions"""
    set_log(int(kwargs.get(Arguments.VERBOSE)))
    try:
        csvloader = CSVLoader(template=Path(kwargs.get(
            Arguments.CSV_FILE_TEMPLATE)), csvfile=None)
        kc = Keycloak(server_url=kwargs.get(Arguments.KEYCLOAK_SERVER_URL),
                      client_id=kwargs.get(Arguments.KEYCLOAK_CLIENT_ID),
                      realm_name=kwargs.get(Arguments.KEYCLOAK_REALM_NAME),
                      client_secret_key=kwargs.get(Arguments.KEYCLOAK_CLIENT_SECRET))
        list_users = kc.get_users(csvloader=csvloader, rule='delete_rules')
        list(map(lambda user: click.echo(
            f'-->{Fore.RED}{user.username}{Style.RESET_ALL}'), list_users))
        if click.confirm('Are you sure you want to delete these users on keycloak?'):
            kc.delete_users(list_users=list_users)
            click.echo(f'Total delete users: {len(list_users)}')
    except (CSVLoader.CSVLoaderError, KCUser.KCUserError, Keycloak.KeycloakError) as error:
        logger.error(error)
        sys.exit(1)
