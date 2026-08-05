# 🚀 Employee Leave Management System

A modern **Employee Leave Management System** built using **Python, Flask, MySQL, SQLAlchemy, HTML, CSS, JavaScript, and Bootstrap**. The application automates the leave request and approval workflow while providing managers with dashboards, employee management, analytics, and reporting capabilities.

---

## 📖 Overview

The Employee Leave Management System simplifies leave management by allowing employees to submit leave requests and managers to review, approve, or reject them. The system tracks leave balances, prevents invalid requests through validation, and provides insightful reports for better workforce management.

The application follows a modular architecture using **Flask** and **SQLAlchemy**, making it scalable, maintainable, and easy to extend.

---

## ✨ Features

### 🔐 Authentication
- Employee Login
- Manager/Admin Login
- Secure password authentication
- Session management
- Role-based access control

---

### 👨‍💼 Employee Module

- Apply for leave
- View leave balances
- Track leave request status
- View leave history
- Edit profile information

---

### 👨‍💻 Manager/Admin Module

- Review pending leave requests
- Approve leave requests
- Reject leave requests with comments
- Search employees
- Manage employee records
- Monitor leave balances
- View organization-wide reports

---

### 📊 Reports & Analytics

- Total Employees
- Pending Requests
- Approved Requests
- Rejected Requests
- Leave Utilization Report
- Department-wise Leave Analysis
- Monthly Leave Trends
- Export Reports as CSV

---

### ✅ Validation

- Required field validation
- Date validation
- Leave balance validation
- Duplicate leave request prevention
- Role authorization validation

---

### ⚠️ Error Handling

- Invalid login credentials
- Database exception handling
- Invalid date selection
- Empty form validation
- Graceful error messages

---

# 🖥️ Screenshots

## Login Page

<p align="center">
  <img src="login page.png" width="900">
</p>

---

## Dashboard

<p align="center">
  <img src="Dashboard Overview.png" width="900">
</p>


---

## Pending Leave Requests

<p align="center">
  <img src="Pending Requests.png" width="900">
</p>

---

## Employee Directory

<p align="center">
  <img src="Employee Directory.png" width="900">
</p>

---

## Leave Reports & Analytics


<p align="center">
  <img src="leave report.png" width="900">
</p>

---

# 🏗️ System Architecture

```
Browser
      │
      ▼
HTML • CSS • JavaScript • Bootstrap
      │
      ▼
Flask Application
      │
      ▼
Business Logic (Python)
      │
      ▼
SQLAlchemy ORM
      │
      ▼
MySQL Database
```

---

# 🗄️ Database Design

## Employee

| Column | Type |
|---------|------|
| EmployeeID | INT |
| Name | VARCHAR |
| Email | VARCHAR |
| Department | VARCHAR |
| Password | VARCHAR |
| LeaveBalance | INT |

---

## LeaveRequest

| Column | Type |
|---------|------|
| LeaveID | INT |
| EmployeeID | INT |
| LeaveType | VARCHAR |
| StartDate | DATE |
| EndDate | DATE |
| NumberOfDays | INT |
| Reason | TEXT |
| Status | VARCHAR |

---

## Admin

| Column | Type |
|---------|------|
| AdminID | INT |
| Username | VARCHAR |
| Password | VARCHAR |

---

# 💻 Tech Stack

## Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap

## Backend

- Python
- Flask
- SQLAlchemy

## Database

- MySQL

## Tools

- Git
- GitHub
- VS Code

---

# 🧠 Python Concepts Implemented

- Object-Oriented Programming (OOP)
- Functions
- Classes
- Modules
- CRUD Operations
- Exception Handling
- Database Connectivity
- Form Validation
- Session Management
- File Handling
- Modular Programming

---

# 📂 Project Structure

```
Employee-Leave-Management-System/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
│
├── models/
│   ├── employee.py
│   ├── leave.py
│   └── admin.py
│
├── routes/
│   ├── auth.py
│   ├── employee.py
│   ├── manager.py
│   └── reports.py
│
├── templates/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── screenshots/
│
└── database/
    └── schema.sql
```

---

# ⚙️ Installation

## Clone the Repository

```bash
git clone https://github.com/yourusername/employee-leave-management-system.git
```

```bash
cd employee-leave-management-system
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Database

Create a MySQL database.

```sql
CREATE DATABASE leave_management;
```

Update your database configuration in:

```
config.py
```

---

## Run the Application

```bash
python app.py
```

Open your browser:

```
http://127.0.0.1:5000
```

---

# 📌 Future Enhancements

- Email notifications for leave approval/rejection
- Calendar integration
- PDF report generation
- Employee profile image upload
- Multi-level leave approval workflow
- REST API support
- Docker deployment
- Unit testing with PyTest
- CI/CD using GitHub Actions

---

# 🎯 Learning Outcomes

This project demonstrates practical software engineering skills including:

- Full Stack Web Development
- Python Programming
- Flask Framework
- SQLAlchemy ORM
- MySQL Database Design
- Authentication & Authorization
- CRUD Operations
- Session Management
- Error Handling
- Data Validation
- Version Control using Git
- Clean Code Practices

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature-name
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push the branch

```bash
git push origin feature-name
```

5. Create a Pull Request

---

# 📄 License

This project is licensed under the **MIT License**.

---

## 👨‍💻 Author

**Chaitanya**
