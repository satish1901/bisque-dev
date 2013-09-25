import os
from tg import config


def bisque_root():
    root = os.getenv('BISQUE_ROOT')
    return root or config.get('bisque.paths.root') or ''

def bisque_path(*names):
    'return a path constructed from the installation path'
    root = bisque_root()
    return os.path.join(root, *names)
    
def data_path(*names):
    'return a path constructed from the data directory path'
    data = config.get('bisque.paths.data')
    data = data or os.path.join(bisque_root(), 'data')
    return os.path.join(data, *names)
    

def config_path(*names):
    'return a path constructed from the config directory path'
    conf = config.get('bisque.paths.config')
    conf = conf or os.path.join(bisque_root(), 'config')
    return os.path.join(conf, *names)


def site_cfg_path():
    'find a site.cfg from the usual places: locally, config, or /etc'
    site_cfg = config.get('bisque.paths.site_cfg')
    if site_cfg is not None:
        return site_cfg
    paths = ['.', 'config', '/etc/bisque']
    for d in paths:
        site_cfg = os.path.join(d, 'site.cfg')
        if os.path.exists(site_cfg):
            return site_cfg
    return None
        
                              
