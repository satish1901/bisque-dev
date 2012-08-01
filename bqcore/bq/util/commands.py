import os

config_dirs = ('.', './config', '/etc/bisque')

def asbool(v):
  return str(v).lower() in ("yes", "true", "t", "1")

def find_site_cfg(cfg_file):
    for dp in config_dirs:
        site_cfg = os.path.join(dp, cfg_file)
        if os.path.exists(site_cfg):
            return site_cfg
    return None
