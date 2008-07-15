"""Setup the addressbook application"""
import logging

from paste.deploy import appconfig
from pylons import config

from addressbook.config.environment import load_environment
from addressbook.model import meta

log = logging.getLogger(__name__)

def setup_config(command, filename, section, vars):
    """Place any commands to setup addressbook here"""
    conf = appconfig('config:' + filename)
    load_environment(conf.global_conf, conf.local_conf)
    
    log.info("Creating tables")
    meta.metadata.create_all(bind=meta.engine)
    log.info("Successfully setup")
    
    
