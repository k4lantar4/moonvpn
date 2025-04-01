# Import necessary components from SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Import the Base class from the database configuration
from app.db.base import Base

# Define the Plan model class, inheriting from Base
class Plan(Base):
    """
    Service plan model for storing different subscription plans that users can purchase.
    """
    # Define the table name explicitly
    __tablename__ = "plans"

    # Primary key column: 'id'
    id = Column(Integer, primary_key=True, index=True)

    # Plan name column: 'name'
    # - Unique identifier for the plan (e.g., "Standard 30-Day", "Premium Unlimited")
    # - Indexed for faster lookups
    name = Column(String(100), nullable=False)

    # Plan description column: 'description'
    # - Optional text describing the plan details
    description = Column(Text, nullable=True)

    # Plan price column: 'price'
    # - Using DECIMAL for precise decimal values (e.g., for currency)
    # - Specify precision and scale as needed (e.g., precision=10, scale=2 for 12345678.90)
    # - Cannot be null
    price = Column(DECIMAL(10, 2), nullable=False)

    # Plan duration column: 'duration_days'
    # - Validity period of the plan in days
    # - Cannot be null
    duration_days = Column(Integer, nullable=False)

    # Traffic limit column: 'traffic_limit_gb'
    # - Maximum data usage allowed in Gigabytes (GB)
    # - Can be null (indicating unlimited traffic)
    traffic_limit_gb = Column(Integer, nullable=True)

    # Plan status column: 'is_active'
    # - Indicates if the plan is currently available for purchase
    # - Defaults to True
    is_active = Column(Boolean, default=True)

    # Plan status column: 'is_featured'
    # - Indicates if the plan is featured/recommended
    # - Defaults to False
    is_featured = Column(Boolean, default=False)

    # Plan status column: 'sort_order'
    # - Used for sorting plans in UI
    # - Defaults to 100
    sort_order = Column(Integer, default=100)

    # Plan status column: 'category_id'
    # - Optional category for grouping plans
    category_id = Column(Integer, ForeignKey("plan_categories.id"), nullable=True)

    # Plan status column: 'created_at'
    # - Timestamp when the plan was created
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Plan status column: 'updated_at'
    # - Timestamp when the plan was last updated
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to PlanCategory
    category = relationship("PlanCategory", back_populates="plans")

    # Relationship to Orders/Subscriptions to be added later
    # orders = relationship("Order", back_populates="plan")

    # Representation method for easy debugging
    def __repr__(self) -> str:
        """
        Provides a string representation of the Plan instance.
        """
        return f"<Plan(id={self.id}, name='{self.name}', price={self.price}, duration={self.duration_days})>" 