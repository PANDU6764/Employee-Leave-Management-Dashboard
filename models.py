from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # 'employee' or 'manager'
    department = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    leave_balances = db.relationship('LeaveBalance', backref='user', lazy=True, cascade="all, delete-orphan")
    leave_requests = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.user_id', backref='applicant', lazy=True, cascade="all, delete-orphan")
    reviewed_requests = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.reviewed_by', backref='reviewer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'email': self.email,
            'role': self.role,
            'department': self.department,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class LeaveBalance(db.Model):
    __tablename__ = 'leave_balances'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # 'Casual', 'Sick', 'Paid'
    allocated = db.Column(db.Integer, nullable=False)
    used = db.Column(db.Integer, nullable=False, default=0)
    pending = db.Column(db.Integer, nullable=False, default=0)

    @property
    def remaining(self):
        return self.allocated - self.used - self.pending

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'leave_type': self.leave_type,
            'allocated': self.allocated,
            'used': self.used,
            'pending': self.pending,
            'remaining': self.remaining
        }


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # 'Casual', 'Sick', 'Paid'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Number of days
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # 'Pending', 'Approved', 'Rejected'
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Manager review columns
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    manager_remarks = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'employee_name': f"{self.applicant.first_name} {self.applicant.last_name}" if self.applicant else "Unknown",
            'department': self.applicant.department if self.applicant else "Unknown",
            'leave_type': self.leave_type,
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'duration': self.duration,
            'reason': self.reason,
            'status': self.status,
            'applied_on': self.applied_on.strftime('%Y-%m-%d %H:%M:%S'),
            'reviewed_by': self.reviewed_by,
            'reviewer_name': f"{self.reviewer.first_name} {self.reviewer.last_name}" if self.reviewer else None,
            'manager_remarks': self.manager_remarks
        }
