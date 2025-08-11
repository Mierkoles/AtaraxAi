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
                if (!document.getElementById('workout-modal').classList.contains('hidden')) {
                    this.hideWorkoutModal();
                }
                if (!document.getElementById('workout-completion-modal').classList.contains('hidden')) {
                    this.hideWorkoutCompletionModal();
                }
            }
        });
        
        // Handle manual URL hash changes
        window.addEventListener('hashchange', () => {
            this.handleURLNavigation();
        });
        
        document.getElementById('goal-type').addEventListener('change', (e) => this.handleGoalTypeChange(e));

        // Workout modal
        document.getElementById('close-workout-modal').addEventListener('click', () => this.hideWorkoutModal());
        document.getElementById('workout-modal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('workout-modal')) {
                this.hideWorkoutModal();
            }
        });

        // Workout completion modal
        document.getElementById('close-completion-modal').addEventListener('click', () => this.hideWorkoutCompletionModal());
        document.getElementById('cancel-completion').addEventListener('click', () => this.hideWorkoutCompletionModal());
        document.getElementById('workout-completion-modal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('workout-completion-modal')) {
                this.hideWorkoutCompletionModal();
            }
        });
        document.getElementById('workout-completion-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleWorkoutCompletionSubmit(e);
        });

        // Profile form handlers
        document.getElementById('profile-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleProfileUpdate(e);
        });
        document.getElementById('load-profile-btn').addEventListener('click', () => this.loadUserProfile());

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
        console.log('Goal creation started');
        e.preventDefault();
        
        const goalType = document.getElementById('goal-type').value;
        const goalTitle = document.getElementById('goal-title').value;
        const fitnessAssessment = document.getElementById('fitness-assessment').value;
        
        // Validate required fields before proceeding
        if (!goalType) {
            this.showNotification('error', 'Validation Error', 'Please select a goal type.');
            return;
        }
        
        if (!goalTitle.trim()) {
            this.showNotification('error', 'Validation Error', 'Please enter a goal title.');
            return;
        }
        
        if (!fitnessAssessment.trim()) {
            this.showNotification('error', 'Validation Error', 'Please describe your current fitness level.');
            return;
        }
        
        // Show AI progress modal immediately
        this.showAIProgressModal();
        
        // Hide the goal creation modal
        this.hideGoalModal();
        
        const eventDate = document.getElementById('event-date').value;
        
        // Collect all form data
        const goalData = {
            title: goalTitle,
            goal_type: goalType,
            description: document.getElementById('goal-description').value,
            event_date: eventDate || null,
            event_location: document.getElementById('event-location').value,
            current_fitness_assessment: fitnessAssessment
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
            goalData.target_weight_lbs = parseFloat(document.getElementById('target-weight').value) || null;
        }

        if (goalType === 'strength_training') {
            goalData.target_bench_press_lbs = parseFloat(document.getElementById('target-bench').value) || null;
            goalData.target_squat_lbs = parseFloat(document.getElementById('target-squat').value) || null;
            goalData.target_deadlift_lbs = parseFloat(document.getElementById('target-deadlift').value) || null;
        }

        console.log('🔄 About to process goal-specific data...');
        
        try {
            console.log('Starting API call to create goal...');
            
            const response = await this.apiCall('/goals/', 'POST', goalData);
            console.log('Goal creation API response:', response);
            
            this.currentGoal = response;
            
            // Hide AI progress modal
            this.hideAIProgressModal();
            
            // Show completion notification
            this.showNotification('success', 'Training Plan Ready!', 
                'Your personalized AI training plan has been generated and is ready to view.');
            
            // Reset form for future use
            document.getElementById('goal-form').reset();
            document.getElementById('event-date').value = '2026-06-28';
            
            // Reload dashboard data to show new plan
            await this.loadDashboardData();
            console.log('Dashboard data reloaded after goal creation');
            
            // Navigate to training section to show the new plan
            this.showSection('training');
            
        } catch (error) {
            console.error('Error in handleCreateGoal:', error);
            
            // Hide AI progress modal
            this.hideAIProgressModal();
            
            const errorMessage = error.detail || error.message || 'Failed to create goal';
            this.showNotification('error', 'Training Plan Generation Failed', errorMessage);
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
            // Make sure we have goal data
            if (!this.currentGoal) {
                try {
                    const dashboardData = await this.apiCall('/goals/dashboard', 'GET');
                    this.currentGoal = dashboardData.active_goal;
                } catch (goalError) {
                    console.log('No active goal found for timeline');
                }
            }

            // Load training plans
            const plans = await this.apiCall('/training/plans', 'GET');
            this.displayTrainingPlans(plans);

            // Load current week workouts for sidebar
            const currentWorkouts = await this.apiCall('/training/workouts/current', 'GET');
            this.displayWeeklyWorkouts(currentWorkouts);
            
            // Load all workouts for calendar view
            const allWorkouts = await this.apiCall('/training/workouts', 'GET');
            this.displayWorkoutCalendar(allWorkouts);
            
            // Display timeline if we have an active goal
            // Timeline removed from Training page - now only on Dashboard
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
        
        // Display motivational quote
        this.displayMotivationalQuote();
        
        if (dashboardData && dashboardData.active_goal) {
            const goal = dashboardData.active_goal;
            document.getElementById('days-to-goal').textContent = goal.days_until_event || '--';
            const currentPhase = goal.current_phase || 'Base';
            const phaseElement = document.getElementById('current-phase');
            phaseElement.textContent = currentPhase;
            
            // Add tooltip to current phase stat
            const phaseTooltips = {
                'Base': 'Building aerobic fitness and establishing training routine. Focus on easy-paced workouts to develop cardiovascular base.',
                'Build': 'Increasing training intensity and sport-specific skills. Adding tempo work, intervals, and race-pace training.',
                'Peak': 'Highest intensity training with race simulation. Fine-tuning performance for peak fitness on event day.',
                'Taper': 'Reducing training volume while maintaining intensity. Allowing body to recover for peak race day performance.'
            };
            phaseElement.title = phaseTooltips[currentPhase] || 'Current training phase';
            let enhancedProgress = dashboardData.enhanced_progress || 0;
            const completedWorkouts = dashboardData.completed_workouts_count || 0;
            
            // Ensure at least 1% if any workouts completed
            if (completedWorkouts > 0 && enhancedProgress < 1) {
                enhancedProgress = 1;
            }
            
            document.getElementById('progress-percent').textContent = `${Math.round(enhancedProgress)}%`;
            document.getElementById('workouts-completed').textContent = completedWorkouts;
            
            // Update progress bar if exists
            const progressBar = document.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = `${enhancedProgress}%`;
            }
            
            // Show and update dashboard timeline
            this.updateDashboardTimeline(goal);
            
            // Load today's workouts
            await this.loadTodaysWorkouts();
        } else {
            // No active goal state
            document.getElementById('days-to-goal').textContent = '--';
            document.getElementById('current-phase').textContent = '--';
            document.getElementById('progress-percent').textContent = '--%';
            document.getElementById('workouts-completed').textContent = '--';
            document.getElementById('todays-workout').innerHTML = '<p class="text-gray-600">No active goal. Create a goal to see your workouts!</p>';
            
            // Hide dashboard timeline
            const dashboardTimeline = document.getElementById('dashboard-timeline');
            if (dashboardTimeline) {
                dashboardTimeline.classList.add('hidden');
            }
        }
    }

    updateDashboardTimeline(goal) {
        const dashboardTimeline = document.getElementById('dashboard-timeline');
        if (!dashboardTimeline || !goal) {
            return;
        }
        
        // Show timeline
        dashboardTimeline.classList.remove('hidden');
        
        // Update title and subtitle
        document.getElementById('dashboard-timeline-title').textContent = goal.title;
        document.getElementById('dashboard-timeline-subtitle').textContent = 
            `${goal.total_weeks || 16} week training plan • Week ${goal.current_week || 1} of ${goal.total_weeks || 16}`;
        
        // Calculate phase widths as percentages
        const baseWeeks = goal.base_weeks || 6;
        const buildWeeks = goal.build_weeks || 6;
        const peakWeeks = goal.peak_weeks || 2;
        const taperWeeks = goal.taper_weeks || 2;
        const totalWeeks = baseWeeks + buildWeeks + peakWeeks + taperWeeks;
        
        const basePercent = (baseWeeks / totalWeeks * 100).toFixed(1);
        const buildPercent = (buildWeeks / totalWeeks * 100).toFixed(1);
        const peakPercent = (peakWeeks / totalWeeks * 100).toFixed(1);
        const taperPercent = (taperWeeks / totalWeeks * 100).toFixed(1);
        
        // Update timeline phases with tooltips
        const phasesContainer = document.getElementById('dashboard-timeline-phases');
        phasesContainer.innerHTML = `
            <div class="timeline-phase phase-base" style="width: ${basePercent}%" 
                 title="BASE PHASE: Building aerobic fitness and establishing training routine. Focus on easy-paced, longer duration workouts to develop your cardiovascular base and movement patterns.">
                Base
            </div>
            <div class="timeline-phase phase-build" style="width: ${buildPercent}%" 
                 title="BUILD PHASE: Increasing training intensity and sport-specific skills. Adding tempo work, intervals, and race-pace training to build strength and speed.">
                Build
            </div>
            <div class="timeline-phase phase-peak" style="width: ${peakPercent}%" 
                 title="PEAK PHASE: Highest intensity training with race simulation. Fine-tuning performance and practicing race tactics for peak fitness on event day.">
                Peak
            </div>
            <div class="timeline-phase phase-taper" style="width: ${taperPercent}%" 
                 title="TAPER PHASE: Reducing training volume while maintaining intensity. Allowing body to recover and be fresh for peak performance on race day.">
                Taper
            </div>
        `;
        
        // Calculate phase end dates
        const startDate = new Date(goal.created_at || Date.now());
        
        const baseEndDate = new Date(startDate);
        baseEndDate.setDate(startDate.getDate() + (baseWeeks * 7));
        
        const buildEndDate = new Date(startDate);
        buildEndDate.setDate(startDate.getDate() + ((baseWeeks + buildWeeks) * 7));
        
        const peakEndDate = new Date(startDate);
        peakEndDate.setDate(startDate.getDate() + ((baseWeeks + buildWeeks + peakWeeks) * 7));
        
        const finalEndDate = new Date(startDate);
        finalEndDate.setDate(startDate.getDate() + (totalWeeks * 7));
        
        // Update bottom markers with phase end dates
        const bottomMarkersContainer = dashboardTimeline.querySelector('.timeline-markers-bottom');
        if (bottomMarkersContainer) {
            // Calculate cumulative percentages for phase boundaries
            const baseEndPercent = (baseWeeks / totalWeeks * 100);
            const buildEndPercent = ((baseWeeks + buildWeeks) / totalWeeks * 100);
            const peakEndPercent = ((baseWeeks + buildWeeks + peakWeeks) / totalWeeks * 100);
            
            bottomMarkersContainer.innerHTML = `
                <div class="timeline-marker start" style="position: absolute; left: 0%; transform: translateX(-50%);">
                    <div class="timeline-marker-dot"></div>
                    <div class="timeline-marker-label">${this.formatDate(startDate)}</div>
                </div>
                <div class="timeline-marker phase-end" style="position: absolute; left: ${baseEndPercent}%; transform: translateX(-50%);">
                    <div class="timeline-marker-dot"></div>
                    <div class="timeline-marker-label">${this.formatDate(baseEndDate)}</div>
                </div>
                <div class="timeline-marker phase-end" style="position: absolute; left: ${buildEndPercent}%; transform: translateX(-50%);">
                    <div class="timeline-marker-dot"></div>
                    <div class="timeline-marker-label">${this.formatDate(buildEndDate)}</div>
                </div>
                <div class="timeline-marker phase-end" style="position: absolute; left: ${peakEndPercent}%; transform: translateX(-50%);">
                    <div class="timeline-marker-dot"></div>
                    <div class="timeline-marker-label">${this.formatDate(peakEndDate)}</div>
                </div>
                <div class="timeline-marker finish" style="position: absolute; left: 100%; transform: translateX(-50%);">
                    <div class="timeline-marker-dot"></div>
                    <div class="timeline-marker-label">${this.formatDate(finalEndDate)}</div>
                </div>
            `;
        }
        
        // Position the "You are Here" marker based on current week
        const currentWeek = goal.current_week || 1;
        const progressPercent = ((currentWeek - 1) / totalWeeks * 100).toFixed(1);
        
        // Update top markers container positioning
        const topMarkersContainer = dashboardTimeline.querySelector('.timeline-markers-top');
        if (topMarkersContainer) {
            const currentMarker = topMarkersContainer.querySelector('.timeline-marker.current');
            if (currentMarker) {
                // Position the current marker using absolute positioning within the relative container
                currentMarker.style.position = 'absolute';
                currentMarker.style.left = `${progressPercent}%`;
                currentMarker.style.transform = 'translateX(-50%)';
            }
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
            const today = new Date();
            const workoutDate = this.getWorkoutDate(workout);
            return this.isSameDay(workoutDate, today);
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
                        ${workout.is_completed || (this.completedWorkoutIds && this.completedWorkoutIds.has(workout.id)) ? 
                            '<span class="text-green-600 text-sm">✓ Completed</span>' : 
                            `<button class="btn btn-sm btn-primary" onclick="app.completeWorkout(${workout.id})">Complete</button>`
                        }
                    </div>
                </div>
            </div>
        `).join('');
    }

    async completeWorkout(workoutId) {
        // Find the workout to show its details in the modal
        let workout = null;
        if (this.currentWorkouts) {
            workout = this.currentWorkouts.find(w => w.id === workoutId);
        }
        
        this.showWorkoutCompletionModal(workoutId, workout);
    }
    
    showWorkoutCompletionModal(workoutId, workout) {
        const modal = document.getElementById('workout-completion-modal');
        const form = document.getElementById('workout-completion-form');
        
        // Set workout ID in hidden field
        document.getElementById('completion-workout-id').value = workoutId;
        
        // Update modal header with workout details
        if (workout) {
            document.getElementById('completion-modal-title').textContent = `How did "${workout.name}" go?`;
            document.getElementById('completion-modal-meta').innerHTML = `
                <span class="workout-meta-item">${workout.workout_type} • ${workout.intensity}</span>
                ${workout.duration_minutes ? `<span class="workout-meta-item">⏱️ ${workout.duration_minutes} min</span>` : ''}
            `;
            
            // Pre-fill actual duration if we have planned duration
            if (workout.duration_minutes) {
                document.getElementById('actual-duration').value = workout.duration_minutes;
            }
        }
        
        // Reset form
        form.reset();
        
        // Show modal
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
    }

    async submitWorkoutCompletion(completionData) {
        try {
            const workoutId = completionData.workout_id;
            
            // Immediately update UI to show completion
            const button = document.querySelector(`[data-workout-id="${workoutId}"]`);
            if (button) {
                const workoutActions = button.closest('.workout-actions');
                if (workoutActions) {
                    workoutActions.innerHTML = `
                        <div class="completion-message" style="text-align: center; padding: 0.75rem; background: var(--success); color: white; border-radius: 6px; font-weight: 600;">
                            🎉 Excellent work! Workout completed!
                        </div>
                    `;
                }
            }
            
            // Make API call with feedback data
            await this.apiCall(`/training/workouts/${workoutId}/complete`, 'PUT', completionData);
            this.showNotification('success', 'Workout Complete!', 'Thanks for your feedback! This helps us improve your training plan. 🎉');
            
            // Store completed workout ID to prevent UI refresh from overwriting completion state
            if (!this.completedWorkoutIds) {
                this.completedWorkoutIds = new Set();
            }
            this.completedWorkoutIds.add(workoutId);
            
            // Mark the workout as completed locally to prevent UI refresh issues
            if (this.currentWorkouts) {
                const workout = this.currentWorkouts.find(w => w.id === workoutId);
                if (workout) {
                    workout.completed = true;
                    workout.is_completed = true;
                }
            }
            
            // Hide modal
            this.hideWorkoutCompletionModal();
            
            // Only refresh dashboard (not training section to preserve the completion message)
            await this.loadTodaysWorkouts(); // Refresh dashboard only
            
        } catch (error) {
            // Remove from completed set if API call failed
            if (this.completedWorkoutIds) {
                this.completedWorkoutIds.delete(completionData.workout_id);
            }
            
            // Revert UI change if API call failed
            const completionMessage = document.querySelector('.completion-message');
            if (completionMessage) {
                const workoutActions = completionMessage.closest('.workout-actions');
                if (workoutActions) {
                    workoutActions.innerHTML = `
                        <button class="btn btn-primary btn-sm complete-workout-btn" onclick="event.stopPropagation(); app.completeWorkout(${completionData.workout_id})" style="width: 100%;" data-workout-id="${completionData.workout_id}">
                            ✓ Complete Today's Workout
                        </button>
                    `;
                }
            }
            this.showNotification('error', 'Error', 'Failed to mark workout as completed');
        }
    }
    
    hideWorkoutCompletionModal() {
        const modal = document.getElementById('workout-completion-modal');
        modal.classList.add('hidden');
        modal.style.display = 'none';
    }
    
    async handleWorkoutCompletionSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const completionData = {
            workout_id: parseInt(document.getElementById('completion-workout-id').value),
            perceived_exertion: parseInt(formData.get('perceived_exertion') || formData.get('perceived-exertion')),
            energy_level: parseInt(formData.get('energy_level') || formData.get('energy-level')),
            enjoyment_level: parseInt(formData.get('enjoyment_level') || formData.get('enjoyment-level')),
            actual_duration_minutes: parseInt(formData.get('actual_duration') || formData.get('actual-duration')) || null,
            weather_conditions: formData.get('weather_conditions') || formData.get('weather-conditions') || null,
            notes: formData.get('workout_notes') || formData.get('workout-notes') || null
        };
        
        // Remove null/undefined values
        Object.keys(completionData).forEach(key => {
            if (completionData[key] === null || completionData[key] === undefined || isNaN(completionData[key])) {
                if (key !== 'notes' && key !== 'weather_conditions' && key !== 'actual_duration_minutes') {
                    delete completionData[key];
                }
            }
        });
        
        await this.submitWorkoutCompletion(completionData);
    }
    
    async handleProfileUpdate(e) {
        e.preventDefault();
        
        const birth_date = document.getElementById('profile-birth-date').value;
        const weight_lbs = parseFloat(document.getElementById('profile-weight').value);
        const height_inches = document.getElementById('profile-height').value ? parseFloat(document.getElementById('profile-height').value) : null;
        const bmi_known = document.getElementById('profile-bmi').value ? parseFloat(document.getElementById('profile-bmi').value) : null;
        const body_type = document.getElementById('profile-body-type').value || null;
        const fitness_level = document.getElementById('profile-fitness-level').value;
        const medical_conditions = document.getElementById('profile-medical').value || null;

        try {
            await this.apiCall('/auth/profile', 'PUT', {
                birth_date,
                weight_lbs,
                height_inches,
                bmi_known,
                body_type,
                fitness_level,
                medical_conditions
            });

            this.showNotification('success', 'Profile Updated', 'Your athletic profile has been saved successfully!');
            
            // Refresh user data
            await this.loadUserProfile();
            
        } catch (error) {
            this.showNotification('error', 'Error', 'Failed to update profile. Please try again.');
        }
    }
    
    async loadUserProfileData() {
        try {
            const profile = await this.apiCall('/auth/me', 'GET');
            
            // Update account info
            const accountInfo = document.getElementById('user-account-info');
            if (accountInfo) {
                accountInfo.innerHTML = `
                    <div class="space-y-2">
                        <div><strong>Email:</strong> ${profile.email}</div>
                        <div><strong>Username:</strong> ${profile.username}</div>
                        <div><strong>Display Name:</strong> ${profile.full_name || 'Not set'}</div>
                        <div><strong>Member Since:</strong> ${new Date(profile.created_at).toLocaleDateString()}</div>
                        <div><strong>Age:</strong> ${profile.age ? profile.age + ' years old' : 'Not set'}</div>
                        <div><strong>BMI:</strong> ${profile.bmi ? profile.bmi.toFixed(1) : 'Not calculated'}</div>
                    </div>
                `;
            }
            
            // Pre-fill profile form
            if (profile.birth_date) document.getElementById('profile-birth-date').value = profile.birth_date;
            if (profile.weight_lbs) document.getElementById('profile-weight').value = profile.weight_lbs;
            if (profile.height_inches) document.getElementById('profile-height').value = profile.height_inches;
            if (profile.bmi_known) document.getElementById('profile-bmi').value = profile.bmi_known;
            if (profile.body_type) document.getElementById('profile-body-type').value = profile.body_type;
            if (profile.fitness_level) document.getElementById('profile-fitness-level').value = profile.fitness_level;
            if (profile.medical_conditions) document.getElementById('profile-medical').value = profile.medical_conditions;
            
            return profile;
        } catch (error) {
            console.error('Failed to load profile data:', error);
            return null;
        }
    }

    isProfileCompleteForGoals(user) {
        const requiredFields = ['birth_date', 'weight_lbs', 'fitness_level'];
        return requiredFields.every(field => user[field] !== null && user[field] !== undefined && user[field] !== '');
    }

    getMissingProfileFields(user) {
        const missing = [];
        if (!user.birth_date) missing.push('Birth Date');
        if (!user.weight_lbs) missing.push('Weight');
        if (!user.fitness_level) missing.push('Training Experience Level');
        return missing;
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
        `;
    }

    // Motivational Quotes System
    getMotivationalQuotes() {
        return [
            // Stoic Philosophy Quotes
            {
                text: "You have power over your mind - not outside events. Realize this, and you will find strength.",
                author: "Marcus Aurelius"
            },
            {
                text: "The impediment to action advances action. What stands in the way becomes the way.",
                author: "Marcus Aurelius"
            },
            {
                text: "It is not the man who has too little, but the man who craves more, who is poor.",
                author: "Seneca"
            },
            {
                text: "No person was ever honored for what he received. Honor has been the reward for what he gave.",
                author: "Calvin Coolidge"
            },
            {
                text: "Man is disturbed not by things, but by the views he takes of them.",
                author: "Epictetus"
            },
            {
                text: "First say to yourself what you would be; and then do what you have to do.",
                author: "Epictetus"
            },
            {
                text: "The best revenge is not to be like your enemy.",
                author: "Marcus Aurelius"
            },
            {
                text: "Wealth consists in not having great possessions, but in having few wants.",
                author: "Epictetus"
            },
            {
                text: "Every new beginning comes from some other beginning's end.",
                author: "Seneca"
            },
            {
                text: "He is not poor who has little, but he who wants more.",
                author: "Seneca"
            },
            // Athletic & Achievement Quotes
            {
                text: "The miracle isn't that I finished. The miracle is that I had the courage to start.",
                author: "John Bingham"
            },
            {
                text: "Champions aren't made in gyms. Champions are made from something deep inside them: a desire, a dream, a vision.",
                author: "Muhammad Ali"
            },
            {
                text: "Success isn't given. It's earned. On the track, on the field, in the gym. With blood, sweat, and the occasional tear.",
                author: "Nike"
            },
            {
                text: "The only impossible journey is the one you never begin.",
                author: "Tony Robbins"
            },
            {
                text: "Your body can stand almost anything. It's your mind that you have to convince.",
                author: "Unknown"
            },
            {
                text: "Don't limit your challenges. Challenge your limits.",
                author: "Unknown"
            },
            {
                text: "Pain is temporary. Quitting lasts forever.",
                author: "Lance Armstrong"
            },
            {
                text: "The cave you fear to enter holds the treasure you seek.",
                author: "Joseph Campbell"
            },
            {
                text: "Strength does not come from physical capacity. It comes from an indomitable will.",
                author: "Mahatma Gandhi"
            },
            {
                text: "A goal is a dream with a deadline.",
                author: "Napoleon Hill"
            },
            // More Stoic Wisdom
            {
                text: "Today I escaped anxiety. Or no, I discarded it, because it was within me, in my own perceptions—not outside.",
                author: "Marcus Aurelius"
            },
            {
                text: "The mind that is anxious about future misfortunes is miserable.",
                author: "Seneca"
            },
            {
                text: "We suffer more in imagination than in reality.",
                author: "Seneca"
            },
            {
                text: "Difficulties strengthen the mind, as labor does the body.",
                author: "Seneca"
            },
            {
                text: "It is likely that some troubles will befall us; but it is not a present fact. How often has the unexpected happened! How often has the expected never come to pass!",
                author: "Seneca"
            }
        ];
    }

    displayMotivationalQuote() {
        const quoteSection = document.getElementById('motivational-quote-section');
        const quoteText = document.getElementById('quote-text');
        const quoteAuthor = document.getElementById('quote-author');
        
        if (!quoteSection || !quoteText || !quoteAuthor) {
            return;
        }

        const quotes = this.getMotivationalQuotes();
        
        // Get today's date and use it to select a quote consistently for the day
        const today = new Date();
        const dayOfYear = Math.floor((today - new Date(today.getFullYear(), 0, 0)) / (1000 * 60 * 60 * 24));
        const selectedQuote = quotes[dayOfYear % quotes.length];
        
        quoteText.textContent = selectedQuote.text;
        quoteAuthor.textContent = `— ${selectedQuote.author}`;
        
        // Show the quote section
        quoteSection.classList.remove('hidden');
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
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];  // Start with Sunday
        const today = new Date();
        
        // Sort workouts by day (Sunday = 0, Saturday = 6)
        workouts.sort((a, b) => a.day_of_week - b.day_of_week);
        
        let workoutNumber = 1; // Start numbering from 1
        
        workouts.forEach(workout => {
            const dayName = workout.day_of_week < 7 ? days[workout.day_of_week] : 'Rest';
            
            // Calculate the actual date for this workout
            const workoutDate = this.getWorkoutDate(workout);
            const isToday = this.isSameDay(workoutDate, today);
            const isPast = workoutDate < today && !isToday;
            
            // Check completion status (handle different field names from API and local completion tracking)
            const isCompleted = workout.completed || workout.is_completed || 
                               (this.completedWorkoutIds && this.completedWorkoutIds.has(workout.id)) || false;
            
            const workoutIcon = this.getWorkoutIcon(workout.workout_type);
            const phaseClass = `phase-${workout.phase?.toLowerCase() || 'base'}`;
            const intensityClass = `intensity-${workout.intensity?.toLowerCase().replace(' ', '-') || 'easy'}`;
            
            // Additional CSS classes
            const todayClass = isToday ? 'today' : '';
            const completedClass = (isPast || isCompleted) ? 'completed' : '';
            
            // Format duration and distance
            let durationText = `⏱️ ${workout.duration_minutes || 0}min`;
            let distanceText = '';
            if (workout.distance_miles) {
                distanceText = ` | 📏 ${workout.distance_miles}mi`;
            } else if (workout.workout_type === 'SWIM' && workout.total_yards) {
                distanceText = ` | <span class="swim-yards">${workout.total_yards}y</span>`;
            }
            
            html += `
                <div class="workout-card ${phaseClass} ${todayClass} ${completedClass}" onclick="app.showWorkoutDetails(${workout.id})" style="position: relative;">
                    <div class="workout-number">${workoutNumber}</div>
                    <div class="intensity-indicator ${intensityClass}"></div>
                    <div class="workout-card-header">
                        <h3 class="workout-title">
                            <span class="workout-icon">${workoutIcon}</span>
                            ${workout.name}
                        </h3>
                        ${workout.phase ? `<span class="phase-badge ${workout.phase.toLowerCase()}">${workout.phase}</span>` : ''}
                    </div>
                    <div class="workout-meta">
                        <span class="workout-meta-item">📅 ${dayName}, ${this.formatDate(workoutDate)}</span>
                        <span class="workout-meta-item">${durationText}${distanceText}</span>
                        <span class="workout-meta-item">💪 ${workout.intensity || 'Easy'}</span>
                    </div>
                    ${workout.description ? `<div class="workout-description">${workout.description}</div>` : ''}
                    ${workout.instructions ? `<div class="workout-instructions">${workout.instructions}</div>` : ''}
                    ${isToday && !isPast ? 
                        (isCompleted ? 
                            `<div class="workout-actions completed-workout-actions" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--gray-200);">
                                <div class="completion-message" style="text-align: center; padding: 0.75rem; background: var(--success); color: white; border-radius: 6px; font-weight: 600;">
                                    🎉 Excellent work! Workout completed!
                                </div>
                            </div>` :
                            `<div class="workout-actions" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--gray-200);">
                                <button class="btn btn-primary btn-sm complete-workout-btn" onclick="event.stopPropagation(); app.completeWorkout(${workout.id})" style="width: 100%;" data-workout-id="${workout.id}">
                                    ✓ Complete Today's Workout
                                </button>
                            </div>`
                        ) : ''}
                </div>
            `;
            workoutNumber++;
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
                    
                    const phaseClass = workout.phase ? `phase-${workout.phase.toLowerCase()}` : '';
                    const workoutIcon = this.getWorkoutIcon(workout.workout_type);
                    
                    html += `
                        <div class="workout-mini-card ${phaseClass}" 
                             style="border-left-color: ${this.getIntensityColor(workout.intensity)}"
                             onclick="app.showWorkoutDetails(${workout.id})"
                             title="${workout.instructions || workout.description || workout.name}">
                            <div class="font-semibold truncate">
                                <span style="font-size: 0.8rem;">${workoutIcon}</span> ${cleanName}
                            </div>
                            <div class="text-xs opacity-75">${durationText}${distanceText}</div>
                            ${workout.phase ? `<div class="text-xs opacity-60">${workout.phase} Phase</div>` : ''}
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

    getWorkoutIcon(workoutType) {
        const icons = {
            'RUN': '🏃‍♂️',
            'BIKE': '🚴‍♂️',
            'SWIM': '🏊‍♂️',
            'STRENGTH': '💪',
            'CROSS_TRAINING': '🧘‍♂️',
            'REST': '😴'
        };
        return icons[workoutType] || '🏃‍♂️';
    }

    getIntensityColor(intensity) {
        const colors = {
            'RECOVERY': '#4caf50',
            'EASY': '#8bc34a',
            'MODERATE': '#ff9800',
            'HARD': '#f44336',
            'VERY_HARD': '#9c27b0'
        };
        return colors[intensity] || colors['EASY'];
    }

    async showWorkoutDetails(workoutId) {
        try {
            const workout = await this.apiCall(`/training/workouts/${workoutId}`, 'GET');
            this.displayWorkoutModal(workout);
        } catch (error) {
            console.error('Failed to load workout details:', error);
            this.showError('Failed to load workout details');
        }
    }

    displayWorkoutModal(workout) {
        const modal = document.getElementById('workout-modal');
        const title = document.getElementById('workout-modal-title');
        const meta = document.getElementById('workout-modal-meta');
        const description = document.getElementById('workout-modal-description');
        const instructions = document.getElementById('workout-modal-instructions');
        const details = document.getElementById('workout-modal-details');

        // Set title with icon
        const workoutIcon = this.getWorkoutIcon(workout.workout_type);
        title.innerHTML = `${workoutIcon} ${workout.name}`;

        // Set meta information
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const dayName = workout.day_of_week < 7 ? days[workout.day_of_week] : 'Rest Day';
        
        let durationText = `⏱️ ${workout.duration_minutes || 0} minutes`;
        let distanceText = '';
        if (workout.distance_miles) {
            distanceText = ` | 📏 ${workout.distance_miles} miles`;
        } else if (workout.workout_type === 'SWIM' && workout.total_yards) {
            distanceText = ` | 🏊‍♂️ ${workout.total_yards} yards`;
        }

        meta.innerHTML = `
            <div class="workout-meta-item">📅 ${dayName}</div>
            <div class="workout-meta-item">${durationText}${distanceText}</div>
            <div class="workout-meta-item">💪 ${workout.intensity || 'Easy'} Intensity</div>
            ${workout.phase ? `<div class="workout-meta-item"><span class="phase-badge ${workout.phase.toLowerCase()}">${workout.phase} Phase</span></div>` : ''}
        `;

        // Set description
        if (workout.description) {
            description.textContent = workout.description;
            document.getElementById('workout-description-section').style.display = 'block';
        } else {
            document.getElementById('workout-description-section').style.display = 'none';
        }

        // Set instructions
        if (workout.instructions) {
            instructions.textContent = workout.instructions;
            document.getElementById('workout-instructions-section').style.display = 'block';
        } else {
            document.getElementById('workout-instructions-section').style.display = 'none';
        }

        // Set workout details
        let detailsHtml = `
            <div><strong>Workout Type:</strong> ${workout.workout_type?.replace('_', ' ') || 'Unknown'}</div>
            <div><strong>Week:</strong> ${workout.week_number || 1}</div>
        `;
        
        if (workout.scheduled_date) {
            detailsHtml += `<div><strong>Scheduled:</strong> ${new Date(workout.scheduled_date).toLocaleDateString()}</div>`;
        }
        
        if (workout.workout_type === 'SWIM' && workout.total_yards) {
            detailsHtml += `<div><strong>Total Distance:</strong> ${workout.total_yards} yards</div>`;
        }
        
        details.innerHTML = detailsHtml;

        // Show modal
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
    }

    hideWorkoutModal() {
        const modal = document.getElementById('workout-modal');
        modal.classList.add('hidden');
        modal.style.display = 'none';
    }

    showAIProgressModal() {
        const modal = document.getElementById('ai-progress-modal');
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
    }

    hideAIProgressModal() {
        const modal = document.getElementById('ai-progress-modal');
        modal.classList.add('hidden');
        modal.style.display = 'none';
    }

    showNotification(type, title, message) {
        const container = document.getElementById('notification-container');
        const notificationId = 'notification-' + Date.now();
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.id = notificationId;
        
        const icons = {
            success: '✓',
            info: 'ℹ',
            warning: '⚠',
            error: '✕'
        };
        
        notification.innerHTML = `
            <button class="notification-close" onclick="app.removeNotification('${notificationId}')">&times;</button>
            <div class="notification-header">
                <span>${icons[type] || 'ℹ'}</span>
                <span>${title}</span>
            </div>
            <div class="notification-body">${message}</div>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove after 8 seconds for success/info, 12 seconds for warning/error
        const autoRemoveTime = (type === 'success' || type === 'info') ? 8000 : 12000;
        setTimeout(() => {
            this.removeNotification(notificationId);
        }, autoRemoveTime);
    }

    removeNotification(notificationId) {
        const notification = document.getElementById(notificationId);
        if (notification) {
            notification.style.transform = 'translateX(100%)';
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
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

    async showGoalModal() {
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
        
        // Check if user profile is complete for goal creation
        try {
            const user = await this.apiCall('/auth/me', 'GET');
            if (!this.isProfileCompleteForGoals(user)) {
                const missingFields = this.getMissingProfileFields(user);
                this.showNotification('warning', 'Profile Incomplete', 
                    `Please complete your profile before creating a goal. Missing: ${missingFields.join(', ')}`);
                this.showSection('profile');
                return;
            }
        } catch (error) {
            console.error('Error checking profile completeness:', error);
            this.showNotification('error', 'Error', 'Unable to verify profile completeness. Please try again.');
            return;
        }
        
        console.log('User authenticated and profile complete, showing goal modal');
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

    // Helper functions for date handling and timeline
    getWorkoutDate(workout) {
        // Use scheduled_date if available (preferred method)
        if (workout.scheduled_date) {
            return new Date(workout.scheduled_date);
        }
        
        // Fallback: Calculate workout date based on plan start date and week/day
        if (!this.currentGoal || !this.currentGoal.created_at) {
            // Fallback to current date if no goal data
            const today = new Date();
            const dayOffset = workout.day_of_week - today.getDay();
            const workoutDate = new Date(today);
            workoutDate.setDate(today.getDate() + dayOffset + ((workout.week_number - 1) * 7));
            return workoutDate;
        }
        
        const planStartDate = new Date(this.currentGoal.created_at);
        const workoutDate = new Date(planStartDate);
        
        // Add weeks (week_number - 1 because week 1 starts on plan creation)
        workoutDate.setDate(planStartDate.getDate() + ((workout.week_number - 1) * 7));
        
        // Add days to get to the specific day of week
        const dayOffset = workout.day_of_week - planStartDate.getDay();
        workoutDate.setDate(workoutDate.getDate() + dayOffset);
        
        return workoutDate;
    }
    
    isSameDay(date1, date2) {
        return date1.getFullYear() === date2.getFullYear() &&
               date1.getMonth() === date2.getMonth() &&
               date1.getDate() === date2.getDate();
    }
    
    formatDate(date) {
        const options = { month: 'short', day: 'numeric' };
        return date.toLocaleDateString('en-US', options);
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

        // Group workouts by week
        const workoutsByWeek = {};
        let globalWorkoutNumber = 1;
        const today = new Date();
        
        workouts.forEach(workout => {
            const weekKey = `week-${workout.week_number}`;
            if (!workoutsByWeek[weekKey]) {
                workoutsByWeek[weekKey] = [];
            }
            
            // Add global workout number and date
            workout.globalNumber = globalWorkoutNumber++;
            workout.workoutDate = this.getWorkoutDate(workout);
            workout.isToday = this.isSameDay(workout.workoutDate, today);
            workout.isPast = workout.workoutDate < today && !workout.isToday;
            
            workoutsByWeek[weekKey].push(workout);
        });

        // Generate calendar HTML
        let html = '<div class="workout-calendar">';
        
        Object.keys(workoutsByWeek).sort((a, b) => {
            // Extract week numbers for proper numeric sorting
            const weekA = parseInt(a.replace('week-', ''));
            const weekB = parseInt(b.replace('week-', ''));
            return weekA - weekB;
        }).forEach(weekKey => {
            const weekWorkouts = workoutsByWeek[weekKey];
            const weekNumber = weekWorkouts[0].week_number;
            
            // Calculate week start date (first workout date)
            const firstWorkout = weekWorkouts.find(w => w.day_of_week === 0) || weekWorkouts[0]; // Sunday or first workout
            const weekStartDate = new Date(firstWorkout.workoutDate);
            weekStartDate.setDate(weekStartDate.getDate() - firstWorkout.day_of_week); // Adjust to Sunday
            
            const weekEndDate = new Date(weekStartDate);
            weekEndDate.setDate(weekStartDate.getDate() + 6); // Saturday
            
            // Get weekly focus from the first workout of the week (AI-generated content)
            const weekDateRange = `${this.formatDate(weekStartDate)} - ${this.formatDate(weekEndDate)}`;
            const weeklyFocus = weekWorkouts[0].weekly_focus || 'Progressive training continues';
            
            html += `<div class="calendar-week">`;
            html += `<div class="calendar-week-header" style="grid-column: 1 / -1; text-align: center; font-weight: bold; margin-bottom: 1rem; padding: 0.75rem; background: var(--gray-100); border-radius: 6px; border-left: 4px solid var(--primary);">
                <div style="font-size: 1.1rem; color: var(--gray-800); margin-bottom: 0.25rem;">
                    Week ${weekNumber} 
                    <span style="color: var(--gray-500); font-weight: normal; margin: 0 0.5rem;">•</span> 
                    ${weekDateRange}
                </div>
                <div style="font-size: 0.85rem; color: var(--gray-600); font-weight: normal; font-style: italic;">${weeklyFocus}</div>
            </div>`;
            
            // Create 7 day columns (Sunday to Saturday)
            for (let dayOfWeek = 0; dayOfWeek < 7; dayOfWeek++) {
                const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                const dayWorkouts = weekWorkouts.filter(w => w.day_of_week === dayOfWeek);
                
                html += `<div class="calendar-day">`;
                html += `<div class="calendar-day-header">${dayNames[dayOfWeek]}</div>`;
                
                if (dayWorkouts.length > 0) {
                    dayWorkouts.forEach(workout => {
                        const todayClass = workout.isToday ? 'today' : '';
                        const completedClass = (workout.isPast || workout.completed || 
                                              (this.completedWorkoutIds && this.completedWorkoutIds.has(workout.id))) ? 'completed' : '';
                        
                        html += `
                            <div class="calendar-workout ${todayClass} ${completedClass}" onclick="app.showWorkoutDetails(${workout.id})" title="${workout.name}">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                                    <span style="font-weight: bold; font-size: 0.6rem;">#${workout.globalNumber}</span>
                                    <span style="font-size: 0.6rem;">${this.formatDate(workout.workoutDate)}</span>
                                </div>
                                <div style="font-weight: bold;">${this.getWorkoutIcon(workout.workout_type)} ${workout.workout_type}</div>
                                <div>${workout.duration_minutes}min</div>
                                ${workout.distance_miles ? `<div>${workout.distance_miles}mi</div>` : ''}
                                ${workout.total_yards ? `<div>${workout.total_yards}y</div>` : ''}
                            </div>
                        `;
                    });
                } else {
                    // Calculate the date for this empty day
                    const weekStartDate = this.getWorkoutDate(weekWorkouts[0]);
                    const dayDate = new Date(weekStartDate);
                    dayDate.setDate(weekStartDate.getDate() + (dayOfWeek - weekWorkouts[0].day_of_week));
                    
                    html += `<div class="calendar-day-date">${this.formatDate(dayDate)}</div>`;
                }
                
                html += `</div>`;
            }
            
            html += `</div>`;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }
}

// Initialize the application
const app = new AtaraxAiApp();
