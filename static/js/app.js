// AtaraxAi - Athletic Training Platform JavaScript v2.0 - Goals fix, calendar fix, profile fix

class AtaraxAiApp {
    constructor() {
        this.apiBase = '/api/v1';
        this.currentUser = null;
        this.currentGoal = null;
        this.currentSection = 'landing';
        
        this.init();
    }

    async init() {
        console.log('AtaraxAi v1.1 - Initializing...');
        
        // Check for existing authentication
        const token = localStorage.getItem('auth_token');
        console.log('Token found:', !!token);
        
        if (token) {
            try {
                await this.loadUserProfile();
                console.log('User authenticated, showing dashboard');
                this.showDashboard();
            } catch (error) {
                console.log('Invalid token, showing landing page');
                localStorage.removeItem('auth_token');
                this.showLandingPage();
            }
        } else {
            console.log('No token found, showing landing page');
            this.showLandingPage();
        }

        this.setupEventListeners();
        this.handleURLNavigation(); // Handle direct URL navigation
        
        // SAFETY: Ensure all modals are hidden on initialization
        const goalModal = document.getElementById('goal-modal');
        goalModal.classList.add('hidden');
        goalModal.style.display = 'none';
        console.log('Goal modal forced hidden on init');
        
        const authModal = document.getElementById('auth-modal');
        authModal.classList.add('hidden');
        console.log('Auth modal forced hidden on init');
        
        this.hideLoading();
        console.log('AtaraxAi initialization complete');
    }

