from datetime import datetime, date, timedelta
from app import create_app
from models import db, User, LeaveBalance, LeaveRequest

def seed_database():
    print("Starting database seeding...")
    
    # Drop and recreate tables
    db.drop_all()
    db.create_all()
    
    print("Database tables recreated successfully.")

    # 1. Create Users
    users_data = [
        # Managers
        {
            "username": "alice",
            "password": "password123",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@company.com",
            "role": "manager",
            "department": "Engineering"
        },
        {
            "username": "bob",
            "password": "password123",
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob@company.com",
            "role": "manager",
            "department": "HR"
        },
        # Employees
        {
            "username": "charlie",
            "password": "password123",
            "first_name": "Charlie",
            "last_name": "Brown",
            "email": "charlie@company.com",
            "role": "employee",
            "department": "Engineering"
        },
        {
            "username": "david",
            "password": "password123",
            "first_name": "David",
            "last_name": "Miller",
            "email": "david@company.com",
            "role": "employee",
            "department": "Engineering"
        },
        {
            "username": "eve",
            "password": "password123",
            "first_name": "Eve",
            "last_name": "Davis",
            "email": "eve@company.com",
            "role": "employee",
            "department": "HR"
        }
    ]

    users = {}
    for u_data in users_data:
        user = User(
            username=u_data["username"],
            first_name=u_data["first_name"],
            last_name=u_data["last_name"],
            email=u_data["email"],
            role=u_data["role"],
            department=u_data["department"]
        )
        user.set_password(u_data["password"])
        db.session.add(user)
        users[u_data["username"]] = user

    db.session.commit()
    print("Users seeded.")

    # 2. Allocate Leave Balances for all users
    leave_types = [
        {"type": "Casual", "allocated": 10},
        {"type": "Sick", "allocated": 8},
        {"type": "Paid", "allocated": 15}
    ]

    for user in users.values():
        for lt in leave_types:
            balance = LeaveBalance(
                user_id=user.id,
                leave_type=lt["type"],
                allocated=lt["allocated"],
                used=0,
                pending=0
            )
            db.session.add(balance)
            
    db.session.commit()
    print("Leave balances allocated.")

    # 3. Create Sample Leave Requests
    
    # Charlie: 1 Approved Casual Leave
    req1 = LeaveRequest(
        user_id=users["charlie"].id,
        leave_type="Casual",
        start_date=date.today() - timedelta(days=10),
        end_date=date.today() - timedelta(days=9),
        duration=2,
        reason="Family event",
        status="Approved",
        applied_on=datetime.utcnow() - timedelta(days=15),
        reviewed_by=users["alice"].id,
        manager_remarks="Approved. Have a great time!"
    )
    db.session.add(req1)
    
    # Update Charlie's Casual balance
    charlie_casual = LeaveBalance.query.filter_by(user_id=users["charlie"].id, leave_type="Casual").first()
    charlie_casual.used = 2

    # Charlie: 1 Pending Sick Leave
    req2 = LeaveRequest(
        user_id=users["charlie"].id,
        leave_type="Sick",
        start_date=date.today() + timedelta(days=2),
        end_date=date.today() + timedelta(days=2),
        duration=1,
        reason="Doctor appointment",
        status="Pending",
        applied_on=datetime.utcnow() - timedelta(days=1)
    )
    db.session.add(req2)
    
    # Update Charlie's Sick balance (pending)
    charlie_sick = LeaveBalance.query.filter_by(user_id=users["charlie"].id, leave_type="Sick").first()
    charlie_sick.pending = 1

    # David: 1 Pending Paid Leave
    req3 = LeaveRequest(
        user_id=users["david"].id,
        leave_type="Paid",
        start_date=date.today() + timedelta(days=5),
        end_date=date.today() + timedelta(days=9),
        duration=5,
        reason="Summer vacation trip",
        status="Pending",
        applied_on=datetime.utcnow() - timedelta(days=2)
    )
    db.session.add(req3)
    
    # Update David's Paid balance (pending)
    david_paid = LeaveBalance.query.filter_by(user_id=users["david"].id, leave_type="Paid").first()
    david_paid.pending = 5

    # Eve: 1 Rejected Casual Leave
    req4 = LeaveRequest(
        user_id=users["eve"].id,
        leave_type="Casual",
        start_date=date.today() - timedelta(days=4),
        end_date=date.today() - timedelta(days=2),
        duration=3,
        reason="Attending a music festival",
        status="Rejected",
        applied_on=datetime.utcnow() - timedelta(days=8),
        reviewed_by=users["bob"].id,
        manager_remarks="Rejected due to critical deadlines in the HR team on these dates."
    )
    db.session.add(req4)
    # Rejections do not change used or pending balances, so balance remains untouched.

    db.session.commit()
    print("Sample leave requests seeded.")
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_database()
