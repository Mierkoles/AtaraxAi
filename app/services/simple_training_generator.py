"""
Simple, reliable training plan generator.
Fixes the issues with excessive workout generation and unrealistic intensities.
"""
from datetime import date, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.goal import Goal, GoalType
from app.models.training import (
    TrainingPlan, 
    Workout, 
    WorkoutType, 
    WorkoutIntensity, 
    TrainingPhase
)
from app.models.user import User


def create_simple_training_plan(db: Session, goal: Goal, user: User) -> TrainingPlan:
    """Create a simple, realistic training plan."""
    
    # Calculate plan duration based on event date
    if goal.event_date:
        days_available = (goal.event_date - date.today()).days
        total_weeks = max(8, days_available // 7)  # Minimum 8 weeks, scale to event
    else:
        total_weeks = 16  # Default 16-week plan if no event date
    
    # Create training plan
    plan = TrainingPlan(
        goal_id=goal.id,
        name=f"{goal.title} - Training Plan",
        description=f"Progressive {goal.goal_type.value.replace('_', ' ').title()} training plan",
        total_weeks=total_weeks,
        base_weeks=total_weeks // 2,
        build_weeks=total_weeks // 3,
        peak_weeks=2,
        taper_weeks=1,
        weekly_swim_sessions=3 if goal.goal_type in [GoalType.TRIATHLON, GoalType.IRONMAN] else 0,
        weekly_bike_sessions=3 if goal.goal_type in [GoalType.TRIATHLON, GoalType.IRONMAN, GoalType.CYCLING] else 1,
        weekly_run_sessions=4 if goal.goal_type in [GoalType.MARATHON, GoalType.HALF_MARATHON] else 3,
        weekly_strength_sessions=2,
        is_generated=True,
        generated_at=date.today()
    )
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    # Generate workouts - ONE week at a time, 7 workouts per week MAX
    start_date = date.today()
    
    for week_num in range(1, total_weeks + 1):
        week_start = start_date + timedelta(weeks=week_num - 1)
        
        # Determine phase
        if week_num <= plan.base_weeks:
            phase = TrainingPhase.BASE
        elif week_num <= plan.base_weeks + plan.build_weeks:
            phase = TrainingPhase.BUILD
        elif week_num <= plan.base_weeks + plan.build_weeks + plan.peak_weeks:
            phase = TrainingPhase.PEAK
        else:
            phase = TrainingPhase.TAPER
        
        # Generate exactly 7 workouts for this week
        weekly_workouts = generate_week_workouts(goal.goal_type, week_num, phase, week_start, plan)
        
        for workout_data in weekly_workouts:
            workout = Workout(
                training_plan_id=plan.id,
                **workout_data
            )
            db.add(workout)
    
    db.commit()
    return plan


def generate_week_workouts(goal_type: GoalType, week: int, phase: TrainingPhase, start_date: date, plan: TrainingPlan) -> List[Dict]:
    """Generate exactly 7 workouts for one week."""
    workouts = []
    
    # Base intensity based on phase
    base_intensity = {
        TrainingPhase.BASE: WorkoutIntensity.EASY,
        TrainingPhase.BUILD: WorkoutIntensity.MODERATE, 
        TrainingPhase.PEAK: WorkoutIntensity.HARD,
        TrainingPhase.TAPER: WorkoutIntensity.EASY
    }[phase]
    
    if goal_type in [GoalType.TRIATHLON, GoalType.IRONMAN]:
        workouts = generate_triathlon_week(week, phase, start_date, base_intensity)
    elif goal_type in [GoalType.MARATHON, GoalType.HALF_MARATHON, GoalType.TEN_K, GoalType.FIVE_K]:
        workouts = generate_running_week(week, phase, start_date, base_intensity)
    else:
        workouts = generate_general_week(week, phase, start_date, base_intensity)
    
    return workouts


def generate_triathlon_week(week: int, phase: TrainingPhase, start_date: date, intensity: WorkoutIntensity) -> List[Dict]:
    """Generate a realistic triathlon week - exactly 7 workouts."""
    
    # Progressive but realistic distances
    base_run = min(2.0 + (week * 0.2), 6.0)  # Max 6 miles for regular runs
    base_bike = min(10 + (week * 1.0), 25.0)  # Max 25 miles for regular rides  
    base_swim = min(500 + (week * 25), 1500)  # Max 1500 yards
    
    # Taper in final weeks
    if phase == TrainingPhase.TAPER:
        base_run *= 0.7
        base_bike *= 0.7
        base_swim *= 0.7
    
    return [
        # Monday - Rest
        {
            "name": "Rest Day",
            "workout_type": WorkoutType.REST,
            "intensity": WorkoutIntensity.EASY,
            "phase": phase,
            "week_number": week,
            "day_of_week": 0,
            "scheduled_date": start_date,
            "duration_minutes": 0,
            "description": "Complete rest"
        },
        # Tuesday - Run
        {
            "name": f"Run - {base_run:.1f} miles",
            "workout_type": WorkoutType.RUN,
            "intensity": intensity,
            "phase": phase,
            "week_number": week,
            "day_of_week": 1,
            "scheduled_date": start_date + timedelta(days=1),
            "duration_minutes": int(base_run * 9),  # 9 min/mile pace
            "distance_miles": base_run,
            "description": f"Week {week} steady run"
        },
        # Wednesday - Swim
        {
            "name": f"Swim - {int(base_swim)} yards",
            "workout_type": WorkoutType.SWIM,
            "intensity": intensity,
            "phase": phase,
            "week_number": week,
            "day_of_week": 2,
            "scheduled_date": start_date + timedelta(days=2),
            "duration_minutes": int(base_swim / 25),  # ~25 yards per minute
            "distance_miles": base_swim / 1760,  # Convert to miles
            "description": f"Week {week} swim workout"
        },
        # Thursday - Bike
        {
            "name": f"Bike - {base_bike:.1f} miles",
            "workout_type": WorkoutType.BIKE,
            "intensity": intensity,
            "phase": phase,
            "week_number": week,
            "day_of_week": 3,
            "scheduled_date": start_date + timedelta(days=3),
            "duration_minutes": int(base_bike * 3),  # 20mph average
            "distance_miles": base_bike,
            "description": f"Week {week} bike workout"
        },
        # Friday - Easy Swim
        {
            "name": f"Easy Swim - {int(base_swim * 0.6)} yards",
            "workout_type": WorkoutType.SWIM,
            "intensity": WorkoutIntensity.EASY,
            "phase": phase,
            "week_number": week,
            "day_of_week": 4,
            "scheduled_date": start_date + timedelta(days=4),
            "duration_minutes": int(base_swim * 0.6 / 25),
            "distance_miles": (base_swim * 0.6) / 1760,
            "description": "Recovery swim"
        },
        # Saturday - Long workout (alternating)
        {
            "name": f"Long {'Run' if week % 2 == 0 else 'Bike'} - {base_run * 1.5:.1f} {'miles' if week % 2 == 0 else f'{base_bike * 1.2:.1f} miles'}",
            "workout_type": WorkoutType.RUN if week % 2 == 0 else WorkoutType.BIKE,
            "intensity": WorkoutIntensity.EASY,
            "phase": phase,
            "week_number": week,
            "day_of_week": 5,
            "scheduled_date": start_date + timedelta(days=5),
            "duration_minutes": int((base_run * 1.5 * 10) if week % 2 == 0 else (base_bike * 1.2 * 3)),
            "distance_miles": base_run * 1.5 if week % 2 == 0 else base_bike * 1.2,
            "description": f"Week {week} long workout"
        },
        # Sunday - Strength or Rest
        {
            "name": "Strength Training",
            "workout_type": WorkoutType.STRENGTH,
            "intensity": WorkoutIntensity.MODERATE,
            "phase": phase,
            "week_number": week,
            "day_of_week": 6,
            "scheduled_date": start_date + timedelta(days=6),
            "duration_minutes": 45,
            "description": "Full body strength"
        }
    ]


def generate_running_week(week: int, phase: TrainingPhase, start_date: date, intensity: WorkoutIntensity) -> List[Dict]:
    """Generate a realistic running week."""
    base_run = min(3.0 + (week * 0.3), 8.0)
    
    return [
        # Monday - Rest
        {
            "name": "Rest Day",
            "workout_type": WorkoutType.REST,
            "intensity": WorkoutIntensity.EASY,
            "phase": phase,
            "week_number": week,
            "day_of_week": 0,
            "scheduled_date": start_date,
            "duration_minutes": 0,
            "description": "Complete rest"
        },
        # Tuesday - Easy Run
        {
            "name": f"Easy Run - {base_run:.1f} miles",
            "workout_type": WorkoutType.RUN,
            "intensity": WorkoutIntensity.EASY,
            "phase": phase,
            "week_number": week,
            "day_of_week": 1,
            "scheduled_date": start_date + timedelta(days=1),
            "duration_minutes": int(base_run * 10),
            "distance_miles": base_run,
            "description": "Recovery run"
        },
        # Wednesday - Strength
        {
            "name": "Strength Training",
            "workout_type": WorkoutType.STRENGTH,
            "intensity": WorkoutIntensity.MODERATE,
            "phase": phase,
            "week_number": week,
            "day_of_week": 2,
            "scheduled_date": start_date + timedelta(days=2),
            "duration_minutes": 45,
            "description": "Running-specific strength"
        },
        # Thursday - Tempo Run
        {
            "name": f"Tempo Run - {base_run * 0.8:.1f} miles",
            "workout_type": WorkoutType.RUN,
            "intensity": intensity,
            "phase": phase,
            "week_number": week,
            "day_of_week": 3,
            "scheduled_date": start_date + timedelta(days=3),
            "duration_minutes": int(base_run * 0.8 * 8),
            "distance_miles": base_run * 0.8,
            "description": "Tempo pace workout"
        },
        # Friday - Rest
        {
            "name": "Rest Day",
            "workout_type": WorkoutType.REST,
            "intensity": WorkoutIntensity.EASY,
            "phase": phase,
            "week_number": week,
            "day_of_week": 4,
            "scheduled_date": start_date + timedelta(days=4),
            "duration_minutes": 0,
            "description": "Rest before long run"
        },
        # Saturday - Long Run
        {
            "name": f"Long Run - {base_run * 1.5:.1f} miles",
            "workout_type": WorkoutType.RUN,
            "intensity": WorkoutIntensity.EASY,
            "phase": phase,
            "week_number": week,
            "day_of_week": 5,
            "scheduled_date": start_date + timedelta(days=5),
            "duration_minutes": int(base_run * 1.5 * 11),
            "distance_miles": base_run * 1.5,
            "description": "Weekly long run"
        },
        # Sunday - Cross Training
        {
            "name": "Cross Training",
            "workout_type": WorkoutType.CROSS_TRAINING,
            "intensity": WorkoutIntensity.EASY,
            "phase": phase,
            "week_number": week,
            "day_of_week": 6,
            "scheduled_date": start_date + timedelta(days=6),
            "duration_minutes": 30,
            "description": "Light cross training"
        }
    ]


def generate_general_week(week: int, phase: TrainingPhase, start_date: date, intensity: WorkoutIntensity) -> List[Dict]:
    """Generate a general fitness week."""
    
    schedule = [
        ("Strength Training", WorkoutType.STRENGTH, 45),
        ("Cardio Run", WorkoutType.RUN, 30),
        ("Upper Body Strength", WorkoutType.STRENGTH, 45),
        ("Rest Day", WorkoutType.REST, 0),
        ("Lower Body Strength", WorkoutType.STRENGTH, 45),
        ("Cardio Workout", WorkoutType.RUN, 35),
        ("Rest Day", WorkoutType.REST, 0)
    ]
    
    workouts = []
    for day, (name, workout_type, duration) in enumerate(schedule):
        workouts.append({
            "name": name,
            "workout_type": workout_type,
            "intensity": intensity if workout_type != WorkoutType.REST else WorkoutIntensity.EASY,
            "phase": phase,
            "week_number": week,
            "day_of_week": day,
            "scheduled_date": start_date + timedelta(days=day),
            "duration_minutes": duration,
            "distance_miles": 3.0 if workout_type == WorkoutType.RUN else None,
            "description": f"Week {week} general fitness"
        })
    
    return workouts
