# Import individual types to facilitate easier imports elsewhere
# e.g. from app.schemas import User, Plan, etc.

# First import models that don't depend on others
from .plan_category import PlanCategory, PlanCategoryCreate, PlanCategoryUpdate, PlanCategoryBase
from .location import Location, LocationCreate, LocationUpdate, LocationBase
from .server import Server, ServerCreate, ServerUpdate, ServerBase
from .plan import Plan, PlanCreate, PlanUpdate, PlanBase
from .panel import Panel, PanelCreate, PanelUpdate, PanelBase

# Now models with dependencies but resolve circular references
from .role import Role, RoleCreate, RoleUpdate, RoleBase
from .permission import Permission, PermissionCreate, PermissionUpdate, PermissionBase

# Finally import user which may depend on the above
from .user import User, UserCreate, UserUpdate, UserBase

# Import Token schemas
from .token import Token, TokenPayload