    setupEventListeners() {
        // Authentication
        document.getElementById('auth-btn').addEventListener('click', () => this.showAuthModal());
        document.getElementById('get-started-btn').addEventListener('click', () => this.showAuthModal());
        document.getElementById('close-auth').addEventListener('click', () => this.hideAuthModal());
        document.getElementById('show-register').addEventListener('click', () => this.showRegisterForm());
        document.getElementById('show-login').addEventListener('click', () => this.showLoginForm());
        document.getElementById('login-form').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('register-form').addEventListener('submit', (e) => this.handleRegister(e));

        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.getAttribute('href').substring(1);
                
                // Check authentication for protected sections
                if (['dashboard', 'goals', 'training', 'nutrition', 'profile'].includes(section)) {
                    if (!this.currentUser) {
                        this.showError('Please log in first to access this section.');
                        this.showAuthModal();
                        return;
                    }
                }
                
                this.showSection(section);
            });
        });

        // Goal creation
        document.getElementById('create-goal-btn').addEventListener('click', () => this.showGoalModal());
        document.getElementById('close-goal-modal').addEventListener('click', () => this.hideGoalModal());
        document.getElementById('close-goal-modal-x').addEventListener('click', () => this.hideGoalModal());
        document.getElementById('goal-form').addEventListener('submit', (e) => this.handleCreateGoal(e));
        
        // Click outside to close modals
        document.getElementById('goal-modal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('goal-modal')) {
                this.hideGoalModal();
            }
        });
        
        document.getElementById('auth-modal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('auth-modal')) {
                this.hideAuthModal();
            }
        });
        
        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (!document.getElementById('goal-modal').classList.contains('hidden')) {
                    this.hideGoalModal();
                }
                if (!document.getElementById('auth-modal').classList.contains('hidden')) {
                    this.hideAuthModal();
                }
            }
        });
        
        // Handle manual URL hash changes
        window.addEventListener('hashchange', () => {
            this.handleURLNavigation();
        });
        
        document.getElementById('goal-type').addEventListener('change', (e) => this.handleGoalTypeChange(e));

        // Set default event date to June 28, 2026
        document.getElementById('event-date').value = '2026-06-28';
    }
    
    handleURLNavigation() {
        // Check if user is trying to access a protected section via URL hash
        const hash = window.location.hash.substring(1); // Remove #
        const protectedSections = ['dashboard', 'goals', 'training', 'nutrition', 'profile'];
        
        if (protectedSections.includes(hash) && !this.currentUser) {
            console.log('Attempted to access protected section without auth:', hash);
            // Clear the URL hash and show auth modal
            window.location.hash = '';
            this.showAuthModal();
        }
    }

    // Authentication Methods
    async handleLogin(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const response = await this.apiCall('/auth/login', 'POST', {
                username,
                password
            });

            localStorage.setItem('auth_token', response.access_token);
            this.currentUser = response.user;
            
            // Explicitly hide modal before proceeding
            console.log('Login successful, hiding auth modal');
            this.hideAuthModal();
            
            this.showDashboard();
            await this.loadDashboardData();
        } catch (error) {
            this.showError('Invalid username or password');
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        
        const email = document.getElementById('reg-email').value;
        const username = document.getElementById('reg-username').value;
        const password = document.getElementById('reg-password').value;
        const full_name = document.getElementById('reg-name').value;

        try {
            await this.apiCall('/auth/register', 'POST', {
                email,
                username,
                password,
                full_name
            });

            // Auto-login after registration
            const loginResponse = await this.apiCall('/auth/login', 'POST', {
                username,
                password
            });

            localStorage.setItem('auth_token', loginResponse.access_token);
            this.currentUser = loginResponse.user;
            
            // Explicitly hide modal before proceeding
            console.log('Registration and login successful, hiding auth modal');
            this.hideAuthModal();
            
            // Show welcome message and immediately prompt for goal creation for new users
            this.showSuccess('Welcome to AtaraxAi! Let\'s create your first goal to get started.');
            this.showDashboard();
            
            // Automatically open goal creation modal for new users after a short delay
            setTimeout(() => {
                this.showGoalModal();
            }, 2000);
            
        } catch (error) {
            this.showError(error.detail || 'Registration failed');
        }
    }

    async loadUserProfile() {
        const user = await this.apiCall('/auth/me', 'GET');
        this.currentUser = user;
        document.getElementById('user-name').textContent = user.full_name || user.username;
        this.updateAuthButton();
    }

    logout() {
        localStorage.removeItem('auth_token');
        this.currentUser = null;
        this.currentGoal = null;
        this.showLandingPage();
        this.updateAuthButton();
    }

    // Goal Management
    handleGoalTypeChange(e) {
        const goalType = e.target.value;
        
        // Hide all goal-specific sections
        document.getElementById('race-distances').classList.add('hidden');
        document.getElementById('weight-goals').classList.add('hidden');
        document.getElementById('strength-goals').classList.add('hidden');
        
        // Show/hide distance fields based on goal type
        const swimGroup = document.getElementById('swim-distance-group');
        const bikeGroup = document.getElementById('bike-distance-group');
        const runGroup = document.getElementById('run-distance-group');
        
        // Reset visibility
        swimGroup.style.display = 'block';
        bikeGroup.style.display = 'block';
        runGroup.style.display = 'block';
        
        // Show relevant sections based on goal type
        if (['triathlon', 'ironman'].includes(goalType)) {
            document.getElementById('race-distances').classList.remove('hidden');
            // Set default triathlon distances
            document.getElementById('swim-distance').value = goalType === 'ironman' ? '3800' : '750';
            document.getElementById('bike-distance').value = goalType === 'ironman' ? '112' : '14.3';
            document.getElementById('run-distance').value = goalType === 'ironman' ? '26.2' : '3.1';
        } else if (['marathon', 'half_marathon', '10k', '5k'].includes(goalType)) {
            document.getElementById('race-distances').classList.remove('hidden');
            swimGroup.style.display = 'none';
            bikeGroup.style.display = 'none';
            
            const distances = {
                'marathon': '26.2',
                'half_marathon': '13.1',
                '10k': '6.2',
                '5k': '3.1'
            };
            document.getElementById('run-distance').value = distances[goalType] || '3.1';
        } else if (['cycling', 'century_ride'].includes(goalType)) {
            document.getElementById('race-distances').classList.remove('hidden');
            swimGroup.style.display = 'none';
            runGroup.style.display = 'none';
            
            document.getElementById('bike-distance').value = goalType === 'century_ride' ? '100' : '50';
        } else if (['weight_loss', 'muscle_gain'].includes(goalType)) {
            document.getElementById('weight-goals').classList.remove('hidden');
        } else if (goalType === 'strength_training') {
            document.getElementById('strength-goals').classList.remove('hidden');
        }
        
        // Update placeholder text based on goal
        const fitnessAssessment = document.getElementById('fitness-assessment');
        const placeholders = {
            'triathlon': 'e.g., Can run 1.5 miles, swim 200m, bike 5 miles. New to triathlon training.',
            'marathon': 'e.g., Can run 3 miles continuously, currently running 2x/week',
            'weight_loss': 'e.g., Currently 175lbs, want to lose 15lbs. Exercise 2x/week, mostly walking.',
            'strength_training': 'e.g., Beginner with weights, can bench 100lbs, squat bodyweight',
            'general_fitness': 'e.g., Sedentary lifestyle, want to get in shape, no current exercise routine'
        };
        
        fitnessAssessment.placeholder = placeholders[goalType] || fitnessAssessment.placeholder;
    }

    async handleCreateGoal(e) {
        console.log('🚀 handleCreateGoal called!');
        console.log('📝 Event details:', e);
        e.preventDefault();
        
        console.log('🎯 Starting goal creation process...');
        
        const goalType = document.getElementById('goal-type').value;
        const eventDate = document.getElementById('event-date').value;
        
        console.log('📊 Goal type:', goalType);
        console.log('📅 Event date:', eventDate);
        
        const goalData = {
            title: document.getElementById('goal-title').value,
            goal_type: goalType,
            description: document.getElementById('goal-description').value,
            event_date: eventDate || null,
            event_location: document.getElementById('event-location').value,
            current_fitness_assessment: document.getElementById('fitness-assessment').value,
            workouts_per_week: parseInt(document.getElementById('workouts-per-week').value),
            time_per_workout_minutes: parseInt(document.getElementById('workout-duration').value)
        };
        
        console.log('📋 Goal data collected:', goalData);

        // Add goal-specific data
        if (['triathlon', 'ironman', 'marathon', 'half_marathon', '10k', '5k', 'cycling', 'century_ride'].includes(goalType)) {
            if (document.getElementById('swim-distance-group').style.display !== 'none') {
                goalData.swim_distance_meters = parseFloat(document.getElementById('swim-distance').value) || null;
            }
            if (document.getElementById('bike-distance-group').style.display !== 'none') {
                goalData.bike_distance_miles = parseFloat(document.getElementById('bike-distance').value) || null;
            }
            if (document.getElementById('run-distance-group').style.display !== 'none') {
                goalData.run_distance_miles = parseFloat(document.getElementById('run-distance').value) || null;
            }
        }

        if (['weight_loss', 'muscle_gain'].includes(goalType)) {
            goalData.current_weight_lbs = parseFloat(document.getElementById('current-weight').value) || null;
            goalData.target_weight_lbs = parseFloat(document.getElementById('target-weight').value) || null;
        }

        if (goalType === 'strength_training') {
            goalData.target_bench_press_lbs = parseFloat(document.getElementById('target-bench').value) || null;
            goalData.target_squat_lbs = parseFloat(document.getElementById('target-squat').value) || null;
            goalData.target_deadlift_lbs = parseFloat(document.getElementById('target-deadlift').value) || null;
        }

        console.log('🔄 About to process goal-specific data...');
        
        try {
            console.log('🚀 Entering try block for API call...');
            
            // Show loading state
            const submitBtn = document.querySelector('#goal-modal .btn-primary');
            console.log('🔲 Submit button found:', submitBtn);
            
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Creating AI Training Plan...';
            submitBtn.disabled = true;
            
            console.log('🔄 Button state updated, showing info message...');
            
            // Show progress message
            this.showInfo('Generating AI training plan with Claude... This may take up to 30 seconds.');
            
            console.log('🌐 Making API call to /goals/ with data:', goalData);
            
            const goal = await this.apiCall('/goals/', 'POST', goalData);
            
            console.log('✅ API call successful! Goal created:', goal);
            this.currentGoal = goal;
            this.hideGoalModal();
            this.showSuccess('Goal and AI training plan created successfully!');
            await this.loadDashboardData();
            this.showSection('dashboard');
            
            // Reset button
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            
        } catch (error) {
            console.error('❌ Error in handleCreateGoal:', error);
            console.error('❌ Error type:', typeof error);
            console.error('❌ Error detail:', error.detail);
            console.error('❌ Full error object:', JSON.stringify(error, null, 2));
            
            // Reset button on error
            const submitBtn = document.querySelector('#goal-modal .btn-primary');
            if (submitBtn) {
                submitBtn.textContent = 'Create Goal & AI Training Plan';
                submitBtn.disabled = false;
            }
            
            const errorMessage = error.detail || error.message || 'Failed to create goal';
            console.error('❌ Showing error message:', errorMessage);
            this.showError(errorMessage);
        }
    }

    async loadGoals() {
        try {
            console.log('🔄 Loading goals...');
            const goals = await this.apiCall('/goals/', 'GET');
            console.log('✅ Goals loaded:', goals.length, 'goals');
            console.log('📊 Goals data:', goals);
            goals.forEach((goal, index) => {
                console.log(`Goal ${index + 1}:`, {
                    id: goal.id,
                    title: goal.title,
                    status: goal.status,
                    goal_type: goal.goal_type,
                    target_date: goal.target_date
                });
            });
            this.displayGoals(goals);
        } catch (error) {
            console.error('❌ Failed to load goals:', error);
        }
    }

    async loadTrainingData() {
        try {
            // Load training plans
            const plans = await this.apiCall('/training/plans', 'GET');
            this.displayTrainingPlans(plans);

            // Load current week workouts
            const workouts = await this.apiCall('/training/workouts/current', 'GET');
            this.displayWeeklyWorkouts(workouts);
            this.displayWorkoutCalendar(workouts);
        } catch (error) {
            console.error('Failed to load training data:', error);
            this.displayTrainingError();
        }
    }

    async loadNutritionData() {
        // Nutrition functionality is coming soon
        const nutritionContainer = document.getElementById('daily-nutrition');
        if (nutritionContainer) {
            nutritionContainer.innerHTML = `
                <div class="text-center p-6">
                    <div class="text-6xl mb-4">🍎</div>
                    <h3 class="text-lg font-semibold mb-2">Nutrition Plans Coming Soon!</h3>
                    <p class="text-gray-600">AI-generated meal plans and nutrition tracking will be available in a future update.</p>
                </div>
            `;
        }
    }

    async loadProfileData() {
        try {
            // Load user profile data
            const user = await this.apiCall('/auth/me', 'GET');
            this.displayUserProfile(user);
        } catch (error) {
            console.error('Failed to load profile data:', error);
            const profileContainer = document.getElementById('user-profile');
            if (profileContainer) {
                profileContainer.innerHTML = `
                    <div class="text-center p-6">
                        <p class="text-red-600">Failed to load profile information.</p>
                    </div>
                `;
            }
        }
    }

    async loadActiveGoal() {
        try {
            const goal = await this.apiCall('/goals/active', 'GET');
            this.currentGoal = goal;
            this.displayCurrentGoal(goal);
            return goal;
        } catch (error) {
            // No active goal
            return null;
        }
    }

    async loadDashboardState() {
        try {
            const dashboardData = await this.apiCall('/goals/dashboard', 'GET');
            this.dashboardData = dashboardData;
            this.currentGoal = dashboardData.active_goal;
            
            // Update dashboard based on user state
            this.updateDashboardForUserState(dashboardData);
            
            return dashboardData;
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            return null;
        }
    }

    // Dashboard Methods
    async loadDashboardData() {
        // Use the new dashboard state endpoint
        const dashboardData = await this.loadDashboardState();
        
        if (dashboardData && dashboardData.active_goal) {
            const goal = dashboardData.active_goal;
            document.getElementById('days-to-goal').textContent = goal.days_until_event || '--';
            document.getElementById('current-phase').textContent = goal.current_phase || 'Planning';
            document.getElementById('progress-percent').textContent = `${Math.round(goal.progress_percentage || 0)}%`;
            
            // Update progress bar if exists
            const progressBar = document.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = `${goal.progress_percentage || 0}%`;
            }
            
            // Load today's workouts
            await this.loadTodaysWorkouts();
        } else {
            // No active goal state
            document.getElementById('days-to-goal').textContent = '--';
            document.getElementById('current-phase').textContent = '--';
            document.getElementById('progress-percent').textContent = '--%';
            document.getElementById('todays-workout').innerHTML = '<p class="text-gray-600">No active goal. Create a goal to see your workouts!</p>';
        }
    }

    async loadTodaysWorkouts() {
        try {
            const workouts = await this.apiCall('/training/workouts/current', 'GET');
            this.displayTodaysWorkouts(workouts);
        } catch (error) {
            console.error('Failed to load today\'s workouts:', error);
            document.getElementById('todays-workout').innerHTML = '<p class="text-gray-600">Unable to load workouts.</p>';
        }
    }

    displayTodaysWorkouts(workouts) {
        const container = document.getElementById('todays-workout');
        
        if (!workouts || workouts.length === 0) {
            container.innerHTML = '<p class="text-gray-600">No workouts scheduled for today.</p>';
            return;
        }

        const todayWorkouts = workouts.filter(workout => {
            const today = new Date().getDay(); // 0=Sunday, 1=Monday, etc.
            const workoutDay = (workout.day_of_week + 1) % 7; // Convert to same format
            return workoutDay === today;
        });

        if (todayWorkouts.length === 0) {
            container.innerHTML = '<p class="text-gray-600">No workouts scheduled for today.</p>';
            return;
        }

        container.innerHTML = todayWorkouts.map(workout => `
            <div class="workout-item p-3 border border-gray-200 rounded mb-2">
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="font-medium">${workout.name}</h4>
                        <p class="text-sm text-gray-600">${workout.workout_type} • ${workout.intensity}</p>
                        ${workout.duration_minutes ? `<p class="text-sm text-gray-500">${workout.duration_minutes} minutes</p>` : ''}
                        ${workout.distance_miles ? `<p class="text-sm text-gray-500">${workout.distance_miles} miles</p>` : ''}
                    </div>
                    <div>
                        ${workout.is_completed ? 
                            '<span class="text-green-600 text-sm">✓ Completed</span>' : 
                            `<button class="btn btn-sm btn-primary" onclick="app.completeWorkout(${workout.id})">Complete</button>`
                        }
                    </div>
                </div>
            </div>
        `).join('');
    }

    async completeWorkout(workoutId) {
        try {
            await this.apiCall(`/training/workouts/${workoutId}/complete`, 'PUT');
            this.showSuccess('Workout completed! Great job! 🎉');
            await this.loadTodaysWorkouts(); // Refresh the workout display
        } catch (error) {
            this.showError('Failed to mark workout as completed');
        }
    }

    updateDashboardForUserState(dashboardData) {
        const currentGoalContainer = document.getElementById('current-goal');
        
        if (dashboardData.is_new_user) {
            // New user with no goals
            currentGoalContainer.innerHTML = `
                <div class="text-center p-6 bg-blue-50 border border-blue-200 rounded-lg">
                    <div class="text-4xl mb-4">🏃‍♂️</div>
                    <h3 class="text-lg font-semibold text-blue-900 mb-2">Welcome to AtaraxAi!</h3>
                    <p class="text-blue-700 mb-4">Ready to start your fitness journey? Create your first goal to get a personalized AI training plan.</p>
                    <button class="btn btn-primary" onclick="app.showGoalModal()">Create Your First Goal</button>
                </div>
            `;
        } else if (!dashboardData.active_goal && dashboardData.has_completed_goals) {
            // User with completed goals but no active goal
            currentGoalContainer.innerHTML = `
                <div class="text-center p-6 bg-green-50 border border-green-200 rounded-lg">
                    <div class="text-4xl mb-4">🏆</div>
                    <h3 class="text-lg font-semibold text-green-900 mb-2">Congratulations!</h3>
                    <p class="text-green-700 mb-4">You've completed ${dashboardData.completed_goals.length} goal(s). Ready for your next challenge?</p>
                    <button class="btn btn-primary" onclick="app.showGoalModal()">Set New Goal</button>
                    <div class="mt-4">
                        <h4 class="font-medium text-green-800 mb-2">Your Achievements:</h4>
                        <div class="text-sm">
                            ${dashboardData.completed_goals.map(goal => `
                                <div class="flex justify-between items-center py-1">
                                    <span>${goal.title}</span>
                                    <span class="text-green-600">✓ Completed</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        } else if (!dashboardData.active_goal) {
            // User with goals but no active goal
            currentGoalContainer.innerHTML = `
                <div class="text-center p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div class="text-4xl mb-4">🎯</div>
                    <h3 class="text-lg font-semibold text-yellow-900 mb-2">No Active Goal</h3>
                    <p class="text-yellow-700 mb-4">You have ${dashboardData.total_goals} goal(s) but none are currently active. Create a new goal or activate an existing one.</p>
                    <div class="space-x-2">
                        <button class="btn btn-primary" onclick="app.showGoalModal()">Create New Goal</button>
                        <button class="btn btn-outline" onclick="app.showSection('goals')">View All Goals</button>
                    </div>
                </div>
            `;
        } else {
            // User has active goal - use existing display
            this.displayCurrentGoal(dashboardData.active_goal);
        }
    }

    displayCurrentGoal(goal) {
        const container = document.getElementById('current-goal');
        if (!goal) {
            container.innerHTML = '<p class="text-gray-600">No active goal. <a href="#goals" class="text-primary">Create your first goal!</a></p>';
            return;
        }

        container.innerHTML = `
            <div class="mb-4">
                <h4 class="font-semibold">${goal.title}</h4>
                <p class="text-sm text-gray-600">${goal.description || ''}</p>
                <div class="mt-2">
                    <span class="phase-badge ${goal.current_phase}">${goal.current_phase}</span>
                </div>
            </div>
            <div class="text-sm text-gray-600">
                <p><strong>Event:</strong> ${new Date(goal.event_date).toLocaleDateString()}</p>
                <p><strong>Location:</strong> ${goal.event_location || 'Not specified'}</p>
                <p><strong>Distances:</strong> ${goal.swim_distance_meters}m swim, ${goal.bike_distance_miles}mi bike, ${goal.run_distance_miles}mi run</p>
            </div>
            <div class="mt-4">
                <div class="progress">
                    <div class="progress-bar" style="width: ${goal.progress_percentage}%"></div>
                </div>
                <p class="text-sm text-gray-600 mt-1">${Math.round(goal.progress_percentage)}% complete</p>
            </div>
        `;
    }

    displayGoals(goals) {
        console.log('🎯 displayGoals called with:', goals.length, 'goals');
        const container = document.getElementById('goals-list');
        console.log('📍 Container found:', !!container);
        
        if (goals.length === 0) {
            container.innerHTML = `
                <div class="card text-center">
                    <h3>No Goals Yet</h3>
                    <p class="text-gray-600 mb-4">Create your first athletic goal to get started with personalized training.</p>
                    <button class="btn btn-primary" id="first-goal-btn">Create Your First Goal</button>
                </div>
            `;
            
            // Add event listener for dynamically created button
            document.getElementById('first-goal-btn').addEventListener('click', () => this.showGoalModal());
            return;
        }

        // Separate goals by status (handle both uppercase and lowercase)
        const activeGoals = goals.filter(goal => goal.status?.toLowerCase() === 'active');
        const planningGoals = goals.filter(goal => goal.status?.toLowerCase() === 'planning');
        const completedGoals = goals.filter(goal => goal.status?.toLowerCase() === 'completed');
        const pausedGoals = goals.filter(goal => goal.status?.toLowerCase() === 'paused');
        
        console.log('🔍 Goal filtering results:');
        console.log('  Active:', activeGoals.length);
        console.log('  Planning:', planningGoals.length);
        console.log('  Paused:', pausedGoals.length);
        console.log('  Completed:', completedGoals.length);

        let html = '';

        // Active Goals Section
        if (activeGoals.length > 0) {
            html += `
                <div class="col-span-full">
                    <h2 class="text-xl font-semibold text-green-600 mb-4">🎯 Active Goals</h2>
                </div>
            `;
            html += activeGoals.map(goal => this.renderGoalCard(goal)).join('');
        }

        // Planning Goals Section
        if (planningGoals.length > 0) {
            html += `
                <div class="col-span-full">
                    <h2 class="text-xl font-semibold text-blue-600 mb-4">📋 Planning Goals</h2>
                </div>
            `;
            html += planningGoals.map(goal => this.renderGoalCard(goal)).join('');
        }

        // Paused Goals Section
        if (pausedGoals.length > 0) {
            html += `
                <div class="col-span-full">
                    <h2 class="text-xl font-semibold text-yellow-600 mb-4">⏸️ Paused Goals</h2>
                </div>
            `;
            html += pausedGoals.map(goal => this.renderGoalCard(goal)).join('');
        }

        // Completed Goals Section
        if (completedGoals.length > 0) {
            html += `
                <div class="col-span-full">
                    <h2 class="text-xl font-semibold text-gray-600 mb-4">🏆 Completed Goals</h2>
                </div>
            `;
            html += completedGoals.map(goal => this.renderGoalCard(goal)).join('');
        }

        container.innerHTML = html;
    }

    renderGoalCard(goal) {
        const eventDate = goal.event_date ? new Date(goal.event_date).toLocaleDateString() : 'No target date';
        const progressPercentage = goal.progress_percentage || 0;
        const daysRemaining = goal.days_until_event || '--';
        
        return `
            <div class="card">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-lg font-semibold">${goal.title}</h3>
                        <p class="text-sm text-gray-600">${eventDate}</p>
                        ${goal.description ? `<p class="text-sm text-gray-500 mt-1">${goal.description}</p>` : ''}
                    </div>
                    <span class="phase-badge ${goal.status}">${goal.status}</span>
                </div>
                
                <div class="progress mb-2">
                    <div class="progress-bar" style="width: ${progressPercentage}%"></div>
                </div>
                <div class="flex justify-between items-center text-sm text-gray-600 mb-3">
                    <span>${Math.round(progressPercentage)}% complete</span>
                    ${goal.status?.toLowerCase() === 'completed' ? 
                        '<span class="text-green-600 font-medium">✓ Completed!</span>' : 
                        `<span>${daysRemaining} days remaining</span>`
                    }
                </div>
                
                <div class="flex gap-2 flex-wrap">
                    ${goal.status?.toLowerCase() === 'planning' ? `
                        <button class="btn btn-primary btn-sm" onclick="app.activateGoal(${goal.id})">
                            Start Training
                        </button>
                        <button class="btn btn-outline btn-sm" onclick="app.deleteGoal(${goal.id})">
                            Delete
                        </button>
                    ` : ''}
                    ${goal.status?.toLowerCase() === 'paused' ? `
                        <button class="btn btn-primary btn-sm" onclick="app.activateGoal(${goal.id})">
                            Resume Training
                        </button>
                        <button class="btn btn-outline btn-sm" onclick="app.cancelGoal(${goal.id})">
                            Cancel Goal
                        </button>
                    ` : ''}
                    ${goal.status?.toLowerCase() === 'completed' ? `
                        <button class="btn btn-outline btn-sm" onclick="app.viewGoalDetails(${goal.id})">
                            View Details
                        </button>
                        <button class="btn btn-outline btn-sm text-orange-600" onclick="app.archiveGoal(${goal.id})">
                            Archive
                        </button>
                        <button class="btn btn-outline btn-sm text-red-600" onclick="app.deleteGoal(${goal.id})">
                            Delete
                        </button>
                    ` : ''}
                    ${goal.status?.toLowerCase() === 'active' ? `
                        <button class="btn btn-outline btn-sm" onclick="app.viewTrainingPlan(${goal.id})">
                            View Training Plan
                        </button>
                        <button class="btn btn-outline btn-sm text-yellow-600" onclick="app.pauseGoal(${goal.id})">
                            Pause
                        </button>
                        <button class="btn btn-outline btn-sm text-red-600" onclick="app.cancelGoal(${goal.id})">
                            Cancel & Quit
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    async activateGoal(goalId) {
        try {
            await this.apiCall(`/goals/${goalId}/activate`, 'POST');
            this.showSuccess('Goal activated! Your training plan is ready.');
            await this.loadDashboardData();
            this.showSection('dashboard');
        } catch (error) {
            this.showError('Failed to activate goal');
        }
    }

    async viewGoalDetails(goalId) {
        try {
            const goal = await this.apiCall(`/goals/${goalId}`, 'GET');
            this.showGoalDetailsModal(goal);
        } catch (error) {
            this.showError('Failed to load goal details');
        }
    }

    showGoalDetailsModal(goal) {
        // Create a simple details modal (could be expanded)
        this.showNotification(`Goal "${goal.title}" completed on ${new Date(goal.updated_at).toLocaleDateString()}`, 'success');
    }

    async viewTrainingPlan(goalId) {
        try {
            // For now, just show a success message and navigate to training section
            this.showSuccess('Training plan loaded! Check the Training section for your workouts.');
            this.showSection('training');
        } catch (error) {
            this.showError('Failed to load training plan');
        }
    }

    async pauseGoal(goalId) {
        if (!confirm('Are you sure you want to pause this goal? You can resume it later.')) {
            return;
        }
        
        try {
            await this.apiCall(`/goals/${goalId}/pause`, 'PUT');
            this.showSuccess('Goal paused. You can resume it anytime.');
            await this.loadGoals();
        } catch (error) {
            this.showError('Failed to pause goal');
        }
    }

    async cancelGoal(goalId) {
        if (!confirm('Are you sure you want to cancel this goal? This will stop all training and cannot be undone.')) {
            return;
        }
        
        try {
            await this.apiCall(`/goals/${goalId}/cancel`, 'PUT');
            this.showSuccess('Goal cancelled successfully.');
            await this.loadGoals();
            await this.loadDashboardData();
        } catch (error) {
            this.showError('Failed to cancel goal');
        }
    }

    async archiveGoal(goalId) {
        if (!confirm('Are you sure you want to archive this goal? It will be moved to archived goals.')) {
            return;
        }
        
        try {
            await this.apiCall(`/goals/${goalId}/archive`, 'PUT');
            this.showSuccess('Goal archived successfully.');
            await this.loadGoals();
        } catch (error) {
            this.showError('Failed to archive goal');
        }
    }

    async deleteGoal(goalId) {
        if (!confirm('Are you sure you want to permanently delete this goal? This action cannot be undone.')) {
            return;
        }
        
        try {
            await this.apiCall(`/goals/${goalId}`, 'DELETE');
            this.showSuccess('Goal deleted successfully.');
            await this.loadGoals();
            await this.loadDashboardData();
        } catch (error) {
            this.showError('Failed to delete goal');
        }
    }

    displayTrainingPlans(plans) {
        const container = document.getElementById('training-plans-list');
        if (!container) return;

        if (plans.length === 0) {
            container.innerHTML = `
                <div class="text-center p-6">
                    <div class="text-6xl mb-4">🏃‍♂️</div>
                    <h3 class="text-lg font-semibold mb-2">No Training Plans Yet</h3>
                    <p class="text-gray-600 mb-4">Create a goal to generate your first AI training plan!</p>
                    <button class="btn btn-primary" onclick="app.showSection('goals')">Create a Goal</button>
                </div>
            `;
            return;
        }

        let html = '';
        plans.forEach(plan => {
            html += `
                <div class="border rounded-lg p-4 mb-4">
                    <h4 class="font-semibold text-lg">${plan.name}</h4>
                    <p class="text-gray-600 mb-2">${plan.description}</p>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>Total Weeks: <span class="font-semibold">${plan.total_weeks}</span></div>
                        <div>Swim Sessions: <span class="font-semibold">${plan.weekly_swim_sessions}/week</span></div>
                        <div>Bike Sessions: <span class="font-semibold">${plan.weekly_bike_sessions}/week</span></div>
                        <div>Run Sessions: <span class="font-semibold">${plan.weekly_run_sessions}/week</span></div>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    }

    displayWeeklyWorkouts(workouts) {
        const container = document.getElementById('weekly-workouts');
        if (!container) return;

        if (workouts.length === 0) {
            container.innerHTML = `
                <div class="text-center p-4">
                    <p class="text-gray-600">No workouts scheduled for this week.</p>
                </div>
            `;
            return;
        }

        let html = '';
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        
        workouts.forEach(workout => {
            const dayName = workout.day_of_week < 7 ? days[workout.day_of_week] : 'Rest';
            const isToday = workout.day_of_week === new Date().getDay();
            
            html += `
                <div class="border rounded p-3 mb-2 ${isToday ? 'bg-blue-50 border-blue-200' : ''}">
                    <div class="flex justify-between items-center">
                        <div>
                            <div class="font-semibold text-sm">${dayName}</div>
                            <div class="text-sm">${workout.name}</div>
                        </div>
                        <div class="text-xs text-gray-600">${workout.duration_minutes}min</div>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    }

    displayWorkoutCalendar(workouts) {
        const container = document.getElementById('workout-calendar');
        if (!container) return;

        if (workouts.length === 0) {
            container.innerHTML = `
                <div class="text-center p-6">
                    <p class="text-gray-600">No workouts to display.</p>
                </div>
            `;
            return;
        }

        // Get current week start (Monday)
        const today = new Date();
        const currentDayOfWeek = today.getDay(); // 0 = Sunday, 1 = Monday, etc.
        const daysToMonday = (currentDayOfWeek === 0 ? 6 : currentDayOfWeek - 1);
        const monday = new Date(today);
        monday.setDate(today.getDate() - daysToMonday);

        const daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        
        // Group workouts by day of week
        const workoutsByDay = {};
        workouts.forEach(workout => {
            const dayIndex = workout.day_of_week; // 0 = Monday, 1 = Tuesday, etc.
            if (!workoutsByDay[dayIndex]) {
                workoutsByDay[dayIndex] = [];
            }
            workoutsByDay[dayIndex].push(workout);
        });

        // Build calendar table
        let html = `
            <div class="w-full">
                <table class="w-full border-collapse">
                    <thead>
                        <tr>
        `;

        // Header row with dates
        for (let i = 0; i < 7; i++) {
            const currentDate = new Date(monday);
            currentDate.setDate(monday.getDate() + i);
            const dateStr = currentDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            
            html += `
                <th class="border p-2 bg-gray-100 text-center text-xs font-semibold">
                    <div>${daysOfWeek[i]}</div>
                    <div class="text-gray-600 font-normal">${dateStr}</div>
                </th>
            `;
        }

        html += `
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
        `;

        // Create workout cells for each day
        for (let day = 0; day < 7; day++) {
            const dayWorkouts = workoutsByDay[day] || [];
            
            html += '<td class="border p-2 align-top" style="width: 14.28%; min-height: 100px;">';
            
            if (dayWorkouts.length > 0) {
                dayWorkouts.forEach(workout => {
                    const workoutColor = this.getWorkoutColor(workout.workout_type);
                    
                    // Clean up workout name and format properly
                    let cleanName = workout.name;
                    if (cleanName.includes(' - ')) {
                        cleanName = cleanName.split(' - ')[0];
                    }
                    
                    // Format duration properly
                    const duration = workout.duration_minutes;
                    let durationText = `${duration} min`;
                    
                    // Format distance based on workout type
                    let distanceText = '';
                    if (workout.distance_miles && workout.distance_miles > 0) {
                        if (workout.workout_type === 'swim') {
                            // Convert miles to yards for swimming (1 mile = 1760 yards)
                            const yards = Math.round(workout.distance_miles * 1760);
                            distanceText = ` • ${yards} yds`;
                        } else {
                            distanceText = ` • ${workout.distance_miles.toFixed(1)} mi`;
                        }
                    }
                    
                    html += `
                        <div class="mb-1 border rounded p-1 text-xs ${workoutColor} cursor-pointer hover:opacity-80"
                             onclick="app.showWorkoutDetails(${workout.id})">
                            <div class="font-semibold truncate">${cleanName}</div>
                            <div class="text-xs opacity-75">${durationText}${distanceText}</div>
                        </div>
                    `;
                });
            } else {
                html += `<div class="text-center text-gray-400 text-xs py-2">Rest Day</div>`;
            }
            
            html += '</td>';
        }
        
        html += `
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = html;
    }

    getWorkoutColor(workoutType) {
        const colors = {
            'run': 'bg-red-50 border-red-200 text-red-800',
            'bike': 'bg-blue-50 border-blue-200 text-blue-800', 
            'swim': 'bg-cyan-50 border-cyan-200 text-cyan-800',
            'strength': 'bg-purple-50 border-purple-200 text-purple-800',
            'rest': 'bg-gray-50 border-gray-200 text-gray-600',
            'cross_training': 'bg-green-50 border-green-200 text-green-800'
        };
        return colors[workoutType] || 'bg-gray-50 border-gray-200 text-gray-600';
    }

    showWorkoutDetails(workoutId) {
        // TODO: Implement workout details modal
        console.log('Show workout details for:', workoutId);
    }

    displayTrainingError() {
        const container = document.getElementById('training-plans-list');
        if (container) {
            container.innerHTML = `
                <div class="text-center p-6">
                    <p class="text-red-600">Failed to load training data. Please try again.</p>
                </div>
            `;
        }
    }

    displayUserProfile(user) {
        const container = document.getElementById('user-profile');
        if (!container) return;

        container.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-center space-x-4">
                    <div class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                        ${user.full_name ? user.full_name.charAt(0).toUpperCase() : user.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <h3 class="text-lg font-semibold">${user.full_name || user.username}</h3>
                        <p class="text-gray-600">${user.email}</p>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <label class="font-semibold">Username:</label>
                        <p>${user.username}</p>
                    </div>
                    <div>
                        <label class="font-semibold">Email:</label>
                        <p>${user.email}</p>
                    </div>
                    <div>
                        <label class="font-semibold">Full Name:</label>
                        <p>${user.full_name || 'Not set'}</p>
                    </div>
                    <div>
                        <label class="font-semibold">Member Since:</label>
                        <p>${new Date(user.created_at).toLocaleDateString()}</p>
                    </div>
                </div>
            </div>
        `;
    }

    // UI State Management
    showSection(section) {
        // Hide all sections
        document.querySelectorAll('section').forEach(s => s.classList.add('hidden'));
        
        // Show target section
        const targetSection = document.getElementById(`${section}-section`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            this.currentSection = section;
        }

        // Load section data
        if (section === 'goals') {
            this.loadGoals();
        } else if (section === 'dashboard') {
            this.loadDashboardData();
        } else if (section === 'training') {
            this.loadTrainingData();
        } else if (section === 'nutrition') {
            this.loadNutritionData();
        } else if (section === 'profile') {
            this.loadProfileData();
        }

        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${section}`) {
                link.classList.add('active');
            }
        });
    }

    showLandingPage() {
        this.showSection('landing');
        this.updateAuthButton();
    }

    showDashboard() {
        // Ensure auth modal is hidden when showing dashboard
        this.hideAuthModal();
        this.showSection('dashboard');
        this.updateAuthButton();
    }

    updateAuthButton() {
        const authBtn = document.getElementById('auth-btn');
        const navLinks = document.querySelectorAll('.nav-link');
        
        if (this.currentUser) {
            authBtn.textContent = 'Logout';
            authBtn.onclick = () => this.logout();
            
            // Show navigation links for authenticated users
            navLinks.forEach(link => {
                link.style.display = 'block';
            });
        } else {
            authBtn.textContent = 'Login';
            authBtn.onclick = () => this.showAuthModal();
            
            // Hide navigation links for non-authenticated users
            navLinks.forEach(link => {
                link.style.display = 'none';
            });
        }
    }

    // Modal Management
    showAuthModal() {
        console.log('showAuthModal called');
        const authModal = document.getElementById('auth-modal');
        authModal.classList.remove('hidden');
        authModal.style.display = 'flex'; // Ensure modal is displayed
        this.showLoginForm();
    }

    hideAuthModal() {
        console.log('Hiding auth modal');
        const authModal = document.getElementById('auth-modal');
        authModal.classList.add('hidden');
        authModal.style.display = 'none'; // Force hide with inline style as backup
        this.clearAuthForms();
    }

    showLoginForm() {
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('register-form').classList.add('hidden');
        document.getElementById('auth-title').textContent = 'Welcome Back';
    }

    showRegisterForm() {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
        document.getElementById('auth-title').textContent = 'Create Account';
    }

    showGoalModal() {
        console.log('showGoalModal called, currentUser:', !!this.currentUser);
        
        // EMERGENCY: Force close goal modal if it's already showing
        const modal = document.getElementById('goal-modal');
        modal.classList.add('hidden');
        modal.style.display = 'none';
        
        // Check if user is authenticated first
        if (!this.currentUser) {
            console.log('User not authenticated, showing auth modal instead');
            // Don't show error, just directly show auth modal for better UX
            this.showAuthModal();
            return;
        }
        
        console.log('User authenticated, showing goal modal');
        modal.classList.remove('hidden');
        modal.style.display = 'flex'; // Override the !important none
    }

    hideGoalModal() {
        const modal = document.getElementById('goal-modal');
        modal.classList.add('hidden');
        modal.style.display = 'none';
        document.getElementById('goal-form').reset();
        // Reset default date
        document.getElementById('event-date').value = '2026-06-28';
    }
    
    // Emergency method to force close all modals and show auth
    forceShowAuth() {
        console.log('EMERGENCY: Force closing all modals and showing auth');
        const goalModal = document.getElementById('goal-modal');
        goalModal.classList.add('hidden');
        goalModal.style.display = 'none';
        document.getElementById('auth-modal').classList.remove('hidden');
        this.showLoginForm();
    }

    clearAuthForms() {
        document.getElementById('login-form').reset();
        document.getElementById('register-form').reset();
    }

    hideLoading() {
        document.getElementById('loading').classList.add('hidden');
    }

    // Utility Methods
    async apiCall(endpoint, method = 'GET', data = null) {
        console.log(`🌐 API Call: ${method} ${endpoint}`);
        console.log('📦 Request data:', data);
        
        const token = localStorage.getItem('auth_token');
        console.log('🔑 Auth token found:', !!token);
        
        const headers = {
            'Content-Type': 'application/json',
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            method,
            headers,
        };

        if (data) {
            config.body = JSON.stringify(data);
        }

        console.log('🚀 Making fetch request to:', `${this.apiBase}${endpoint}`);
        console.log('⚙️ Request config:', config);

        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, config);
            console.log('📡 Response received:', response.status, response.statusText);
            
            if (!response.ok) {
                console.error('❌ Response not OK:', response.status, response.statusText);
                const errorData = await response.json().catch(() => ({}));
                console.error('❌ Error data:', errorData);
                throw errorData;
            }

            const result = await response.json();
            console.log('✅ Response data:', result);
            return result;
        } catch (fetchError) {
            console.error('❌ Fetch error:', fetchError);
            throw fetchError;
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 1rem;
            right: 1rem;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            color: white;
            font-weight: 500;
            z-index: 2000;
            max-width: 300px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        `;

        // Set color based on type
        if (type === 'success') {
            notification.style.backgroundColor = '#10b981';
        } else if (type === 'error') {
            notification.style.backgroundColor = '#ef4444';
        } else {
            notification.style.backgroundColor = '#3b82f6';
        }

        notification.textContent = message;
        document.body.appendChild(notification);

        // Remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

// Initialize the application
const app = new AtaraxAiApp();
