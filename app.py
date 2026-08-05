import csv
import io
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
from config import Config
from models import db, User, LeaveBalance, LeaveRequest

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    
    # Register routes on this app instance
    register_routes(app)
    
    return app

# Helper decorators for route protection
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'manager':
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized. Manager privileges required.'}), 403
            flash('Access denied. Managers only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def register_routes(app):
    # Context processor to make current user available in all templates
    @app.context_processor
    def inject_user():
        user = None
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
        return dict(current_user=user)

    # --- HTML Routes ---

    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            if not username or not password:
                flash('Please enter both username and password.', 'danger')
                return render_template('login.html')
                
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['role'] = user.role
                session['username'] = user.username
                flash(f'Welcome back, {user.first_name}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
                
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user = db.session.get(User, session['user_id'])
        balances = LeaveBalance.query.filter_by(user_id=user.id).all()
        
        if user.role == 'manager':
            # Managers see all pending requests
            pending_requests = LeaveRequest.query.filter_by(status='Pending').order_by(LeaveRequest.applied_on.desc()).all()
            # History of all processed requests
            processed_requests = LeaveRequest.query.filter(LeaveRequest.status != 'Pending').order_by(LeaveRequest.applied_on.desc()).limit(50).all()
            return render_template('dashboard.html', balances=balances, pending_requests=pending_requests, processed_requests=processed_requests)
        else:
            # Employees see their own requests
            my_requests = LeaveRequest.query.filter_by(user_id=user.id).order_by(LeaveRequest.applied_on.desc()).all()
            return render_template('dashboard.html', balances=balances, my_requests=my_requests)

    # --- API Routes ---

    @app.route('/api/leave/apply', methods=['POST'])
    @login_required
    def apply_leave():
        user_id = session['user_id']
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Invalid request data.'}), 400
            
        leave_type = data.get('leave_type')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        reason = data.get('reason', '').strip()
        
        if not leave_type or not start_date_str or not end_date_str or not reason:
            return jsonify({'error': 'All fields are required.'}), 400
            
        if leave_type not in ['Casual', 'Sick', 'Paid']:
            return jsonify({'error': 'Invalid leave type.'}), 400
            
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Dates must be in YYYY-MM-DD format.'}), 400
            
        today = date.today()
        if start_date < today:
            return jsonify({'error': 'Start date cannot be in the past.'}), 400
            
        if end_date < start_date:
            return jsonify({'error': 'End date must be on or after the start date.'}), 400
            
        # Calculate duration (calendar days)
        duration = (end_date - start_date).days + 1
        
        # Check for overlapping leave requests
        overlapping = LeaveRequest.query.filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status.in_(['Pending', 'Approved']),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date
        ).first()
        
        if overlapping:
            return jsonify({
                'error': f'You already have a {overlapping.status.lower()} leave request '
                         f'({overlapping.start_date} to {overlapping.end_date}) that overlaps with this range.'
            }), 400
            
        # Check leave balance
        balance = LeaveBalance.query.filter_by(user_id=user_id, leave_type=leave_type).first()
        if not balance:
            return jsonify({'error': 'Leave balance profile not found.'}), 404
            
        if balance.remaining < duration:
            return jsonify({
                'error': f'Insufficient leave balance. You requested {duration} days, '
                         f'but you only have {balance.remaining} days remaining for {leave_type} leave.'
            }), 400
            
        try:
            req = LeaveRequest(
                user_id=user_id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                duration=duration,
                reason=reason,
                status='Pending'
            )
            db.session.add(req)
            
            balance.pending += duration
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Leave application submitted successfully.',
                'request': req.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500


    @app.route('/api/leave/review/<int:request_id>', methods=['POST'])
    @manager_required
    def review_leave(request_id):
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data.'}), 400
            
        action = data.get('action')
        remarks = data.get('remarks', '').strip()
        
        if action not in ['approve', 'reject']:
            return jsonify({'error': 'Action must be either "approve" or "reject".'}), 400
            
        req = db.session.get(LeaveRequest, request_id)
        if not req:
            return jsonify({'error': 'Leave request not found.'}), 404
            
        if req.status != 'Pending':
            return jsonify({'error': f'This leave request has already been {req.status.lower()}.'}), 400
            
        balance = LeaveBalance.query.filter_by(user_id=req.user_id, leave_type=req.leave_type).first()
        if not balance:
            return jsonify({'error': 'Employee leave balance record not found.'}), 404
            
        try:
            req.reviewed_by = session['user_id']
            req.manager_remarks = remarks
            
            if action == 'approve':
                req.status = 'Approved'
                balance.pending = max(0, balance.pending - req.duration)
                balance.used += req.duration
            else:
                req.status = 'Rejected'
                balance.pending = max(0, balance.pending - req.duration)
                
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Leave request has been successfully {req.status.lower()}.',
                'request': req.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500


    @app.route('/api/employees/search', methods=['GET'])
    @manager_required
    def search_employees():
        query = request.args.get('query', '').strip()
        
        if not query:
            employees = User.query.filter_by(role='employee').all()
        else:
            search_filter = f"%{query}%"
            employees = User.query.filter(
                (User.role == 'employee') & (
                    User.username.ilike(search_filter) |
                    User.first_name.ilike(search_filter) |
                    User.last_name.ilike(search_filter) |
                    User.department.ilike(search_filter)
                )
            ).all()
            
        results = []
        for emp in employees:
            emp_data = emp.to_dict()
            balances = LeaveBalance.query.filter_by(user_id=emp.id).all()
            emp_data['balances'] = {b.leave_type: b.to_dict() for b in balances}
            
            pending_cnt = LeaveRequest.query.filter_by(user_id=emp.id, status='Pending').count()
            approved_cnt = LeaveRequest.query.filter_by(user_id=emp.id, status='Approved').count()
            emp_data['requests_summary'] = {
                'pending': pending_cnt,
                'approved': approved_cnt
            }
            results.append(emp_data)
            
        return jsonify(results)


    @app.route('/api/reports/leave-stats', methods=['GET'])
    @manager_required
    def leave_stats():
        types = ['Casual', 'Sick', 'Paid']
        type_stats = {}
        for t in types:
            total_days = db.session.query(db.func.sum(LeaveRequest.duration))\
                .filter(LeaveRequest.leave_type == t, LeaveRequest.status == 'Approved').scalar() or 0
            type_stats[t] = total_days
            
        dept_stats = {}
        depts = db.session.query(User.department).filter(User.role == 'employee').distinct().all()
        for (dept,) in depts:
            total_days = db.session.query(db.func.sum(LeaveRequest.duration))\
                .join(User, LeaveRequest.user_id == User.id)\
                .filter(User.department == dept, LeaveRequest.status == 'Approved').scalar() or 0
            dept_stats[dept] = total_days

        current_year = date.today().year
        monthly_stats = [0] * 12
        approved_requests = LeaveRequest.query.filter(
            LeaveRequest.status == 'Approved',
            db.extract('year', LeaveRequest.start_date) == current_year
        ).all()
        
        for req in approved_requests:
            month_idx = req.start_date.month - 1
            monthly_stats[month_idx] += req.duration

        status_counts = {
            'Pending': LeaveRequest.query.filter_by(status='Pending').count(),
            'Approved': LeaveRequest.query.filter_by(status='Approved').count(),
            'Rejected': LeaveRequest.query.filter_by(status='Rejected').count()
        }
        
        return jsonify({
            'by_type': type_stats,
            'by_department': dept_stats,
            'monthly_trend': monthly_stats,
            'status_counts': status_counts
        })


    @app.route('/api/reports/export')
    @manager_required
    def export_csv():
        requests_list = LeaveRequest.query.order_by(LeaveRequest.applied_on.desc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Request ID', 'Employee Name', 'Department', 'Email', 
            'Leave Type', 'Start Date', 'End Date', 'Duration (Days)', 
            'Status', 'Reason', 'Applied On', 'Reviewed By', 'Manager Remarks'
        ])
        
        for r in requests_list:
            applicant = r.applicant
            reviewer = r.reviewer
            applicant_name = f"{applicant.first_name} {applicant.last_name}" if applicant else "N/A"
            applicant_email = applicant.email if applicant else "N/A"
            department = applicant.department if applicant else "N/A"
            reviewer_name = f"{reviewer.first_name} {reviewer.last_name}" if reviewer else "N/A"
            
            writer.writerow([
                r.id,
                applicant_name,
                department,
                applicant_email,
                r.leave_type,
                r.start_date.strftime('%Y-%m-%d'),
                r.end_date.strftime('%Y-%m-%d'),
                r.duration,
                r.status,
                r.reason,
                r.applied_on.strftime('%Y-%m-%d %H:%M:%S'),
                reviewer_name,
                r.manager_remarks or ''
            ])
            
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=leave_report.csv"}
        )

# Global app instance for default WSGI/Flask execution
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
