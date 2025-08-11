"""
Claude-powered AI training plan generation.
Uses Anthropic's Claude API to create personalized training plans.
"""
import json
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import anthropic

from app.core.config import settings
from app.models.goal import Goal, GoalType
from app.models.training import (
    TrainingPlan, 
    Workout, 
    WorkoutType, 
    WorkoutIntensity, 
    TrainingPhase
)
from app.models.user import User


class ClaudeTrainingGenerator:
    """AI-powered training plan generator using Claude."""
    
    def __init__(self):
        """Initialize the Claude client."""
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=30.0  # 30 second timeout
        )
    
    def create_training_plan(self, db: Session, goal: Goal, user: User) -> TrainingPlan:
        """Create an AI-generated training plan using Claude."""
        
        # Calculate plan duration based on event date
        if goal.event_date:
            days_available = (goal.event_date - date.today()).days
            total_weeks = max(8, days_available // 7)
        else:
            total_weeks = 16
        
        try:
            # Generate training plan with Claude
            plan_data = self._generate_plan_with_claude(goal, user, total_weeks)
            
            # Create the training plan record
            training_plan = TrainingPlan(
                goal_id=goal.id,
                name=plan_data.get("name", f"{goal.title} - AI Training Plan"),
                description=plan_data.get("description", "AI-generated training plan"),
                total_weeks=total_weeks,
                base_weeks=plan_data.get("base_weeks", total_weeks // 2),
                build_weeks=plan_data.get("build_weeks", total_weeks // 3),
                peak_weeks=plan_data.get("peak_weeks", 2),
                taper_weeks=plan_data.get("taper_weeks", 1),
                weekly_swim_sessions=plan_data.get("weekly_swim_sessions", 0),
                weekly_bike_sessions=plan_data.get("weekly_bike_sessions", 0),
                weekly_run_sessions=plan_data.get("weekly_run_sessions", 0),
                weekly_strength_sessions=plan_data.get("weekly_strength_sessions", 2),
                is_generated=True
            )
            
            db.add(training_plan)
            db.commit()
            db.refresh(training_plan)
            
            # Generate workouts using Claude
            self._generate_workouts_with_claude(db, training_plan, goal, user, plan_data)
            
        except Exception as e:
            print(f"Error in Claude training plan generation: {e}")
            # Rollback any partial changes
            db.rollback()
            raise e
        
        return training_plan
    
    def _generate_plan_with_claude(self, goal: Goal, user: User, total_weeks: int) -> Dict[str, Any]:
        """Use Claude to generate the high-level training plan structure."""
        
        # Calculate age from birth date if available
        age_info = ""
        if hasattr(goal, 'birth_date') and goal.birth_date:
            from datetime import date
            age = date.today().year - goal.birth_date.year
            age_info = f"- Age: {age} years old"
        
        # Format medical conditions info
        medical_info = ""
        if hasattr(goal, 'medical_conditions') and goal.medical_conditions:
            medical_info = f"- Medical Conditions/Injuries: {goal.medical_conditions}"
        
        # Format training experience
        experience_info = ""
        if hasattr(goal, 'training_experience') and goal.training_experience:
            experience_info = f"- Training Experience: {goal.training_experience}"
        
        # Format current weight
        weight_info = ""
        if hasattr(goal, 'current_weight_lbs') and goal.current_weight_lbs:
            weight_info = f"- Current Weight: {goal.current_weight_lbs} lbs"
        
        prompt = f"""You are an expert athletic training coach and exercise physiologist. Create a personalized training plan for this athlete:

ATHLETE PROFILE:
- Goal: {goal.title}
- Goal Type: {goal.goal_type.value}
- Goal Description: {goal.description or 'None provided'}
- Event Date: {goal.event_date or 'No specific date'}
- Training Duration: {total_weeks} weeks
{age_info}
{weight_info}
{experience_info}
{medical_info}

CURRENT FITNESS ASSESSMENT:
{goal.current_fitness_assessment or 'Not provided'}

TRAINING PREFERENCES:
- Workouts per week: {getattr(goal, 'workouts_per_week', 4)}
- Preferred workout duration: {getattr(goal, 'time_per_workout_minutes', 45)} minutes

SAFETY AND PERSONALIZATION REQUIREMENTS:
1. Consider the athlete's age for appropriate training intensities and recovery
2. Account for any medical conditions or injuries in workout design
3. Scale difficulty based on training experience level
4. Create progressive, achievable goals that match their current fitness
5. Include proper warm-up, cool-down, and recovery protocols

PLAN STRUCTURE REQUIREMENTS:
1. Create realistic, evidence-based periodization (base, build, peak, taper phases)
2. Determine appropriate weekly session counts for different activities
3. Ensure the plan scales properly to the event date and available time
4. Include injury prevention strategies appropriate for the goal type

Please respond with a JSON object containing:
{{
    "name": "Training plan name",
    "description": "Brief description of the plan approach and key adaptations",
    "base_weeks": number_of_base_training_weeks,
    "build_weeks": number_of_build_training_weeks, 
    "peak_weeks": number_of_peak_training_weeks,
    "taper_weeks": number_of_taper_weeks,
    "weekly_swim_sessions": sessions_per_week_or_0,
    "weekly_bike_sessions": sessions_per_week_or_0,
    "weekly_run_sessions": sessions_per_week_or_0,
    "weekly_strength_sessions": sessions_per_week,
    "training_philosophy": "Detailed explanation of the coaching approach, key adaptations for this athlete, and safety considerations"
}}

Focus on creating a safe, personalized, and achievable plan. Consider the athlete's specific circumstances, limitations, and goals."""

        try:
            print(f"Calling Claude API for plan generation...")
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            print(f"Claude API call completed successfully")
            
            # Extract JSON from Claude's response
            response_text = response.content[0].text
            print(f"Claude plan response: {response_text}")  # Debug log
            
            # Find JSON in the response (Claude might include explanatory text)
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                plan_data = json.loads(json_str)
                print(f"Parsed plan data: {plan_data}")  # Debug log
                return plan_data
            else:
                print(f"No JSON found in response: {response_text}")
                raise ValueError("No valid JSON found in Claude's response")
                
        except Exception as e:
            print(f"Error calling Claude API for plan generation: {e}")
            # Fallback to simple plan structure
            return self._fallback_plan_structure(goal, total_weeks)
    
    def _generate_workouts_with_claude(self, db: Session, plan: TrainingPlan, goal: Goal, user: User, plan_data: Dict[str, Any]):
        """Use Claude to generate specific workouts for each week."""
        
        for week_num in range(1, plan.total_weeks + 1):
            # Determine training phase
            if week_num <= plan.base_weeks:
                phase = TrainingPhase.BASE
            elif week_num <= plan.base_weeks + plan.build_weeks:
                phase = TrainingPhase.BUILD
            elif week_num <= plan.base_weeks + plan.build_weeks + plan.peak_weeks:
                phase = TrainingPhase.PEAK
            else:
                phase = TrainingPhase.TAPER
            
            # Generate workouts for this week
            week_workouts = self._generate_week_workouts_with_claude(
                goal, week_num, phase, plan, plan_data
            )
            
            # Create workout records
            week_start = date.today() + timedelta(weeks=week_num-1)
            
            for day_idx, workout_data in enumerate(week_workouts):
                if workout_data:  # Skip rest days (None entries)
                    print(f"Processing workout for day {day_idx}: {workout_data}")  # Debug log
                    
                    # Ensure workout_data is a dictionary
                    if not isinstance(workout_data, dict):
                        print(f"Error: workout_data is not a dict: {type(workout_data)} - {workout_data}")
                        continue
                    
                    try:
                        workout = Workout(
                            training_plan_id=plan.id,
                            name=workout_data.get("name", f"Workout {day_idx + 1}"),
                            workout_type=WorkoutType(workout_data.get("type", "rest")),
                            intensity=WorkoutIntensity(workout_data.get("intensity", "easy")),
                            phase=phase,
                            week_number=week_num,
                            day_of_week=day_idx,
                            duration_minutes=workout_data.get("duration", 30),
                            distance_miles=workout_data.get("distance", 0.0),
                            description=workout_data.get("description", ""),
                            instructions=workout_data.get("instructions", ""),
                            scheduled_date=week_start + timedelta(days=day_idx)
                        )
                        db.add(workout)
                    except Exception as workout_error:
                        print(f"Error creating workout for day {day_idx}: {workout_error}")
                        continue
        
        db.commit()
    
    def _generate_week_workouts_with_claude(self, goal: Goal, week_num: int, phase: TrainingPhase, plan: TrainingPlan, plan_data: Dict[str, Any]) -> List[Optional[Dict[str, Any]]]:
        """Generate workouts for a specific week using Claude."""
        
        prompt = f"""Create 7 specific workouts for week {week_num} of a {plan.total_weeks}-week training plan.

PLAN CONTEXT:
- Goal: {goal.title} ({goal.goal_type.value})
- Current Phase: {phase.value}
- Week: {week_num} of {plan.total_weeks}
- Training Philosophy: {plan_data.get('training_philosophy', 'Progressive training')}

WEEKLY SESSION TARGETS:
- Swimming: {plan.weekly_swim_sessions} sessions/week
- Biking: {plan.weekly_bike_sessions} sessions/week  
- Running: {plan.weekly_run_sessions} sessions/week
- Strength: {plan.weekly_strength_sessions} sessions/week

GUIDELINES:
1. Create exactly 7 workouts (Monday-Sunday)
2. Include rest days as null
3. Progressive difficulty based on week number
4. Appropriate intensity for {phase.value} phase
5. Realistic durations and distances
6. Include warm-up/cool-down in duration

Respond with a JSON array of 7 items (one per day), where each workout is:
{{
    "name": "Workout name",
    "type": "run|bike|swim|strength|rest|cross_training",
    "intensity": "easy|moderate|hard|very_hard",
    "duration": minutes_as_integer,
    "distance": miles_as_float_or_0_for_non_distance,
    "description": "Brief workout description",
    "instructions": "Specific workout instructions"
}}

Use null for rest days. Make it realistic and progressive."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.content[0].text
            print(f"Claude workout response for week {week_num}: {response_text}")  # Debug log
            
            # Find JSON array in the response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                workouts = json.loads(json_str)
                print(f"Parsed workouts for week {week_num}: {workouts}")  # Debug log
                
                # Ensure we have exactly 7 items
                if len(workouts) != 7:
                    print(f"Warning: Expected 7 workouts, got {len(workouts)} for week {week_num}")
                
                return workouts
            else:
                print(f"No JSON array found in workout response for week {week_num}: {response_text}")
                raise ValueError("No valid JSON array found in Claude's response")
                
        except Exception as e:
            print(f"Error calling Claude API for week {week_num} workouts: {e}")
            # Fallback to simple week generation
            return self._fallback_week_workouts(goal, week_num, phase)
    
    def _fallback_plan_structure(self, goal: Goal, total_weeks: int) -> Dict[str, Any]:
        """Fallback plan structure if Claude API fails."""
        
        if goal.goal_type in [GoalType.TRIATHLON, GoalType.IRONMAN]:
            return {
                "name": f"{goal.title} - AI Training Plan",
                "description": "Comprehensive triathlon training plan",
                "base_weeks": total_weeks // 2,
                "build_weeks": total_weeks // 3,
                "peak_weeks": 2,
                "taper_weeks": 1,
                "weekly_swim_sessions": 3,
                "weekly_bike_sessions": 3,
                "weekly_run_sessions": 3,
                "weekly_strength_sessions": 2,
                "training_philosophy": "Progressive triathlon training"
            }
        else:
            return {
                "name": f"{goal.title} - AI Training Plan", 
                "description": "Progressive training plan",
                "base_weeks": total_weeks // 2,
                "build_weeks": total_weeks // 3,
                "peak_weeks": 2,
                "taper_weeks": 1,
                "weekly_swim_sessions": 0,
                "weekly_bike_sessions": 1,
                "weekly_run_sessions": 4,
                "weekly_strength_sessions": 2,
                "training_philosophy": "Progressive endurance training"
            }
    
    def _fallback_week_workouts(self, goal: Goal, week_num: int, phase: TrainingPhase) -> List[Optional[Dict[str, Any]]]:
        """Simple fallback workouts if Claude API fails."""
        
        intensity = "easy" if phase == TrainingPhase.BASE else "moderate"
        
        return [
            {"name": "Rest Day", "type": "rest", "intensity": "easy", "duration": 0, "distance": 0.0, "description": "Complete rest", "instructions": "Rest and recover"},
            {"name": f"Run - Week {week_num}", "type": "run", "intensity": intensity, "duration": 30 + week_num * 2, "distance": 2.0 + week_num * 0.2, "description": "Easy run", "instructions": "Maintain conversational pace"},
            {"name": "Strength Training", "type": "strength", "intensity": "moderate", "duration": 45, "distance": 0.0, "description": "Full body strength", "instructions": "Focus on major muscle groups"},
            {"name": f"Bike - Week {week_num}", "type": "bike", "intensity": intensity, "duration": 45 + week_num * 3, "distance": 8.0 + week_num * 0.5, "description": "Endurance ride", "instructions": "Steady effort"},
            {"name": "Cross Training", "type": "cross_training", "intensity": "easy", "duration": 30, "distance": 0.0, "description": "Active recovery", "instructions": "Light activity"},
            {"name": f"Long Workout - Week {week_num}", "type": "run", "intensity": "moderate", "duration": 60 + week_num * 5, "distance": 5.0 + week_num * 0.5, "description": "Long endurance session", "instructions": "Build endurance"},
            {"name": "Rest Day", "type": "rest", "intensity": "easy", "duration": 0, "distance": 0.0, "description": "Complete rest", "instructions": "Rest and recover"}
        ]


def create_claude_training_plan(db: Session, goal: Goal, user: User) -> TrainingPlan:
    """Create a training plan using Claude AI."""
    generator = ClaudeTrainingGenerator()
    return generator.create_training_plan(db, goal, user)
