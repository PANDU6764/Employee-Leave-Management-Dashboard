/* -------------------------------------------------------------
   LUMINA LEAVE MANAGEMENT SYSTEM - FRONTEND INTERACTION
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Sidebar Section Navigation
    setupNavigation();
    
    // 2. Setup Mobile Sidebar Toggles
    setupMobileSidebar();

    // 3. User Role-Specific Setup
    if (window.USER_ROLE === 'employee') {
        setupEmployeeFeatures();
    } else if (window.USER_ROLE === 'manager') {
        setupManagerFeatures();
    }
});

/* -------------------------------------------------------------
   NAVIGATION LOGIC
   ------------------------------------------------------------- */
function setupNavigation() {
    const navItems = document.querySelectorAll('.sidebar-nav li');
    const sections = document.querySelectorAll('.dashboard-section');
    const pageTitle = document.getElementById('pageTitle');
    const sidebar = document.getElementById('sidebar');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetSectionId = item.getAttribute('data-section');
            
            // Switch Active Section
            sections.forEach(sec => {
                if (sec.id === targetSectionId) {
                    sec.classList.add('active-section');
                } else {
                    sec.classList.remove('active-section');
                }
            });

            // Update Active Nav Item
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Update Header Page Title
            const sectionName = item.querySelector('span').textContent;
            pageTitle.textContent = sectionName;

            // Close sidebar on mobile after selecting
            if (sidebar.classList.contains('sidebar-open')) {
                sidebar.classList.remove('sidebar-open');
            }
        });
    });

    // Handle Quick Navigation Shortcuts
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('nav-shortcut')) {
            const targetId = e.target.getAttribute('data-target');
            const matchingNavItem = document.querySelector(`.sidebar-nav li[data-section="${targetId}"]`);
            if (matchingNavItem) {
                matchingNavItem.click();
            }
        }
    });
}

function setupMobileSidebar() {
    const menuToggle = document.getElementById('menuToggleBtn');
    const sidebarClose = document.getElementById('sidebarCloseBtn');
    const sidebar = document.getElementById('sidebar');

    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.add('sidebar-open');
        });
    }

    if (sidebarClose && sidebar) {
        sidebarClose.addEventListener('click', () => {
            sidebar.classList.remove('sidebar-open');
        });
    }
}

/* -------------------------------------------------------------
   EMPLOYEE SYSTEM FEATURES
   ------------------------------------------------------------- */
