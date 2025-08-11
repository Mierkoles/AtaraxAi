"""
AI-powered training plan generation for any fitness goal.
"""
from datetime import date, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
import json

from app.models.goal import Goal, GoalType
from app.models.training import (
    TrainingPlan, 
    Workout, 
    WorkoutType, 
    WorkoutIntensity, 
    TrainingPhase
)
from app.models.user import User


class AITrainingPlanGenerator:
    """AI-powered training plan generator that adapts to any fitness goal."""
    
    def __init__(self, goal: Goal, user: User):
        self.goal = goal
        self.user = user
        self.goal_analyzer = GoalAnalyzer(goal, user)
        
    def generate_plan(self, db: Session) -> TrainingPlan:
        """Generate a complete AI-powered training plan."""
        
        # Analyze the goal and determine plan parameters
        plan_params = self.goal_analyzer.analyze()
        
        # Create the training plan
        plan = TrainingPlan(
            goal_id=self.goal.id,
            name=f"{self.goal.title} - AI Training Plan",
            description=plan_params['description'],
            total_weeks=plan_params['total_weeks'],
            base_weeks=plan_params['base_weeks'],
            build_weeks=plan_params['build_weeks'],
            peak_weeks=plan_params['peak_weeks'],
            taper_weeks=plan_params['taper_weeks'],
            weekly_swim_sessions=plan_params.get('swim_sessions', 0),
            weekly_bike_sessions=plan_params.get('bike_sessions', 0),
            weekly_run_sessions=plan_params.get('run_sessions', 0),
            weekly_strength_sessions=plan_params.get('strength_sessions', 0),
            is_generated=True,
            generated_at=date.today()
        )
        
        db.add(plan)
        db.commit()
        db.refresh(plan)
        
        # Generate workouts using goal-specific strategy
        workout_generator = self._get_workout_generator(plan_params)
        workout_generator.generate_all_workouts(db, plan, plan_params)
        
        return plan
    
    def _get_workout_generator(self, plan_params: Dict) -> 'WorkoutGenerator':
        """Get the appropriate workout generator for the goal type."""
        goal_type = self.goal.goal_type
        
        if goal_type in [GoalType.TRIATHLON, GoalType.IRONMAN]:
            return TriathlonWorkoutGenerator(self.goal, self.user)
        elif goal_type in [GoalType.MARATHON, GoalType.HALF_MARATHON, GoalType.TEN_K, GoalType.FIVE_K]:
            return RunningWorkoutGenerator(self.goal, self.user)
        elif goal_type in [GoalType.WEIGHT_LOSS, GoalType.MUSCLE_GAIN]:
            return WeightManagementWorkoutGenerator(self.goal, self.user)
        elif goal_type == GoalType.STRENGTH_TRAINING:
            return StrengthWorkoutGenerator(self.goal, self.user)
        elif goal_type in [GoalType.CYCLING, GoalType.CENTURY_RIDE]:
            return CyclingWorkoutGenerator(self.goal, self.user)
        else:
            return GeneralFitnessWorkoutGenerator(self.goal, self.user)


