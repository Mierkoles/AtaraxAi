"""
Adaptive Training Plan Generator - Rolling 2-week generation with feedback integration.

This service generates training plans progressively, adapting based on user feedback
and performance data rather than creating static long-term plans.
"""
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.goal import Goal, GoalType
from app.models.training import (
    TrainingPlan, 
    Workout, 
    WorkoutLog,
    WorkoutType, 
    WorkoutIntensity, 
    TrainingPhase
)
from app.models.user import User


class AdaptiveTrainingGenerator:
    """Generates adaptive training plans with rolling 2-week windows."""
    
    def __init__(self):
        self.ROLLING_WEEKS = 2  # How many weeks to generate in advance
        self.ADAPTATION_THRESHOLD = 3  # Number of workouts needed before adapting
    
    def create_adaptive_training_plan(self, db: Session, goal: Goal, user: User) -> TrainingPlan:
        """Create initial training plan with phase structure but limited workout generation."""
        
        # Calculate plan duration
        if goal.event_date:
            days_available = (goal.event_date - date.today()).days
            total_weeks = max(8, days_available // 7)
        else:
            total_weeks = 16
        
        # Get plan structure based on goal type
        plan_data = self._get_plan_structure(goal, user, total_weeks)
        
        # Update goal with phase information
        goal.base_weeks = plan_data["base_weeks"]
        goal.build_weeks = plan_data["build_weeks"] 
        goal.peak_weeks = plan_data["peak_weeks"]
        goal.taper_weeks = plan_data["taper_weeks"]
        
        # Create the training plan record
        training_plan = TrainingPlan(
            goal_id=goal.id,
            name=plan_data["name"],
            description=plan_data["description"],
            total_weeks=total_weeks,
            base_weeks=goal.base_weeks,
            build_weeks=goal.build_weeks,
            peak_weeks=goal.peak_weeks,
            taper_weeks=goal.taper_weeks,
            weekly_swim_sessions=plan_data.get("weekly_swim_sessions", 0),
            weekly_bike_sessions=plan_data.get("weekly_bike_sessions", 0),
            weekly_run_sessions=plan_data.get("weekly_run_sessions", 0),
            weekly_strength_sessions=plan_data.get("weekly_strength_sessions", 2),
            is_generated=True,
            generated_at=date.today()
        )
        
        db.add(training_plan)
        db.commit()
        db.refresh(training_plan)
        
        # Generate initial 2-week rolling window
        self._generate_rolling_workouts(db, training_plan, goal, user, 1, self.ROLLING_WEEKS)
        
        return training_plan
    
    def update_rolling_plan(self, db: Session, training_plan: TrainingPlan, current_week: int) -> bool:
        """Update the rolling plan by generating new workouts and adapting based on feedback."""
        
        # Check if we need to generate new weeks
        max_generated_week = self._get_max_generated_week(db, training_plan.id)
        weeks_ahead = max_generated_week - current_week
        
        if weeks_ahead < self.ROLLING_WEEKS:
            # Need to generate more weeks
            weeks_to_generate = self.ROLLING_WEEKS - weeks_ahead
            start_week = max_generated_week + 1
            
            # Get recent feedback for adaptations
            feedback_data = self._analyze_recent_feedback(db, training_plan.goal.user_id)
            
            # Generate new weeks with adaptations
            self._generate_adaptive_workouts(
                db, training_plan, start_week, 
                min(weeks_to_generate, training_plan.total_weeks - start_week + 1),
                feedback_data
            )
            return True
        
        return False
    
    def _get_plan_structure(self, goal: Goal, user: User, total_weeks: int) -> Dict[str, Any]:
        """Get the basic plan structure based on goal type and user profile."""
        
        # Get user profile information for personalization
        age = user.age if user.birth_date else 25  # Default age if not provided
        bmi = user.bmi if (user.height_inches and user.weight_lbs) or user.bmi_known else 22.0
        fitness_level = user.fitness_level or "beginner"
        body_type = user.body_type or "average"
        
        # Adjust training intensity based on user profile
        intensity_modifier = 1.0
        if fitness_level == "beginner":
            intensity_modifier = 0.8
        elif fitness_level == "advanced":
            intensity_modifier = 1.2
        elif fitness_level == "expert":
            intensity_modifier = 1.3
        
        if goal.goal_type == GoalType.TRIATHLON:
            return {
                "name": f"Adaptive Sprint Triathlon Plan - {total_weeks} Weeks",
                "description": f"Personalized triathlon training plan adapted for {fitness_level} level athlete (age {age}, BMI {bmi:.1f}). This adaptive approach adjusts weekly based on your feedback, energy levels, and performance while respecting your body's signals and {body_type} build.",
                "base_weeks": max(6, total_weeks // 2),
                "build_weeks": max(4, total_weeks // 3),
                "peak_weeks": max(2, total_weeks // 8),
                "taper_weeks": 2,
                "weekly_swim_sessions": max(1, int(2 * intensity_modifier)),
                "weekly_bike_sessions": max(1, int(2 * intensity_modifier)),
                "weekly_run_sessions": max(2, int(3 * intensity_modifier)),
                "weekly_strength_sessions": 2
            }
        elif goal.goal_type == GoalType.MARATHON:
            return {
                "name": f"Adaptive Marathon Training - {total_weeks} Weeks",
                "description": "Progressive marathon training with smart adjustments based on your weekly feedback. Marathon training that adapts to your recovery patterns and energy levels while maintaining consistent mileage progression.",
                "base_weeks": max(8, total_weeks * 2 // 3),
                "build_weeks": max(6, total_weeks // 4),
                "peak_weeks": 2,
                "taper_weeks": 3,
                "weekly_swim_sessions": 0,
                "weekly_bike_sessions": 1,  # Cross training
                "weekly_run_sessions": 4,
                "weekly_strength_sessions": 2
            }
        else:
            # General fitness
            return {
                "name": f"Adaptive Fitness Plan - {total_weeks} Weeks",
                "description": "Balanced fitness plan that adapts to your preferences and progress. Flexible fitness approach that adapts based on your enjoyment levels and energy feedback.",
                "base_weeks": max(4, total_weeks // 3),
                "build_weeks": max(4, total_weeks // 3),
                "peak_weeks": max(2, total_weeks // 6),
                "taper_weeks": 1,
                "weekly_swim_sessions": 1,
                "weekly_bike_sessions": 1,
                "weekly_run_sessions": 2,
                "weekly_strength_sessions": 2
            }
    
    def _generate_rolling_workouts(self, db: Session, plan: TrainingPlan, goal: Goal, 
                                  user: User, start_week: int, num_weeks: int):
        """Generate workouts for the rolling window."""
        
        # Calculate plan start date from goal creation
        plan_start_date = goal.created_at.date() if goal.created_at else date.today()
        
        for week_num in range(start_week, start_week + num_weeks):
            if week_num > plan.total_weeks:
                break
                
            phase = self._get_training_phase(week_num, plan)
            weekly_focus = self._get_weekly_focus(goal.goal_type, week_num, phase, plan.total_weeks)
            
            # Calculate week start date (week 1 starts on plan_start_date)
            week_start_date = plan_start_date + timedelta(days=(week_num - 1) * 7)
            
            # Use current mock workout generation (we'll enhance this later with adaptations)
            workouts = self._generate_week_workouts(goal.goal_type, week_num, phase, plan)
            
            for workout_data in workouts:
                # Calculate specific scheduled date for this workout
                days_from_week_start = workout_data["day_of_week"]
                scheduled_date = week_start_date + timedelta(days=days_from_week_start)
                
                workout = Workout(
                    training_plan_id=plan.id,
                    week_number=week_num,
                    day_of_week=workout_data["day_of_week"],
                    scheduled_date=scheduled_date,  # Set specific date
                    name=workout_data["name"],
                    description=workout_data.get("description", ""),
                    instructions=workout_data.get("instructions", ""),
                    workout_type=WorkoutType[workout_data["workout_type"]],
                    phase=phase,
                    intensity=WorkoutIntensity[workout_data.get("intensity", "EASY").upper()],
                    duration_minutes=workout_data.get("duration_minutes", 45),
                    distance_miles=workout_data.get("distance_miles"),
                    total_yards=workout_data.get("total_yards"),
                    weekly_focus=weekly_focus
                )
                db.add(workout)
        
        db.commit()
    
    def _generate_adaptive_workouts(self, db: Session, plan: TrainingPlan, start_week: int, 
                                   num_weeks: int, feedback_data: Dict[str, Any]):
        """Generate workouts with adaptations based on feedback."""
        
        # Get goal and user for context
        goal = plan.goal
        
        # Calculate plan start date from goal creation
        plan_start_date = goal.created_at.date() if goal.created_at else date.today()
        
        for week_num in range(start_week, start_week + num_weeks):
            if week_num > plan.total_weeks:
                break
                
            phase = self._get_training_phase(week_num, plan)
            weekly_focus = self._get_weekly_focus(goal.goal_type, week_num, phase, plan.total_weeks)
            
            # Calculate week start date (week 1 starts on plan_start_date)
            week_start_date = plan_start_date + timedelta(days=(week_num - 1) * 7)
            
            # Generate base workouts
            workouts = self._generate_week_workouts(goal.goal_type, week_num, phase, plan)
            
            # Apply adaptations based on feedback
            adapted_workouts = self._adapt_workouts_based_feedback(workouts, feedback_data)
            
            for workout_data in adapted_workouts:
                # Calculate specific scheduled date for this workout
                days_from_week_start = workout_data["day_of_week"]
                scheduled_date = week_start_date + timedelta(days=days_from_week_start)
                
                workout = Workout(
                    training_plan_id=plan.id,
                    week_number=week_num,
                    day_of_week=workout_data["day_of_week"],
                    scheduled_date=scheduled_date,  # Set specific date
                    name=workout_data["name"],
                    description=workout_data.get("description", ""),
                    instructions=workout_data.get("instructions", ""),
                    workout_type=WorkoutType[workout_data["workout_type"]],
                    phase=phase,
                    intensity=WorkoutIntensity[workout_data.get("intensity", "EASY").upper()],
                    duration_minutes=workout_data.get("duration_minutes", 45),
                    distance_miles=workout_data.get("distance_miles"),
                    total_yards=workout_data.get("total_yards"),
                    weekly_focus=weekly_focus
                )
                db.add(workout)
        
        db.commit()
    
    def _analyze_recent_feedback(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Analyze recent workout feedback to inform adaptations."""
        
        # Get recent workout logs (last 2 weeks)
        recent_logs = (
            db.query(WorkoutLog)
            .filter(WorkoutLog.user_id == user_id)
            .filter(WorkoutLog.completed_date >= date.today() - timedelta(weeks=2))
            .order_by(desc(WorkoutLog.completed_date))
            .limit(10)
            .all()
        )
        
        if not recent_logs:
            return {"has_feedback": False}
        
        # Calculate averages
        exertion_scores = [log.perceived_exertion for log in recent_logs if log.perceived_exertion]
        energy_scores = [log.energy_level for log in recent_logs if log.energy_level]
        enjoyment_scores = [log.enjoyment_level for log in recent_logs if log.enjoyment_level]
        
        feedback = {
            "has_feedback": True,
            "num_workouts": len(recent_logs),
            "avg_perceived_exertion": sum(exertion_scores) / len(exertion_scores) if exertion_scores else None,
            "avg_energy_level": sum(energy_scores) / len(energy_scores) if energy_scores else None,
            "avg_enjoyment": sum(enjoyment_scores) / len(enjoyment_scores) if enjoyment_scores else None,
            "recent_notes": [log.notes for log in recent_logs if log.notes],
        }
        
        # Determine adaptation needs
        if feedback["avg_perceived_exertion"]:
            if feedback["avg_perceived_exertion"] >= 7:
                feedback["intensity_adjustment"] = "decrease"
            elif feedback["avg_perceived_exertion"] <= 3:
                feedback["intensity_adjustment"] = "increase"
            else:
                feedback["intensity_adjustment"] = "maintain"
        
        if feedback["avg_energy_level"]:
            if feedback["avg_energy_level"] <= 4:
                feedback["recovery_adjustment"] = "more_rest"
            elif feedback["avg_energy_level"] >= 8:
                feedback["recovery_adjustment"] = "can_push_harder"
            else:
                feedback["recovery_adjustment"] = "maintain"
        
        return feedback
    
    def _adapt_workouts_based_feedback(self, workouts: List[Dict], feedback: Dict[str, Any]) -> List[Dict]:
        """Adapt workout intensity and structure based on feedback."""
        
        if not feedback.get("has_feedback", False):
            return workouts
        
        adapted_workouts = []
        
        for workout in workouts:
            adapted_workout = workout.copy()
            
            # Intensity adjustments
            if feedback.get("intensity_adjustment") == "decrease":
                if adapted_workout["intensity"] == "HARD":
                    adapted_workout["intensity"] = "MODERATE"
                elif adapted_workout["intensity"] == "MODERATE":
                    adapted_workout["intensity"] = "EASY"
                # Reduce duration by 10%
                adapted_workout["duration_minutes"] = int(adapted_workout.get("duration_minutes", 45) * 0.9)
                
            elif feedback.get("intensity_adjustment") == "increase":
                if adapted_workout["intensity"] == "EASY":
                    adapted_workout["intensity"] = "MODERATE"
                elif adapted_workout["intensity"] == "MODERATE":
                    adapted_workout["intensity"] = "HARD"
                # Increase duration by 10%
                adapted_workout["duration_minutes"] = int(adapted_workout.get("duration_minutes", 45) * 1.1)
            
            # Recovery adjustments
            if feedback.get("recovery_adjustment") == "more_rest":
                # Convert some workouts to easier recovery sessions
                if workout["workout_type"] != "REST" and adapted_workout["intensity"] in ["HARD", "MODERATE"]:
                    adapted_workout["intensity"] = "EASY"
                    adapted_workout["name"] = f"Recovery {adapted_workout['name']}"
                    adapted_workout["description"] = "Adjusted for additional recovery based on your recent energy levels"
            
            adapted_workouts.append(adapted_workout)
        
        return adapted_workouts
    
    def _get_training_phase(self, week_num: int, plan: TrainingPlan) -> TrainingPhase:
        """Determine training phase for given week."""
        if week_num <= plan.base_weeks:
            return TrainingPhase.BASE
        elif week_num <= plan.base_weeks + plan.build_weeks:
            return TrainingPhase.BUILD
        elif week_num <= plan.base_weeks + plan.build_weeks + plan.peak_weeks:
            return TrainingPhase.PEAK
        else:
            return TrainingPhase.TAPER
    
    def _get_max_generated_week(self, db: Session, plan_id: int) -> int:
        """Get the highest week number that has been generated for this plan."""
        result = (
            db.query(func.max(Workout.week_number))
            .filter(Workout.training_plan_id == plan_id)
            .scalar()
        )
        return result or 0
    
    def _generate_week_workouts(self, goal_type: GoalType, week_num: int, 
                               phase: TrainingPhase, plan: TrainingPlan) -> List[Dict]:
        """Generate base workouts for a week (simplified version for now)."""
        
        # For now, use a simplified version - this would be expanded with full workout logic
        workouts = []
        
        if goal_type == GoalType.TRIATHLON:
            # Basic triathlon week structure
            workouts = [
                {
                    "day_of_week": 1, "workout_type": "SWIM", "name": f"Swim Technique - Week {week_num}",
                    "intensity": "EASY", "duration_minutes": 45, "total_yards": 400 + (week_num * 50)
                },
                {
                    "day_of_week": 2, "workout_type": "BIKE", "name": f"Bike Endurance - Week {week_num}",
                    "intensity": "MODERATE", "duration_minutes": 60, "distance_miles": 8 + (week_num * 0.5)
                },
                {
                    "day_of_week": 3, "workout_type": "RUN", "name": f"Easy Run - Week {week_num}",
                    "intensity": "EASY", "duration_minutes": 30, "distance_miles": 2 + (week_num * 0.1)
                },
                {
                    "day_of_week": 5, "workout_type": "STRENGTH", "name": f"Functional Strength - Week {week_num}",
                    "intensity": "MODERATE", "duration_minutes": 30
                }
            ]
        
        return workouts
    
    def _get_weekly_focus(self, goal_type: GoalType, week_num: int, phase: TrainingPhase, total_weeks: int) -> str:
        """Get weekly focus (simplified version)."""
        phase_focuses = {
            TrainingPhase.BASE: ["Building aerobic base", "Establishing routine", "Technique focus"],
            TrainingPhase.BUILD: ["Increasing intensity", "Race pace practice", "Building strength"],
            TrainingPhase.PEAK: ["High intensity training", "Race simulation", "Peak fitness"],
            TrainingPhase.TAPER: ["Recovery and preparation", "Maintaining fitness", "Race readiness"]
        }
        
        focuses = phase_focuses[phase]
        return focuses[(week_num - 1) % len(focuses)]


def create_adaptive_training_plan(db: Session, goal: Goal, user: User) -> TrainingPlan:
    """Create a new adaptive training plan."""
    generator = AdaptiveTrainingGenerator()
    return generator.create_adaptive_training_plan(db, goal, user)


def update_training_plan_rolling_window(db: Session, training_plan: TrainingPlan, current_week: int) -> bool:
    """Update the rolling training plan window."""
    generator = AdaptiveTrainingGenerator()
    return generator.update_rolling_plan(db, training_plan, current_week)