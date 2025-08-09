"""
Nutrition and meal planning models.
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, Float, Text, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base


class MealType(enum.Enum):
    """Types of meals."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    PRE_WORKOUT = "pre_workout"
    POST_WORKOUT = "post_workout"


class DietaryRestriction(enum.Enum):
    """Dietary restrictions."""
    NONE = "none"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    KETO = "keto"
    PALEO = "paleo"


class NutritionGoal(Base):
    """Nutrition goals and targets."""
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    goal_id = Column(Integer, ForeignKey("goal.id"), nullable=True)
    
    # Daily targets
    daily_calories = Column(Integer, nullable=False)
    daily_protein_g = Column(Float, nullable=False)
    daily_carbs_g = Column(Float, nullable=False)
    daily_fat_g = Column(Float, nullable=False)
    daily_fiber_g = Column(Float, nullable=True)
    daily_water_oz = Column(Float, nullable=True)
    
    # Dietary preferences
    dietary_restrictions = Column(String(255), nullable=True)  # JSON array
    food_allergies = Column(Text, nullable=True)
    preferred_cuisines = Column(Text, nullable=True)
    disliked_foods = Column(Text, nullable=True)
    
    # Activity multiplier
    activity_level = Column(String(50), nullable=True)  # sedentary, light, moderate, active, very_active
    
    # Timestamps
    created_at = Column(Date, server_default=func.now())
    updated_at = Column(Date, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    meal_plans = relationship("MealPlan", back_populates="nutrition_goal")
    
    def __repr__(self):
        return f"<NutritionGoal(id={self.id}, calories={self.daily_calories})>"


class MealPlan(Base):
    """Weekly meal plan."""
    
    id = Column(Integer, primary_key=True, index=True)
    nutrition_goal_id = Column(Integer, ForeignKey("nutritiongoal.id"), nullable=False)
    
    # Plan details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    week_start_date = Column(Date, nullable=False)
    
    # Plan status
    is_active = Column(Boolean, default=False)
    is_generated = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(Date, server_default=func.now())
    updated_at = Column(Date, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    nutrition_goal = relationship("NutritionGoal", back_populates="meal_plans")
    meals = relationship("Meal", back_populates="meal_plan")
    
    def __repr__(self):
        return f"<MealPlan(id={self.id}, name='{self.name}')>"


class Recipe(Base):
    """Recipe database."""
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Recipe details
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    cuisine_type = Column(String(100), nullable=True)
    meal_type = Column(SQLEnum(MealType), nullable=False)
    
    # Timing
    prep_time_minutes = Column(Integer, nullable=True)
    cook_time_minutes = Column(Integer, nullable=True)
    total_time_minutes = Column(Integer, nullable=True)
    
    # Nutrition per serving
    servings = Column(Integer, default=1)
    calories_per_serving = Column(Integer, nullable=True)
    protein_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)
    fiber_g = Column(Float, nullable=True)
    sugar_g = Column(Float, nullable=True)
    sodium_mg = Column(Float, nullable=True)
    
    # Recipe content
    ingredients = Column(Text, nullable=False)  # JSON array
    instructions = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Dietary info
    dietary_tags = Column(String(255), nullable=True)  # JSON array: vegetarian, gluten_free, etc.
    difficulty_level = Column(String(50), default="easy")  # easy, medium, hard
    
    # Ratings
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Source
    source_url = Column(String(500), nullable=True)
    created_by = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(Date, server_default=func.now())
    updated_at = Column(Date, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    meals = relationship("Meal", back_populates="recipe")
    
    def __repr__(self):
        return f"<Recipe(id={self.id}, name='{self.name}')>"


class Meal(Base):
    """Individual meal in a meal plan."""
    
    id = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("mealplan.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipe.id"), nullable=False)
    
    # Scheduling
    meal_date = Column(Date, nullable=False)
    meal_type = Column(SQLEnum(MealType), nullable=False)
    
    # Customization
    servings = Column(Float, default=1.0)
    notes = Column(Text, nullable=True)
    
    # Completion tracking
    is_completed = Column(Boolean, default=False)
    completed_at = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(Date, server_default=func.now())
    updated_at = Column(Date, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    meal_plan = relationship("MealPlan", back_populates="meals")
    recipe = relationship("Recipe", back_populates="meals")
    
    @property
    def total_calories(self) -> float:
        """Calculate total calories for this meal."""
        if self.recipe and self.recipe.calories_per_serving:
            return self.recipe.calories_per_serving * self.servings
        return 0.0
    
    @property
    def total_protein(self) -> float:
        """Calculate total protein for this meal."""
        if self.recipe and self.recipe.protein_g:
            return self.recipe.protein_g * self.servings
        return 0.0
    
    def __repr__(self):
        return f"<Meal(id={self.id}, type='{self.meal_type.value}', date='{self.meal_date}')>"
