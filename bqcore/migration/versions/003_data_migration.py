import os
from sqlalchemy import *
from migrate import *

class MigrationException(Exception):
    pass
def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata

    from migration.versions.env002 import metadata, DBSession
    #meta = MetaData()
    metadata.bind = migrate_engine
    DBSession.configure(bind=migrate_engine)

    # MIGRATION OF DATA
    #from migration.versions.mig002 import main
    # While I though it would be b
    print "BEGIN MIGRATING DATA.. can take a very long TIME"

    # While the following lines seem like they would work
    # the columns were not really defined in the current process
    # so we fork to a new process instead
    #from migration.versions.mig002 import main
    #main()
    path = os.path.join('bqcore', 'migration', 'versions', 'mig002.py')
    ret = os.system("python %s %s" % (path, migrate_engine.url))
    if ret  != 0:
        print "MIGRATION FAILED.. exiting"
        raise  MigrationException()

    print "END MIGRATING DATA"
    print "cleaning up"
    #END MIGRATION OF DATA
    
    # Removing unused columns and tables
    from migration.versions.model002 import (taggable, names, tags, gobjects, images,
                                             users, groups, templates, modules, mex,
                                             dataset, services)
    from migration.versions.model002 import (files, files_acl)

    taggable.c.tb_id.drop()
    taggable.c.mex_id.alter (name='mex_id')

    services.drop()
    dataset.drop()
    mex.drop()
    modules.drop()
    templates.drop()
    groups.drop()
    users.drop()
    images.drop()
    gobjects.drop()
    tags.drop()
    names.drop()

    files_acl.drop()
    files.drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
