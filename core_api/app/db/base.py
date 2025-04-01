# Import Base from base_class
from app.db.base_class import Base

# No need to import models here. SQLAlchemy discovers them through Base's metadata.
# This module simply re-exports Base for convenience. 