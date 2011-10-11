from sqlalchemy import *
from sqlalchemy.orm import mapper, relation, backref
from sqlalchemy.types import Integer, Unicode, Boolean

from blobsrv.model import DeclarativeBase, metadata, DBSession

__all__ = [ 'BlobAcl' ]

class BlobAcl(DeclarativeBase):
    __tablename__ = 'blob_acls'
    blob_id = Column(Integer, ForeignKey('blobs.id'), primary_key=True)
    blob = relation('Blob', foreign_keys=blob_id)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relation('BlobsrvUser', foreign_keys=user_id)
    perms = Column(Integer, nullable=False)
    def __repr__(self):
        return (u"<BlobAcl('%s','%s', '%s')>" % (
            self.blob, self.user, self.perms
        )).encode('utf-8')
