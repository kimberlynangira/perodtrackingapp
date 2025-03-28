// Login
// Toggle password visibility
const passwordInput = document.getElementById('password');
const togglePasswordButton = document.getElementById('togglePassword');

if (togglePasswordButton) {
    togglePasswordButton.addEventListener('click', () => {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
    });
}

// Login functionality
const loginForm = document.getElementById('loginForm');

if (loginForm) {
    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.ok) {
                if (data.success) {
                    console.log(data.message);
                    // **Session Handling (Example - Adjust for your server)**
                    // If the server returns a session ID or token
                    // localStorage.setItem('sessionId', data.sessionId);  // Insecure example
                    // **Ideally, use HttpOnly, Secure cookies**
                    window.location.href = 'pages/home.html';
                } else {
                    // Display login error message
                    const loginErrorMessage = document.getElementById('login-error-message');
                    if (loginErrorMessage) {
                        loginErrorMessage.textContent = data.message;
                    } else {
                        alert(data.message);
                    }
                }
            } else {
                // Handle non-OK responses
                console.error('Login error:', data.message || 'Login failed');
                const loginErrorMessage = document.getElementById('login-error-message');
                if (loginErrorMessage) {
                    loginErrorMessage.textContent = data.message || 'Login failed';
                } else {
                    alert(data.message || 'Login failed');
                }
            }
        } catch (error) {
            console.error('Login error:', error);
            const loginErrorMessage = document.getElementById('login-error-message');
            if (loginErrorMessage) {
                loginErrorMessage.textContent = 'An error occurred during login';
            } else {
                alert('An error occurred during login');
            }
        }
    });
}

// Calendar functionality
const prevMonthButton = document.getElementById('prev-month');

if (prevMonthButton) {
    const nextMonthButton = document.getElementById('next-month');
    const monthDisplay = document.getElementById('current-month');
    const calendarDaysContainer = document.querySelector('.calendar-days');

    // Get current date
    const today = new Date();
    let currentMonth = today.getMonth();
    let currentYear = today.getFullYear();

    // Function to display the calendar
    function displayCalendar(month, year) {
        const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
        monthDisplay.textContent = `${months[month]} ${year}`;
        const firstDayOfMonth = new Date(year, month, 1).getDay();
        const totalDaysInMonth = new Date(year, month + 1, 0).getDate();
        calendarDaysContainer.innerHTML = '';

        for (let i = 0; i < firstDayOfMonth; i++) {
            const emptyDiv = document.createElement('div');
            calendarDaysContainer.appendChild(emptyDiv);
        }

        // Fetch period dates for the current month
        fetch(`/cycles/period_dates?month=${month + 1}&year=${year}`, { // Adjust route as needed
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
             if (!response.ok) {
                throw new Error('Network response was not ok');
              }
              return response.json();
        })
        .then(data => {
            let periodDates = [];
            if (data.success) {
                 periodDates = data.period_dates;
            } else {
                console.error('Error fetching period dates:', data.message);
            }

            for (let i = 1; i <= totalDaysInMonth; i++) {
                const dayDiv = document.createElement('div');
                dayDiv.textContent = i;

                const currentDate = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;

                if (i === today.getDate() && month === today.getMonth() && year === today.getFullYear()) {
                    dayDiv.classList.add('today');
                }

                if (month !== today.getMonth() || year !== today.getFullYear()) {
                    dayDiv.classList.add('not-current-month');
                }

                if (periodDates && periodDates.includes(currentDate)) {
                    dayDiv.classList.add('period-date');
                }

                calendarDaysContainer.appendChild(dayDiv);
            }
        })
        .catch(error => {
            console.error('Error fetching period dates:', error);
            // Display a default calendar or handle the error gracefully
            for (let i = 1; i <= totalDaysInMonth; i++) {
                const dayDiv = document.createElement('div');
                dayDiv.textContent = i;

                if (i === today.getDate() && month === today.getMonth() && year === today.getFullYear()) {
                    dayDiv.classList.add('today');
                }

                if (month !== today.getMonth() || year !== today.getFullYear()) {
                    dayDiv.classList.add('not-current-month');
                }
                calendarDaysContainer.appendChild(dayDiv);
            }
        });
    }

    prevMonthButton.addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        displayCalendar(currentMonth, currentYear);
    });

    nextMonthButton.addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        displayCalendar(currentMonth, currentYear);
    });

    displayCalendar(currentMonth, currentYear);
}