function setupEmployeeFeatures() {
    const applyForm = document.getElementById('applyLeaveForm');
    const leaveTypeSelect = document.getElementById('leave_type');
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const daysCountSpan = document.getElementById('daysCount');
    const balanceHelper = document.getElementById('balanceHelper');
    const errorAlert = document.getElementById('apply-error-alert');
    const successAlert = document.getElementById('apply-success-alert');

    if (!applyForm) return;

    // Display remaining balance in tooltip on select change
    leaveTypeSelect.addEventListener('change', () => {
        const type = leaveTypeSelect.value;
        const bal = window.USER_BALANCES[type];
        if (bal) {
            balanceHelper.innerHTML = `<i class="fa-solid fa-circle-info"></i> Available <strong>${type}</strong> Balance: <strong>${bal.remaining}</strong> days (Allocated: ${bal.allocated}, Used: ${bal.used}, Pending: ${bal.pending})`;
        } else {
            balanceHelper.textContent = "Select a leave type to view remaining balance.";
        }
        calculateDuration();
    });

    // Calculate duration when dates change
    startDateInput.addEventListener('change', calculateDuration);
    endDateInput.addEventListener('change', calculateDuration);

    function calculateDuration() {
        const startStr = startDateInput.value;
        const endStr = endDateInput.value;
        
        if (!startStr || !endStr) {
            daysCountSpan.textContent = '0';
            return;
        }

        const start = new Date(startStr);
        const end = new Date(endStr);
        
        if (end < start) {
            daysCountSpan.textContent = '0';
            return;
        }

        // Calculate total calendar days inclusive
        const diffTime = Math.abs(end - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
        
        daysCountSpan.textContent = diffDays;
    }

    // Submit Leave Form
    applyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Hide previous messages
        errorAlert.classList.add('hidden');
        successAlert.classList.add('hidden');

        const leave_type = leaveTypeSelect.value;
        const start_date = startDateInput.value;
        const end_date = endDateInput.value;
        const reason = document.getElementById('reason').value.trim();

        // Client side validation
        const today = new Date();
        today.setHours(0,0,0,0);
        const start = new Date(start_date);
        
        if (start < today) {
            showError("Start date cannot be in the past.");
            return;
        }

        const end = new Date(end_date);
        if (end < start) {
            showError("End date must be on or after the start date.");
            return;
        }

        const duration = Math.ceil(Math.abs(end - start) / (1000 * 60 * 60 * 24)) + 1;
        const bal = window.USER_BALANCES[leave_type];
        if (bal && bal.remaining < duration) {
            showError(`Insufficient balance. You requested ${duration} days, but you only have ${bal.remaining} remaining.`);
            return;
        }

        // Send AJAX Request
        try {
            const response = await fetch('/api/leave/apply', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ leave_type, start_date, end_date, reason })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                successAlert.textContent = "Leave request submitted successfully. Reloading your dashboard...";
                successAlert.classList.remove('hidden');
                applyForm.reset();
                daysCountSpan.textContent = '0';
                balanceHelper.textContent = "Select a leave type to view remaining balance.";
                
                // Refresh dashboard to show new status and updated balances
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showError(result.error || "An error occurred while submitting your request.");
            }
        } catch (err) {
            showError("Server connectivity issue. Please try again.");
            console.error(err);
        }
    });

    function showError(msg) {
        errorAlert.textContent = msg;
        errorAlert.classList.remove('hidden');
        errorAlert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/* -------------------------------------------------------------
   MANAGER SYSTEM FEATURES
   ------------------------------------------------------------- */
function setupManagerFeatures() {
    // 1. Initial Load of Employee Directory
    searchEmployees();

    // 2. Initial Load of Analytics Charts
    loadAnalyticsCharts();
}

// Manager Action: Approve/Reject Leave Request
async function reviewRequest(reqId, action) {
    const remarksInput = document.getElementById(`remarks-${reqId}`);
    const remarks = remarksInput ? remarksInput.value.trim() : '';

    try {
        const response = await fetch(`/api/leave/review/${reqId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action, remarks })
        });

        const result = await response.json();

        if (response.ok) {
            // Show dynamic success toast
            showToast(`Leave request has been successfully ${action}d.`, 'success');
            
            // Remove request card from DOM with a smooth animation
            const card = document.getElementById(`req-card-${reqId}`);
            if (card) {
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                card.style.transition = 'all 0.3s ease';
                setTimeout(() => {
                    card.remove();
                    
                    // Check if there are no more cards in the list
                    const container = document.getElementById('pendingRequestsContainer');
                    if (container && container.querySelectorAll('.request-card').length === 0) {
                        container.innerHTML = `
                            <div class="no-data-card glass text-center">
                                <i class="fa-solid fa-circle-check checked-in-icon"></i>
                                <h3>No Pending Leave Requests</h3>
                                <p>All leaves are reviewed and up to date.</p>
                            </div>
                        `;
                    }
                }, 300);
            }
            
            // If the manager has switched to other tabs, we want database changes reflected on reload.
            // Let's refresh the page in the background or let the user refresh, or just rebuild employee directory and charts:
            searchEmployees();
            loadAnalyticsCharts();
        } else {
            showToast(result.error || "Failed to process request.", 'danger');
        }
    } catch (err) {
        showToast("Error connecting to server.", 'danger');
        console.error(err);
    }
}

// Manager: Dynamic Employee Directory Query
async function searchEmployees() {
    const searchInput = document.getElementById('employeeSearchInput');
    const query = searchInput ? searchInput.value.trim() : '';
    const tableBody = document.getElementById('directoryTableBody');
    
    if (!tableBody) return;

    try {
        const response = await fetch(`/api/employees/search?query=${encodeURIComponent(query)}`);
        const employees = await response.json();

        if (!response.ok) {
            tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Error loading employees: ${employees.error}</td></tr>`;
            return;
        }

        if (employees.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No employees match your search criteria.</td></tr>`;
            return;
        }

        tableBody.innerHTML = '';
        employees.forEach(emp => {
            const casual = emp.balances.Casual;
            const sick = emp.balances.Sick;
            const paid = emp.balances.Paid;

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="table-user-cell">
                        <div class="avatar-sm">${emp.first_name[0]}${emp.last_name[0]}</div>
                        <div>
                            <strong>${emp.full_name}</strong>
                            <div class="text-muted" style="font-size: 11px;">@${emp.username}</div>
                        </div>
                    </div>
                </td>
                <td>${emp.department}</td>
                <td>
                    <span class="remaining-pill" style="color: var(--color-casual)">${casual.remaining}</span> / ${casual.allocated} left
                </td>
                <td>
                    <span class="remaining-pill" style="color: var(--color-sick)">${sick.remaining}</span> / ${sick.allocated} left
                </td>
                <td>
                    <span class="remaining-pill" style="color: var(--color-paid)">${paid.remaining}</span> / ${paid.allocated} left
                </td>
                <td>
                    <span class="badge badge-approved">${emp.requests_summary.approved} approved</span>
                </td>
                <td>
                    <span class="badge badge-pending">${emp.requests_summary.pending} pending</span>
                </td>
            `;
            tableBody.appendChild(row);
        });
    } catch (err) {
        tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Connectivity error loading employee records.</td></tr>';
        console.error(err);
    }
}

