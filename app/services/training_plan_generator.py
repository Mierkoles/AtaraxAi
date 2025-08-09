"""
Training plan generation service.
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


class TriathlonTrainingPlanGenerator:
    """Generate triathlon training plans based on user goals and fitness level."""
    
    def __init__(self, goal: Goal, user: User):
        self.goal = goal
        self.user = user
        self.total_weeks = self._calculate_total_weeks()
        self.phase_distribution = self._calculate_phase_distribution()
    
    def _calculate_total_weeks(self) -> int:
        """Calculate total training weeks based on event date and current fitness."""
        days_until_event = (self.goal.event_date - date.today()).days
        weeks_available = days_until_event // 7
        
        # Adjust based on current fitness level
        if self.user.fitness_level == "beginner":
            return min(32, max(20, weeks_available))
        elif self.user.fitness_level == "intermediate":
            return min(24, max(16, weeks_available))
        else:  # advanced
            return min(20, max(12, weeks_available))
    
    def _calculate_phase_distribution(self) -> Dict[str, int]:
        """Calculate how many weeks for each training phase."""
        total = self.total_weeks
        
        if total <= 12:
            return {"base": 5, "build": 4, "peak": 2, "taper": 1}
        elif total <= 16:
            return {"base": 7, "build": 5, "peak": 3, "taper": 1}
        elif total <= 20:
            return {"base": 9, "build": 6, "peak": 3, "taper": 2}
        elif total <= 24:
            return {"base": 11, "build": 8, "peak": 3, "taper": 2}
        else:  # 24+ weeks
            return {"base": 14, "build": 10, "peak": 4, "taper": 2}
    
    def generate_plan(self, db: Session) -> TrainingPlan:
        """Generate complete training plan."""
        # Create training plan
        plan = TrainingPlan(
            goal_id=self.goal.id,
            name=f"{self.goal.title} Training Plan",
            description=f"Personalized {self.total_weeks}-week triathlon training plan",
            total_weeks=self.total_weeks,
            base_weeks=self.phase_distribution["base"],
            build_weeks=self.phase_distribution["build"],
            peak_weeks=self.phase_distribution["peak"],
            taper_weeks=self.phase_distribution["taper"],
            weekly_swim_sessions=2,
            weekly_bike_sessions=2,
            weekly_run_sessions=3,
            weekly_strength_sessions=1,
            is_generated=True,
            generated_at=date.today()
        )
        
        db.add(plan)
        db.commit()
        db.refresh(plan)
        
        # Generate workouts for each week
        self._generate_workouts(db, plan)
        
        return plan
    
    def _generate_workouts(self, db: Session, plan: TrainingPlan):
        """Generate all workouts for the training plan."""
        current_date = date.today()
        
        for week in range(1, self.total_weeks + 1):
            phase = self._get_phase_for_week(week)
            weekly_workouts = self._generate_weekly_workouts(week, phase, current_date)
            
            for workout_data in weekly_workouts:
                workout = Workout(
                    training_plan_id=plan.id,
                    **workout_data
                )
                db.add(workout)
            
            current_date += timedelta(weeks=1)
        
        db.commit()
    
    def _get_phase_for_week(self, week: int) -> TrainingPhase:
        """Determine training phase for given week."""
        base_end = self.phase_distribution["base"]
        build_end = base_end + self.phase_distribution["build"]
        peak_end = build_end + self.phase_distribution["peak"]
        
        if week <= base_end:
            return TrainingPhase.BASE
        elif week <= build_end:
            return TrainingPhase.BUILD
        elif week <= peak_end:
            return TrainingPhase.PEAK
        else:
            return TrainingPhase.TAPER
    
    def _generate_weekly_workouts(self, week: int, phase: TrainingPhase, start_date: date) -> List[Dict[str, Any]]:
        """Generate workouts for a specific week."""
        workouts = []
        
        # Parse current run ability to set distances
        current_run_miles = self._parse_run_ability()
        
        if phase == TrainingPhase.BASE:
            workouts.extend(self._generate_base_week(week, start_date, current_run_miles))
        elif phase == TrainingPhase.BUILD:
            workouts.extend(self._generate_build_week(week, start_date, current_run_miles))
        elif phase == TrainingPhase.PEAK:
            workouts.extend(self._generate_peak_week(week, start_date, current_run_miles))
        else:  # TAPER
            workouts.extend(self._generate_taper_week(week, start_date, current_run_miles))
        
        return workouts
    
    def _parse_run_ability(self) -> float:
        """Parse current running ability from text description."""
        ability = self.goal.current_run_ability.lower()
        
        # Extract distance from text like "Can run 1.5 miles before walking"
        if "1.5" in ability:
            return 1.5
        elif "1" in ability:
            return 1.0
        elif "2" in ability:
            return 2.0
        elif "3" in ability:
            return 3.0
        else:
            return 1.0  # Default assumption
    
    def _generate_base_week(self, week: int, start_date: date, base_run_miles: float) -> List[Dict[str, Any]]:
        """Generate base phase week workouts."""
        # Progressive build from current ability
        week_multiplier = 1 + (week * 0.1)  # 10% increase per week
        target_long_run = min(base_run_miles * week_multiplier, 6.0)  # Cap at 6 miles
        
        return [
            # Monday - Rest
            {
                "name": "Rest Day",
                "workout_type": WorkoutType.REST,
                "intensity": WorkoutIntensity.RECOVERY,
                "phase": TrainingPhase.BASE,
                "week_number": week,
                "day_of_week": 0,
                "scheduled_date": start_date,
                "duration_minutes": 0,
                "description": "Complete rest or light stretching"
            },
            
            # Tuesday - Easy Run
            {
                "name": "Easy Run",
                "workout_type": WorkoutType.RUN,
                "intensity": WorkoutIntensity.EASY,
                "phase": TrainingPhase.BASE,
                "week_number": week,
                "day_of_week": 1,
                "scheduled_date": start_date + timedelta(days=1),
                "duration_minutes": int(base_run_miles * 10),  # ~10 min/mile
                "distance_miles": base_run_miles,
                "description": "Comfortable pace, should be able to hold conversation",
                "instructions": "Focus on form and breathing. Walk if needed."
            },
            
            # Wednesday - Swim
            {
                "name": "Base Swim",
                "workout_type": WorkoutType.SWIM,
                "intensity": WorkoutIntensity.EASY,
                "phase": TrainingPhase.BASE,
                "week_number": week,
                "day_of_week": 2,
                "scheduled_date": start_date + timedelta(days=2),
                "duration_minutes": 30,
                "total_yards": 500 + (week * 50),  # Progressive increase
                "description": "Focus on technique and breathing",
                "instructions": "Warm up 100y, main set with rest as needed"
            },
            
            # Thursday - Bike
            {
                "name": "Base Bike",
                "workout_type": WorkoutType.BIKE,
                "intensity": WorkoutIntensity.EASY,
                "phase": TrainingPhase.BASE,
                "week_number": week,
                "day_of_week": 3,
                "scheduled_date": start_date + timedelta(days=3),
                "duration_minutes": 30 + (week * 5),
                "distance_miles": 5 + (week * 0.5),
                "description": "Steady pace, build endurance",
                "instructions": "Maintain comfortable effort, focus on cadence 80-90 RPM"
            },
            
            # Friday - Rest or easy swim
            {
                "name": "Recovery Swim",
                "workout_type": WorkoutType.SWIM,
                "intensity": WorkoutIntensity.RECOVERY,
                "phase": TrainingPhase.BASE,
                "week_number": week,
                "day_of_week": 4,
                "scheduled_date": start_date + timedelta(days=4),
                "duration_minutes": 20,
                "total_yards": 300,
                "description": "Easy recovery swim",
                "instructions": "Very easy pace, focus on relaxation"
            },
            
            # Saturday - Long Run
            {
                "name": "Long Run",
                "workout_type": WorkoutType.RUN,
                "intensity": WorkoutIntensity.EASY,
                "phase": TrainingPhase.BASE,
                "week_number": week,
                "day_of_week": 5,
                "scheduled_date": start_date + timedelta(days=5),
                "duration_minutes": int(target_long_run * 11),  # Slightly slower pace
                "distance_miles": target_long_run,
                "description": "Build endurance with longer run",
                "instructions": "Start easy, maintain effort. Walk breaks OK."
            },
            
            # Sunday - Cross training or rest
            {
                "name": "Cross Training",
                "workout_type": WorkoutType.CROSS_TRAINING,
                "intensity": WorkoutIntensity.EASY,
                "phase": TrainingPhase.BASE,
                "week_number": week,
                "day_of_week": 6,
                "scheduled_date": start_date + timedelta(days=6),
                "duration_minutes": 30,
                "description": "Low impact activity",
                "instructions": "Yoga, walking, or other low-intensity activity"
            }
        ]
    
    def _generate_build_week(self, week: int, start_date: date, base_run_miles: float) -> List[Dict[str, Any]]:
        """Generate build phase week workouts with increased intensity."""
        # More intense workouts, intervals, longer sessions
        return self._generate_base_week(week, start_date, base_run_miles)  # Simplified for now
    
    def _generate_peak_week(self, week: int, start_date: date, base_run_miles: float) -> List[Dict[str, Any]]:
        """Generate peak phase week workouts."""
        # Race pace intervals, brick workouts
        return self._generate_base_week(week, start_date, base_run_miles)  # Simplified for now
    
    def _generate_taper_week(self, week: int, start_date: date, base_run_miles: float) -> List[Dict[str, Any]]:
        """Generate taper phase week workouts."""
        # Reduced volume, maintain intensity
        return self._generate_base_week(week, start_date, base_run_miles)  # Simplified for now


def generate_training_plan(db: Session, goal: Goal, user: User) -> TrainingPlan:
    """Generate training plan based on goal type."""
    if goal.goal_type == GoalType.TRIATHLON:
        generator = TriathlonTrainingPlanGenerator(goal, user)
        return generator.generate_plan(db)
    else:
        raise ValueError(f"Training plan generation not implemented for goal type: {goal.goal_type}")
