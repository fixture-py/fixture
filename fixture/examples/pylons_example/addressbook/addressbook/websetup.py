"""Setup the addressbook application"""
import logging

from paste.deploy import appconfig
from pylons import config

from addressbook.config.environment import load_environment
from addressbook import model
from addressbook.model import meta

from fixture import SQLAlchemyFixture
from fixture.style import NamedDataStyle
from addressbook.datasets import PersonData

log = logging.getLogger(__name__)

def setup_config(command, filename, section, vars):
    """Place any commands to setup addressbook here"""
    conf = appconfig('config:' + filename)
    load_environment(conf.global_conf, conf.local_conf)
    
    log.info("Creating tables")
    meta.metadata.create_all(bind=meta.engine)
    log.info("Successfully setup")
    
    # load some initial data during setup-app
    
    db = SQLAlchemyFixture(
            env=model, style=NamedDataStyle(),
            engine=meta.engine)
    
    # quiet down fixture's own debug output 
	# (activated by Paste) 
    fl = logging.getLogger("fixture.loadable")
    fl.setLevel(logging.CRITICAL)
    fl = logging.getLogger("fixture.loadable.tree")
    fl.setLevel(logging.CRITICAL)
            
    data = db.data(PersonData)
    log.info("Inserting initial data")
    data.setup()
    log.info("Done")
    
