import unittest
from datetime import date, timedelta
from app import create_app, db
from models import User, LeaveBalance, LeaveRequest

class LeaveSystemTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory DB for tests
        self.client = self.app.test_client()
        
        # Create tables and active context
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Populate base test users
        self.create_test_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def create_test_data(self):
        # Create a Manager
        self.manager = User(
            username='manager_test',
            first_name='Molly',
            last_name='Manager',
            email='molly@test.com',
            role='manager',
            department='HR'
        )
        self.manager.set_password('pass123')
        db.session.add(self.manager)

        # Create an Employee
        self.employee = User(
            username='employee_test',
            first_name='Eric',
            last_name='Employee',
            email='eric@test.com',
            role='employee',
            department='Engineering'
        )
        self.employee.set_password('pass123')
        db.session.add(self.employee)
        db.session.commit()

        # Seed standard leave balances for the employee
        self.balances = {
            'Casual': LeaveBalance(user_id=self.employee.id, leave_type='Casual', allocated=10, used=0, pending=0),
            'Sick': LeaveBalance(user_id=self.employee.id, leave_type='Sick', allocated=8, used=0, pending=0),
            'Paid': LeaveBalance(user_id=self.employee.id, leave_type='Paid', allocated=15, used=0, pending=0)
        }
        for bal in self.balances.values():
            db.session.add(bal)
        db.session.commit()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    # --- Test Cases ---

    def test_user_password_hashing(self):
        u = User(username='test_hash')
        u.set_password('mysecret')
        self.assertTrue(u.check_password('mysecret'))
        self.assertFalse(u.check_password('notmysecret'))

    def test_login_logout(self):
        # Test valid login
        rv = self.login('employee_test', 'pass123')
        self.assertIn(b'Welcome back, Eric!', rv.data)
        
        # Test invalid login
        self.logout()
        rv = self.login('employee_test', 'wrongpassword')
        self.assertIn(b'Invalid username or password.', rv.data)

    def test_apply_leave_unauthorized(self):
        # Attempt to apply without logging in
        rv = self.client.post('/api/leave/apply', json={
            'leave_type': 'Casual',
            'start_date': str(date.today()),
            'end_date': str(date.today() + timedelta(days=2)),
            'reason': 'Vacation'
        })
        # login_required redirects to login page
        self.assertEqual(rv.status_code, 302)

    def test_apply_leave_success(self):
        self.login('employee_test', 'pass123')
        
        # Apply for 3 days of Casual leave
        start = date.today() + timedelta(days=1)
        end = start + timedelta(days=2)
        
        rv = self.client.post('/api/leave/apply', json={
            'leave_type': 'Casual',
            'start_date': str(start),
            'end_date': str(end),
            'reason': 'Family event'
        })
        
        data = rv.get_json()
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(data['success'])
        
        # Check leave request created
        req = LeaveRequest.query.filter_by(user_id=self.employee.id).first()
        self.assertIsNotNone(req)
        self.assertEqual(req.leave_type, 'Casual')
        self.assertEqual(req.duration, 3)
        self.assertEqual(req.status, 'Pending')
        
        # Check pending balance updated
        bal = LeaveBalance.query.filter_by(user_id=self.employee.id, leave_type='Casual').first()
        self.assertEqual(bal.pending, 3)
        self.assertEqual(bal.remaining, 7)

    def test_apply_leave_insufficient_balance(self):
        self.login('employee_test', 'pass123')
        
        # Apply for 12 days of Casual leave (Allocated: 10)
        start = date.today() + timedelta(days=1)
        end = start + timedelta(days=11)
        
        rv = self.client.post('/api/leave/apply', json={
            'leave_type': 'Casual',
            'start_date': str(start),
            'end_date': str(end),
            'reason': 'Long trip'
        })
        
        data = rv.get_json()
        self.assertEqual(rv.status_code, 400)
        self.assertIn('Insufficient leave balance', data['error'])

    def test_apply_leave_invalid_dates(self):
        self.login('employee_test', 'pass123')
        
        # End date before start date
        start = date.today() + timedelta(days=5)
        end = date.today() + timedelta(days=2)
        
        rv = self.client.post('/api/leave/apply', json={
            'leave_type': 'Casual',
            'start_date': str(start),
            'end_date': str(end),
            'reason': 'Invalid dates test'
        })
        self.assertEqual(rv.status_code, 400)
        self.assertIn('End date must be on or after the start date', rv.get_json()['error'])

        # Start date in the past
        past_start = date.today() - timedelta(days=2)
        past_end = date.today() + timedelta(days=1)
        
        rv = self.client.post('/api/leave/apply', json={
            'leave_type': 'Casual',
            'start_date': str(past_start),
            'end_date': str(past_end),
            'reason': 'Past date test'
        })
        self.assertEqual(rv.status_code, 400)
        self.assertIn('Start date cannot be in the past', rv.get_json()['error'])

    def test_apply_leave_overlapping_requests(self):
        self.login('employee_test', 'pass123')
        
        start1 = date.today() + timedelta(days=5)
        end1 = start1 + timedelta(days=2)
        
        # First request succeeds
        rv1 = self.client.post('/api/leave/apply', json={
            'leave_type': 'Casual',
            'start_date': str(start1),
            'end_date': str(end1),
            'reason': 'First leave'
        })
        self.assertEqual(rv1.status_code, 200)

        # Overlapping request
        start2 = start1 + timedelta(days=1)
        end2 = start1 + timedelta(days=4)
        
        rv2 = self.client.post('/api/leave/apply', json={
            'leave_type': 'Casual',
            'start_date': str(start2),
            'end_date': str(end2),
            'reason': 'Overlapping leave'
        })
        self.assertEqual(rv2.status_code, 400)
        self.assertIn('overlaps with this range', rv2.get_json()['error'])

    def test_manager_review_approve(self):
        # Create a pending request
        req = LeaveRequest(
            user_id=self.employee.id,
            leave_type='Sick',
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=1),
            duration=1,
            reason='Clinic checkup',
            status='Pending'
        )
        db.session.add(req)
        bal = LeaveBalance.query.filter_by(user_id=self.employee.id, leave_type='Sick').first()
        bal.pending = 1
        db.session.commit()

        # Log in as Manager
        self.login('manager_test', 'pass123')
        
        # Approve the request
        rv = self.client.post(f'/api/leave/review/{req.id}', json={
            'action': 'approve',
            'remarks': 'Approved, get well soon!'
        })
        
        data = rv.get_json()
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(data['success'])

        # Verify DB changes
        updated_req = db.session.get(LeaveRequest, req.id)
        self.assertEqual(updated_req.status, 'Approved')
        self.assertEqual(updated_req.reviewed_by, self.manager.id)
        self.assertEqual(updated_req.manager_remarks, 'Approved, get well soon!')
        
        # Verify balances update
        updated_bal = LeaveBalance.query.filter_by(user_id=self.employee.id, leave_type='Sick').first()
        self.assertEqual(updated_bal.pending, 0)
        self.assertEqual(updated_bal.used, 1)
        self.assertEqual(updated_bal.remaining, 7)

    def test_manager_review_reject(self):
        # Create a pending request
        req = LeaveRequest(
            user_id=self.employee.id,
            leave_type='Casual',
            start_date=date.today() + timedelta(days=2),
            end_date=date.today() + timedelta(days=3),
            duration=2,
            reason='Concert visit',
            status='Pending'
        )
        db.session.add(req)
        bal = LeaveBalance.query.filter_by(user_id=self.employee.id, leave_type='Casual').first()
        bal.pending = 2
        db.session.commit()

        # Log in as Manager
        self.login('manager_test', 'pass123')
        
        # Reject the request
        rv = self.client.post(f'/api/leave/review/{req.id}', json={
            'action': 'reject',
            'remarks': 'Rejected due to coverage.'
        })
        
        data = rv.get_json()
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(data['success'])

        # Verify DB changes
        updated_req = db.session.get(LeaveRequest, req.id)
        self.assertEqual(updated_req.status, 'Rejected')
        
        # Verify balances restore pending to 0 and do not add to used
        updated_bal = LeaveBalance.query.filter_by(user_id=self.employee.id, leave_type='Casual').first()
        self.assertEqual(updated_bal.pending, 0)
        self.assertEqual(updated_bal.used, 0)
        self.assertEqual(updated_bal.remaining, 10)

if __name__ == '__main__':
    unittest.main()