class GoalAnalyzer:
    """Analyzes goals and determines optimal training parameters."""
    
    def __init__(self, goal: Goal, user: User):
        self.goal = goal
        self.user = user
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze the goal and return training plan parameters."""
        goal_type = self.goal.goal_type
        
        # Calculate time available
        if self.goal.event_date:
            days_available = (self.goal.event_date - date.today()).days
            weeks_available = max(4, days_available // 7)  # Minimum 4 weeks
        else:
            # No event date - assume 12-week program for general goals
            weeks_available = 12
        
        # Base analysis
        analysis = {
            'total_weeks': min(weeks_available, 32),  # Max 32 weeks
            'description': f"AI-generated {goal_type.value.replace('_', ' ').title()} training plan",
            'swim_sessions': 0,
            'bike_sessions': 0,
            'run_sessions': 0,
            'strength_sessions': 1,  # Default strength for most goals
        }
        
        # Goal-specific analysis
        if goal_type in [GoalType.TRIATHLON, GoalType.IRONMAN]:
            analysis.update(self._analyze_triathlon())
        elif goal_type in [GoalType.MARATHON, GoalType.HALF_MARATHON, GoalType.TEN_K, GoalType.FIVE_K]:
            analysis.update(self._analyze_running())
        elif goal_type in [GoalType.WEIGHT_LOSS, GoalType.MUSCLE_GAIN]:
            analysis.update(self._analyze_weight_management())
        elif goal_type == GoalType.STRENGTH_TRAINING:
            analysis.update(self._analyze_strength())
        elif goal_type in [GoalType.CYCLING, GoalType.CENTURY_RIDE]:
            analysis.update(self._analyze_cycling())
        else:
            analysis.update(self._analyze_general_fitness())
        
        # Calculate phase distribution
        analysis.update(self._calculate_phases(analysis['total_weeks']))
        
        return analysis
    
    def _analyze_triathlon(self) -> Dict[str, Any]:
        return {
            'swim_sessions': 2,
            'bike_sessions': 2,
            'run_sessions': 3,
            'strength_sessions': 1,
            'description': f"Comprehensive triathlon training for {self.goal.swim_distance_meters}m swim, {self.goal.bike_distance_miles}mi bike, {self.goal.run_distance_miles}mi run"
        }
    
    def _analyze_running(self) -> Dict[str, Any]:
        distance = self.goal.run_distance_miles or 3.1
        sessions = 3 if distance <= 5 else 4 if distance <= 13.1 else 5
        return {
            'run_sessions': sessions,
            'strength_sessions': 2,
            'description': f"Progressive running training for {distance} mile race"
        }
    
    def _analyze_weight_management(self) -> Dict[str, Any]:
        return {
            'run_sessions': 2,
            'strength_sessions': 3,
            'description': f"Comprehensive fitness plan for {self.goal.goal_type.value.replace('_', ' ')}"
        }
    
    def _analyze_strength(self) -> Dict[str, Any]:
        return {
            'strength_sessions': 4,
            'run_sessions': 1,  # Cardio for recovery
            'description': "Progressive strength training program"
        }
    
    def _analyze_cycling(self) -> Dict[str, Any]:
        return {
            'bike_sessions': 4,
            'strength_sessions': 2,
            'description': f"Cycling training for {self.goal.bike_distance_miles or 100} mile goal"
        }
    
    def _analyze_general_fitness(self) -> Dict[str, Any]:
        return {
            'run_sessions': 2,
            'strength_sessions': 2,
            'description': "Balanced fitness training program"
        }
    
    def _calculate_phases(self, total_weeks: int) -> Dict[str, int]:
        """Calculate training phase distribution."""
        if total_weeks <= 8:
            return {"base_weeks": 4, "build_weeks": 3, "peak_weeks": 1, "taper_weeks": 0}
        elif total_weeks <= 12:
            return {"base_weeks": 6, "build_weeks": 4, "peak_weeks": 1, "taper_weeks": 1}
        elif total_weeks <= 16:
            return {"base_weeks": 8, "build_weeks": 5, "peak_weeks": 2, "taper_weeks": 1}
        elif total_weeks <= 20:
            return {"base_weeks": 10, "build_weeks": 6, "peak_weeks": 2, "taper_weeks": 2}
        else:
            return {"base_weeks": 12, "build_weeks": 8, "peak_weeks": 3, "taper_weeks": 2}


class WorkoutGenerator:
    """Base class for workout generation."""
    
    def __init__(self, goal: Goal, user: User):
        self.goal = goal
        self.user = user
    
    def generate_all_workouts(self, db: Session, plan: TrainingPlan, params: Dict):
        """Generate all workouts for the training plan."""
        current_date = date.today()
        
        for week in range(1, params['total_weeks'] + 1):
            phase = self._get_phase_for_week(week, params)
            weekly_workouts = self.generate_week(week, phase, current_date, params)
            
            for workout_data in weekly_workouts:
                # Ensure week_number is set correctly
                workout_data['week_number'] = week
                workout = Workout(
                    training_plan_id=plan.id,
                    **workout_data
                )
                db.add(workout)
            
            current_date += timedelta(weeks=1)
        
        db.commit()
    
    def _get_phase_for_week(self, week: int, params: Dict) -> TrainingPhase:
        """Determine training phase for given week."""
        base_end = params["base_weeks"]
        build_end = base_end + params["build_weeks"]
        peak_end = build_end + params["peak_weeks"]
        
        if week <= base_end:
            return TrainingPhase.BASE
        elif week <= build_end:
            return TrainingPhase.BUILD
        elif week <= peak_end:
            return TrainingPhase.PEAK
        else:
            return TrainingPhase.TAPER
    
    def generate_week(self, week: int, phase: TrainingPhase, start_date: date, params: Dict) -> List[Dict]:
        """Generate workouts for a specific week. Override in subclasses."""
        return []


class TriathlonWorkoutGenerator(WorkoutGenerator):
    """Triathlon-specific workout generator."""
    
    def generate_week(self, week: int, phase: TrainingPhase, start_date: date, params: Dict) -> List[Dict]:
        workouts = []
        
        # Parse current abilities
        run_ability = self._parse_fitness_level(self.goal.current_run_ability or self.goal.current_fitness_assessment)
        
        # Progressive training based on week and phase
        week_multiplier = 1 + (week * 0.05)  # 5% increase per week
        
        # Monday - Rest
        workouts.append(self._create_rest_day(0, start_date))
        
        # Tuesday - Run
        run_distance = min(run_ability * week_multiplier, 8.0)
        workouts.append(self._create_run_workout(1, start_date + timedelta(days=1), run_distance, phase))
        
        # Wednesday - Swim
        swim_yards = 400 + (week * 50)
        workouts.append(self._create_swim_workout(2, start_date + timedelta(days=2), swim_yards, phase))
        
        # Thursday - Bike
        bike_distance = 8 + (week * 0.5)
        workouts.append(self._create_bike_workout(3, start_date + timedelta(days=3), bike_distance, phase))
        
        # Friday - Rest or easy swim
        workouts.append(self._create_recovery_swim(4, start_date + timedelta(days=4)))
        
        # Saturday - Long workout (alternating bike/run)
        if week % 2 == 0:
            long_run = min(run_ability * week_multiplier * 1.5, 10.0)
            workouts.append(self._create_long_run(5, start_date + timedelta(days=5), long_run, phase))
        else:
            long_bike = bike_distance * 1.5
            workouts.append(self._create_long_bike(5, start_date + timedelta(days=5), long_bike, phase))
        
        # Sunday - Cross training or rest
        workouts.append(self._create_cross_training(6, start_date + timedelta(days=6)))
        
        return workouts
    
    def _parse_fitness_level(self, description: str) -> float:
        """Parse fitness description to get base running distance."""
        if not description:
            return 1.0
        
        description = description.lower()
        if "1.5" in description:
            return 1.5
        elif "2" in description:
            return 2.0
        elif "3" in description:
            return 3.0
        elif "1" in description:
            return 1.0
        else:
            return 1.0
    
    def _create_rest_day(self, day: int, date: date) -> Dict:
        return {
            "name": "Rest Day",
            "workout_type": WorkoutType.REST,
            "intensity": WorkoutIntensity.RECOVERY,
            "phase": TrainingPhase.BASE,
            "week_number": 1,  # This will be set correctly by the calling function
            "day_of_week": day,
            "scheduled_date": date,
            "duration_minutes": 0,
            "description": "Complete rest or light stretching"
        }
    
    def _create_run_workout(self, day: int, date: date, distance: float, phase: TrainingPhase) -> Dict:
        intensity = WorkoutIntensity.EASY if phase == TrainingPhase.BASE else WorkoutIntensity.MODERATE
        return {
            "name": f"Run - {distance:.1f} miles",
            "workout_type": WorkoutType.RUN,
            "intensity": intensity,
            "phase": phase,
            "week_number": 1,
            "day_of_week": day,
            "scheduled_date": date,
            "duration_minutes": int(distance * 10),
            "distance_miles": distance,
            "description": f"{'Easy pace' if intensity == WorkoutIntensity.EASY else 'Moderate effort'} run",
            "instructions": "Focus on form and breathing. Walk breaks are OK."
        }
    
    def _create_swim_workout(self, day: int, date: date, yards: int, phase: TrainingPhase) -> Dict:
        return {
            "name": f"Swim - {yards} yards",
            "workout_type": WorkoutType.SWIM,
            "intensity": WorkoutIntensity.EASY,
            "phase": phase,
            "week_number": 1,
            "day_of_week": day,
            "scheduled_date": date,
            "duration_minutes": 30,
            "total_yards": yards,
            "description": "Focus on technique and breathing",
            "instructions": "Warm up 100y, main set with rest as needed"
        }
    
    def _create_bike_workout(self, day: int, date: date, distance: float, phase: TrainingPhase) -> Dict:
        return {
            "name": f"Bike - {distance:.1f} miles",
            "workout_type": WorkoutType.BIKE,
            "intensity": WorkoutIntensity.EASY,
            "phase": phase,
            "week_number": 1,
            "day_of_week": day,
            "scheduled_date": date,
            "duration_minutes": int(distance * 4),
            "distance_miles": distance,
            "description": "Steady pace, build endurance",
            "instructions": "Maintain comfortable effort, cadence 80-90 RPM"
        }
    
    def _create_recovery_swim(self, day: int, date: date) -> Dict:
        return {
            "name": "Recovery Swim",
            "workout_type": WorkoutType.SWIM,
            "intensity": WorkoutIntensity.RECOVERY,
            "phase": TrainingPhase.BASE,
            "week_number": 1,
            "day_of_week": day,
            "scheduled_date": date,
            "duration_minutes": 20,
            "total_yards": 300,
            "description": "Easy recovery swim",
            "instructions": "Very easy pace, focus on relaxation"
        }
    
    def _create_long_run(self, day: int, date: date, distance: float, phase: TrainingPhase) -> Dict:
        return {
            "name": f"Long Run - {distance:.1f} miles",
            "workout_type": WorkoutType.RUN,
            "intensity": WorkoutIntensity.EASY,
            "phase": phase,
            "week_number": 1,
            "day_of_week": day,
            "scheduled_date": date,
            "duration_minutes": int(distance * 11),
            "distance_miles": distance,
            "description": "Build endurance with longer run",
            "instructions": "Start easy, maintain effort. Walk breaks OK."
        }
    
    def _create_long_bike(self, day: int, date: date, distance: float, phase: TrainingPhase) -> Dict:
        return {
            "name": f"Long Bike - {distance:.1f} miles",
            "workout_type": WorkoutType.BIKE,
            "intensity": WorkoutIntensity.MODERATE,
            "phase": phase,
            "week_number": 1,
            "day_of_week": day,
            "scheduled_date": date,
            "duration_minutes": int(distance * 4.5),
            "distance_miles": distance,
            "description": "Endurance bike ride",
            "instructions": "Steady effort, practice nutrition and hydration"
        }
    
    def _create_cross_training(self, day: int, date: date) -> Dict:
        return {
            "name": "Cross Training",
            "workout_type": WorkoutType.CROSS_TRAINING,
            "intensity": WorkoutIntensity.EASY,
            "phase": TrainingPhase.BASE,
            "week_number": 1,
            "day_of_week": day,
            "scheduled_date": date,
            "duration_minutes": 30,
            "description": "Low impact activity",
            "instructions": "Yoga, walking, or other low-intensity activity"
        }


# Simplified generators for other goal types
class RunningWorkoutGenerator(WorkoutGenerator):
    """Running-specific workout generator."""
    
    def generate_week(self, week: int, phase: TrainingPhase, start_date: date, params: Dict) -> List[Dict]:
        # Simplified running plan - 3-4 runs per week
        workouts = []
        run_sessions = params.get('run_sessions', 3)
        
        for i in range(7):
            if i in [1, 3, 5][:run_sessions]:  # Spread runs across week
                distance = 2 + (week * 0.2)
                workouts.append({
                    "name": f"Run - {distance:.1f} miles",
                    "workout_type": WorkoutType.RUN,
                    "intensity": WorkoutIntensity.EASY,
                    "phase": phase,
                    "week_number": week,
                    "day_of_week": i,
                    "scheduled_date": start_date + timedelta(days=i),
                    "duration_minutes": int(distance * 10),
                    "distance_miles": distance,
                    "description": "Progressive running training"
                })
            elif i in [2, 4]:  # Strength days
                workouts.append({
                    "name": "Strength Training",
                    "workout_type": WorkoutType.STRENGTH,
                    "intensity": WorkoutIntensity.MODERATE,
                    "phase": phase,
                    "week_number": week,
                    "day_of_week": i,
                    "scheduled_date": start_date + timedelta(days=i),
                    "duration_minutes": 45,
                    "description": "Supporting strength work"
                })
            else:
                workouts.append({
                    "name": "Rest",
                    "workout_type": WorkoutType.REST,
                    "intensity": WorkoutIntensity.RECOVERY,
                    "phase": phase,
                    "week_number": week,
                    "day_of_week": i,
                    "scheduled_date": start_date + timedelta(days=i),
                    "duration_minutes": 0,
                    "description": "Rest and recovery"
                })
        
        return workouts


class WeightManagementWorkoutGenerator(WorkoutGenerator):
    """Weight management workout generator."""
    
    def generate_week(self, week: int, phase: TrainingPhase, start_date: date, params: Dict) -> List[Dict]:
        workouts = []
        
        # Mix of cardio and strength for weight management
        schedule = [
            (WorkoutType.STRENGTH, "Upper Body Strength"),
            (WorkoutType.RUN, "Cardio Run"),
            (WorkoutType.STRENGTH, "Lower Body Strength"),
            (WorkoutType.CROSS_TRAINING, "Cross Training"),
            (WorkoutType.STRENGTH, "Full Body Strength"),
            (WorkoutType.RUN, "Long Cardio"),
            (WorkoutType.REST, "Rest")
        ]
        
        for i, (workout_type, name) in enumerate(schedule):
            duration = 45 if workout_type == WorkoutType.STRENGTH else 30
            distance = 2.5 if workout_type == WorkoutType.RUN else None
            
            workouts.append({
                "name": name,
                "workout_type": workout_type,
                "intensity": WorkoutIntensity.MODERATE,
                "phase": phase,
                "week_number": week,
                "day_of_week": i,
                "scheduled_date": start_date + timedelta(days=i),
                "duration_minutes": duration,
                "distance_miles": distance,
                "description": f"Week {week} - {name}"
            })
        
        return workouts


class StrengthWorkoutGenerator(WorkoutGenerator):
    """Strength training generator."""
    
    def generate_week(self, week: int, phase: TrainingPhase, start_date: date, params: Dict) -> List[Dict]:
        workouts = []
        
        strength_days = ["Upper Body", "Lower Body", "Full Body", "Upper Body"]
        cardio_days = ["Recovery Cardio"]
        
        schedule = strength_days + cardio_days + [None, None]  # 4 strength, 1 cardio, 2 rest
        
        for i, workout_name in enumerate(schedule):
            if workout_name is None:
                workout_type = WorkoutType.REST
                name = "Rest"
                duration = 0
            elif "Cardio" in workout_name:
                workout_type = WorkoutType.RUN
                name = workout_name
                duration = 20
            else:
                workout_type = WorkoutType.STRENGTH
                name = f"Strength - {workout_name}"
                duration = 60
            
            workouts.append({
                "name": name,
                "workout_type": workout_type,
                "intensity": WorkoutIntensity.MODERATE,
                "phase": phase,
                "week_number": week,
                "day_of_week": i,
                "scheduled_date": start_date + timedelta(days=i),
                "duration_minutes": duration,
                "description": f"Week {week} strength training"
            })
        
        return workouts


class CyclingWorkoutGenerator(WorkoutGenerator):
    """Cycling-specific generator."""
    
    def generate_week(self, week: int, phase: TrainingPhase, start_date: date, params: Dict) -> List[Dict]:
        workouts = []
        base_distance = 10 + (week * 1)
        
        schedule = [
            (WorkoutType.BIKE, f"Base Ride - {base_distance}mi", base_distance),
            (WorkoutType.STRENGTH, "Leg Strength", None),
            (WorkoutType.BIKE, f"Interval Ride - {base_distance * 0.7}mi", base_distance * 0.7),
            (WorkoutType.REST, "Rest", None),
            (WorkoutType.BIKE, f"Tempo Ride - {base_distance * 0.8}mi", base_distance * 0.8),
            (WorkoutType.BIKE, f"Long Ride - {base_distance * 1.5}mi", base_distance * 1.5),
            (WorkoutType.REST, "Rest", None)
        ]
        
        for i, (workout_type, name, distance) in enumerate(schedule):
            duration = int(distance * 4) if distance else (45 if workout_type == WorkoutType.STRENGTH else 0)
            
            workouts.append({
                "name": name,
                "workout_type": workout_type,
                "intensity": WorkoutIntensity.MODERATE,
                "phase": phase,
                "week_number": week,
                "day_of_week": i,
                "scheduled_date": start_date + timedelta(days=i),
                "duration_minutes": duration,
                "distance_miles": distance,
                "description": f"Week {week} cycling training"
            })
        
        return workouts


class GeneralFitnessWorkoutGenerator(WorkoutGenerator):
    """General fitness generator."""
    
    def generate_week(self, week: int, phase: TrainingPhase, start_date: date, params: Dict) -> List[Dict]:
        workouts = []
        
        # Balanced approach
        schedule = [
            (WorkoutType.STRENGTH, "Full Body Strength"),
            (WorkoutType.RUN, "Cardio Run"),
            (WorkoutType.STRENGTH, "Upper Body Focus"),
            (WorkoutType.CROSS_TRAINING, "Flexibility/Yoga"),
            (WorkoutType.STRENGTH, "Lower Body Focus"),
            (WorkoutType.RUN, "Longer Cardio"),
            (WorkoutType.REST, "Rest")
        ]
        
        for i, (workout_type, name) in enumerate(schedule):
            duration = 45 if workout_type == WorkoutType.STRENGTH else 30
            distance = 2.0 if workout_type == WorkoutType.RUN else None
            
            workouts.append({
                "name": name,
                "workout_type": workout_type,
                "intensity": WorkoutIntensity.MODERATE,
                "phase": phase,
                "week_number": week,
                "day_of_week": i,
                "scheduled_date": start_date + timedelta(days=i),
                "duration_minutes": duration,
                "distance_miles": distance,
                "description": f"Week {week} general fitness"
            })
        
        return workouts


def generate_ai_training_plan(db: Session, goal: Goal, user: User) -> TrainingPlan:
    """Main function to generate AI training plan for any goal type."""
    generator = AITrainingPlanGenerator(goal, user)
    return generator.generate_plan(db)
