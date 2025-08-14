# seed.py
from datetime import datetime, timedelta
from server import create_app
from server.models import (
    db, User, Business, Customer, Debt, 
    Item, Payment, Invitation, FinanceSettings,
    ChangeLog
)
from werkzeug.security import generate_password_hash
import random

def seed():
    
    
   
        print("🌱 Seeding PaySync database...")

        # ========== USERS ==========
        users_to_add = []
        
        # Owner
        owner = User.query.filter_by(email="owner@example.com").first()
        if not owner:
            owner = User(
                name="Business Owner",
                email="owner@example.com",
                password_hash=generate_password_hash("owner123"),
                role="owner",
                is_verified=True,
                created_at=datetime.utcnow()
            )
            users_to_add.append(owner)

        # Admin
        admin = User.query.filter_by(email="admin@example.com").first()
        if not admin:
            admin = User(
                name="Admin User",
                email="admin@example.com",
                password_hash=generate_password_hash("admin123"),
                role="admin",
                is_verified=True,
                created_at=datetime.utcnow()
            )
            users_to_add.append(admin)

        # Salesperson
        salesperson = User.query.filter_by(email="sales@example.com").first()
        if not salesperson:
            salesperson = User(
                name="Sales Person",
                email="sales@example.com",
                password_hash=generate_password_hash("sales123"),
                role="salesperson",
                is_verified=True,
                created_at=datetime.utcnow()
            )
            users_to_add.append(salesperson)

        if users_to_add:
            db.session.add_all(users_to_add)
            db.session.commit()
        print("✅ Users seeded")

        # ========== BUSINESS ==========
        business = Business.query.filter_by(name="Test Business Inc.").first()
        if not business and owner:
            business = Business(
                name="Test Business Inc.",
                owner_id=owner.id,
                address="123 Main St, Nairobi",
                phone="+254700000000",
                email="info@testbusiness.com",
                website="https://testbusiness.com",
                description="Sample business for testing PaySync"
            )
            db.session.add(business)
            db.session.commit()

            # Assign business to users
            admin.business_id = business.id
            salesperson.business_id = business.id
            db.session.commit()
        print("✅ Business seeded")

        # ========== FINANCE SETTINGS ==========
        if business and not FinanceSettings.query.filter_by(business_id=business.id).first():
            finance_settings = FinanceSettings(
                business_id=business.id,
                default_currency="KES",
                payment_due_day=15,
                late_fee_type="percentage",
                late_fee_value=5.0,
                reminder_method="email",
                updated_by=owner.id
            )
            db.session.add(finance_settings)
            db.session.commit()
        print("✅ Finance settings seeded")

        # ========== CUSTOMERS ==========
        if business and User.query.count() >= 3:  # Ensure users exist
            existing_customers = Customer.query.count()
            if existing_customers < 5:
                users = [owner, admin, salesperson]
                for i in range(1, 6 - existing_customers + 1):
                    customer = Customer(
                        customer_name=f"Customer {existing_customers + i}",
                        phone=f"+25471100000{existing_customers + i}",
                        id_number=f"ID0000{existing_customers + i}",
                        business_id=business.id,
                        created_by=random.choice([u.id for u in users])
                    )
                    db.session.add(customer)
                db.session.commit()
        print("✅ Customers seeded")

        # ========== DEBTS & ITEMS ==========
        customers = Customer.query.all()
        if customers:
            debt_statuses = ["unpaid", "partial", "paid"]
            categories = ["Electronics", "Furniture", "Services"]
            
            for customer in customers:
                existing_debts = Debt.query.filter_by(customer_id=customer.id).count()
                if existing_debts == 0:
                    debt = Debt(
                        customer_id=customer.id,
                        total=0,
                        amount_paid=0,
                        balance=0,
                        due_date=datetime.utcnow() + timedelta(days=30),
                        status=random.choice(debt_statuses),
                        created_by=random.choice([owner.id, admin.id, salesperson.id])
                    )
                    db.session.add(debt)
                    db.session.flush()
                    
                    # Add items
                    for j in range(1, 4):
                        item = Item(
                            debt_id=debt.id,
                            name=f"Product {j}",
                            price=random.uniform(100, 1000),
                            quantity=random.randint(1, 5),
                            category=random.choice(categories)
                        )
                        db.session.add(item)
                    
                    # Calculate totals
                    debt.total = sum(item.total_price for item in debt.items)
                    debt.amount_paid = (debt.total * 0.3 if debt.status == "partial" 
                                       else debt.total if debt.status == "paid" 
                                       else 0)
                    debt.balance = debt.total - debt.amount_paid
                    
                    # Add payment if not unpaid
                    if debt.status != "unpaid":
                        payment = Payment(
                            debt_id=debt.id,
                            amount=debt.amount_paid,
                            method=random.choice(["cash", "mobile money", "bank"]),
                            received_by=random.choice([owner.id, admin.id, salesperson.id])
                        )
                        db.session.add(payment)
            db.session.commit()
        print("✅ Debts and items seeded")

        # ========== INVITATIONS ==========
        if business and not Invitation.query.first():
            for i in range(1, 3):
                invitation = Invitation(
                    token=f"invite-token-{i}",
                    email=f"invite{i}@example.com",
                    name=f"Invited User {i}",
                    role="salesperson",
                    business_id=business.id,
                    created_by=owner.id,
                    expires_at=datetime.utcnow() + timedelta(days=7)
                )
                db.session.add(invitation)
            db.session.commit()
        print("✅ Invitations seeded")

        # ========== CHANGE LOGS ==========
        if not ChangeLog.query.first():
            changelogs = [
                ChangeLog(
                    entity_type="Debt",
                    entity_id=1,
                    action="create",
                    changed_by=owner.id,
                    details={"amount": 1500, "customer": "Customer 1"}
                ),
                ChangeLog(
                    entity_type="Payment",
                    entity_id=1,
                    action="update",
                    changed_by=admin.id,
                    details={"amount": 500, "method": "mobile money"}
                )
            ]
            db.session.add_all(changelogs)
            db.session.commit()
        print("✅ Change logs seeded")

        print("🌱 PaySync seeding complete!")
        print("Test accounts:")
        print(f"  👑 Owner: owner@example.com / owner123")
        print(f"  🔧 Admin: admin@example.com / admin123")
        print(f"  💼 Sales: sales@example.com / sales123")

if __name__ == "__main__":
    seed()