import logging
import os

from pylons import config

from openspending.model import Dataset, meta as db
from openspending.test.helpers import load_fixture

import migrate.versioning.api as migrate_api

log = logging.getLogger(__name__)

def drop():
    log.warn("Dropping database")
    db.metadata.reflect()
    db.metadata.drop_all()
    return 0

def init():
    log.warn("Initializing database")
    db.metadata.create_all()
    url = config.get('sqlalchemy.url')
    repo, repo_version = _migrate_repo()
    migrate_api.version_control(url, repo, version=repo_version)
    return 0

def drop_collections():
    # Kept for backwards compatibility
    return drop()

def drop_dataset(name):
    log.warn("Dropping dataset '%s'", name)
    dataset = db.session.query(Dataset).filter_by(name=name).first()
    dataset.drop()
    db.session.delete(dataset)
    db.session.commit()
    return 0

def load_example(name):
    # TODO: separate the concepts of example/development data and test
    #       fixtures.
    load_fixture(name)
    return 0

def migrate():
    url = config.get('sqlalchemy.url')
    repo, repo_version = _migrate_repo()
    migrate_api.version_control(url, repo, version=repo_version)

    db_version = migrate_api.db_version(url, repo)
    if db_version < repo_version:
        migrate_api.upgrade(url, repo)
    return

def _migrate_repo():
    default = os.path.join(os.path.dirname(config['__file__']), 'migration')
    repo = config.get('openspending.migrate_dir', default)
    return repo, migrate_api.version(repo)

def _init(args):
    return init()

def _drop(args):
    return drop()

def _drop_collections(args):
    return drop_collections()

def _drop_dataset(args):
    return drop_dataset(args.name)

def _load_example(args):
    return load_example(args.name)

def _migrate(args):
    return migrate()

def configure_parser(subparsers):
    parser = subparsers.add_parser('db', help='Database operations')
    sp = parser.add_subparsers(title='subcommands')

    p = sp.add_parser('init', help='Initialize database')
    p.set_defaults(func=_init)

    p = sp.add_parser('drop', help='Drop database')
    p.set_defaults(func=_drop)

    p = sp.add_parser('dropcollections',
                      help='Drop collections within database')
    p.set_defaults(func=_drop_collections)

    p = sp.add_parser('dropdataset',
                      help='Drop a dataset from the database')
    p.add_argument('name')
    p.set_defaults(func=_drop_dataset)

    p = sp.add_parser('loadexample',
                      help='Load an example dataset into the database')
    p.add_argument('name')
    p.set_defaults(func=_load_example)

    p = sp.add_parser('migrate',
                      help='Run pending data migrations')
    p.set_defaults(func=_migrate)