// Manager: Load Analytics using Chart.js
let charts = {}; // Store chart instances to destroy them before reloading
async function loadAnalyticsCharts() {
    const reportsSection = document.getElementById('reports-section');
    if (!reportsSection) return;

    try {
        const response = await fetch('/api/reports/leave-stats');
        const stats = await response.json();

        if (!response.ok) return;

        // Destroy existing charts if they exist (to prevent hover gltiches)
        Object.keys(charts).forEach(key => {
            if (charts[key]) charts[key].destroy();
        });

        // Chart styling defaults
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Inter', sans-serif";

        // 1. Leave Type Donut Chart
        const ctxType = document.getElementById('typeChart').getContext('2d');
        charts.type = new Chart(ctxType, {
            type: 'doughnut',
            data: {
                labels: ['Casual Leave', 'Sick Leave', 'Paid Leave'],
                datasets: [{
                    data: [stats.by_type.Casual, stats.by_type.Sick, stats.by_type.Paid],
                    backgroundColor: ['#38bdf8', '#f43f5e', '#34d399'],
                    borderWidth: 1,
                    borderColor: 'rgba(255,255,255,0.08)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });

        // 2. Department Bar Chart
        const ctxDept = document.getElementById('departmentChart').getContext('2d');
        const deptLabels = Object.keys(stats.by_department);
        const deptValues = Object.values(stats.by_department);

        charts.dept = new Chart(ctxDept, {
            type: 'bar',
            data: {
                labels: deptLabels,
                datasets: [{
                    label: 'Approved Days Taken',
                    data: deptValues,
                    backgroundColor: 'rgba(99, 102, 241, 0.6)',
                    borderColor: '#6366f1',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

        // 3. Monthly Trend Line Chart
        const ctxTrend = document.getElementById('monthlyTrendChart').getContext('2d');
        charts.trend = new Chart(ctxTrend, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Leave Days Taken',
                    data: stats.monthly_trend,
                    borderColor: '#a855f7',
                    backgroundColor: 'rgba(168, 85, 247, 0.1)',
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

        // 4. Request Status Pie Chart
        const ctxStatus = document.getElementById('statusChart').getContext('2d');
        charts.status = new Chart(ctxStatus, {
            type: 'pie',
            data: {
                labels: ['Approved', 'Pending', 'Rejected'],
                datasets: [{
                    data: [stats.status_counts.Approved, stats.status_counts.Pending, stats.status_counts.Rejected],
                    backgroundColor: ['#10b981', '#fbbf24', '#ef4444'],
                    borderWidth: 1,
                    borderColor: 'rgba(255,255,255,0.08)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });

    } catch (err) {
        console.error("Error loading analytics data:", err);
    }
}

/* -------------------------------------------------------------
   HELPERS & TOASTS
   ------------------------------------------------------------- */
function showToast(message, type = 'success') {
    // Check if toast-container exists, if not create it
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let iconClass = 'fa-circle-check';
    if (type === 'danger') iconClass = 'fa-circle-xmark';
    if (type === 'warning') iconClass = 'fa-triangle-exclamation';

    toast.innerHTML = `
        <i class="fa-solid ${iconClass} toast-icon"></i>
        <span class="toast-message">${message}</span>
        <button type="button" class="toast-close">&times;</button>
    `;

    container.appendChild(toast);

    // Close button click listener
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.remove();
    });

    // Auto-remove toast
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        toast.style.transition = 'all 0.4s ease';
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}
