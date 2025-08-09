// AtaraxAi - Athletic Training Platform JavaScript

class AtaraxAiApp {
    constructor() {
        this.apiBase = '/api/v1';
        this.currentUser = null;
        this.currentGoal = null;
        this.currentSection = 'landing';
        
        this.init();
    }

    async init() {
        // Check for existing authentication
        const token = localStorage.getItem('auth_token');
        if (token) {
            try {
                await this.loadUserProfile();
                this.showDashboard();
            } catch (error) {
                console.log('Invalid token, showing landing page');
                localStorage.removeItem('auth_token');
                this.showLandingPage();
            }
        } else {
            this.showLandingPage();
        }

        this.setupEventListeners();
        this.hideLoading();
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
                this.showSection(section);
            });
        });

        // Goal creation
        document.getElementById('create-goal-btn').addEventListener('click', () => this.showGoalModal());
        document.getElementById('close-goal-modal').addEventListener('click', () => this.hideGoalModal());
        document.getElementById('goal-form').addEventListener('submit', (e) => this.handleCreateGoal(e));
        document.getElementById('goal-type').addEventListener('change', (e) => this.handleGoalTypeChange(e));

        // Set default event date to June 28, 2026
        document.getElementById('event-date').value = '2026-06-28';
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
            this.hideAuthModal();
            this.showDashboard();
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
        e.preventDefault();
        
        const goalType = document.getElementById('goal-type').value;
        const eventDate = document.getElementById('event-date').value;
        
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

        try {
            const goal = await this.apiCall('/goals/', 'POST', goalData);
            this.currentGoal = goal;
            this.hideGoalModal();
            this.showSuccess('Goal created successfully! Your AI training plan is being generated.');
            await this.loadDashboardData();
            this.showSection('dashboard');
        } catch (error) {
            this.showError(error.detail || 'Failed to create goal');
        }
    }

    async loadGoals() {
        try {
            const goals = await this.apiCall('/goals/', 'GET');
            this.displayGoals(goals);
        } catch (error) {
            console.error('Failed to load goals:', error);
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

    // Dashboard Methods
    async loadDashboardData() {
        const goal = await this.loadActiveGoal();
        
        if (goal) {
            document.getElementById('days-to-goal').textContent = goal.days_until_event;
            document.getElementById('current-phase').textContent = goal.current_phase || 'Planning';
            document.getElementById('progress-percent').textContent = `${Math.round(goal.progress_percentage)}%`;
            
            // Update progress bar if exists
            const progressBar = document.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = `${goal.progress_percentage}%`;
            }
        } else {
            // No active goal state
            document.getElementById('days-to-goal').textContent = '--';
            document.getElementById('current-phase').textContent = '--';
            document.getElementById('progress-percent').textContent = '--%';
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
        const container = document.getElementById('goals-list');
        
        if (goals.length === 0) {
            container.innerHTML = `
                <div class="card text-center">
                    <h3>No Goals Yet</h3>
                    <p class="text-gray-600 mb-4">Create your first athletic goal to get started with personalized training.</p>
                    <button class="btn btn-primary" onclick="app.showGoalModal()">Create Your First Goal</button>
                </div>
            `;
            return;
        }

        container.innerHTML = goals.map(goal => `
            <div class="card">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-lg font-semibold">${goal.title}</h3>
                        <p class="text-sm text-gray-600">${new Date(goal.event_date).toLocaleDateString()}</p>
                    </div>
                    <span class="phase-badge ${goal.status}">${goal.status}</span>
                </div>
                <div class="progress mb-2">
                    <div class="progress-bar" style="width: ${goal.progress_percentage}%"></div>
                </div>
                <p class="text-sm text-gray-600">${goal.days_until_event} days remaining</p>
                ${goal.status === 'planning' ? `
                    <button class="btn btn-primary btn-sm mt-2" onclick="app.activateGoal(${goal.id})">
                        Start Training
                    </button>
                ` : ''}
            </div>
        `).join('');
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
        this.showSection('dashboard');
        this.updateAuthButton();
    }

    updateAuthButton() {
        const authBtn = document.getElementById('auth-btn');
        if (this.currentUser) {
            authBtn.textContent = 'Logout';
            authBtn.onclick = () => this.logout();
        } else {
            authBtn.textContent = 'Login';
            authBtn.onclick = () => this.showAuthModal();
        }
    }

    // Modal Management
    showAuthModal() {
        document.getElementById('auth-modal').classList.remove('hidden');
        this.showLoginForm();
    }

    hideAuthModal() {
        document.getElementById('auth-modal').classList.add('hidden');
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
        // Check if user is authenticated first
        if (!this.currentUser) {
            this.showError('Please log in first to create a goal.');
            this.showAuthModal();
            return;
        }
        document.getElementById('goal-modal').classList.remove('hidden');
    }

    hideGoalModal() {
        document.getElementById('goal-modal').classList.add('hidden');
        document.getElementById('goal-form').reset();
        // Reset default date
        document.getElementById('event-date').value = '2026-06-28';
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
        const token = localStorage.getItem('auth_token');
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

        const response = await fetch(`${this.apiBase}${endpoint}`, config);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw errorData;
        }

        return await response.json();
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
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
