from flask_restful import Resource, reqparse, Api
from flask_jwt_extended import get_jwt_identity
from server.models import db, User, Business, Customer, Debt, Payment, Item, ChangeLog
from server.utils.decorators import role_required
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from . import dashboard_bp

api = Api(dashboard_bp) 

# server/resources/dashboard.py
class ManagerDashboard(Resource):
    @role_required("admin")  # Manager role
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("business_id", type=int, required=True, help="Business ID is required")
        parser.add_argument("start_date", type=str, required=False)
        parser.add_argument("end_date", type=str, required=False)
        args = parser.parse_args()

        business_id = args["business_id"]

        # Validate business exists
        business = Business.query.get(business_id)
        if not business:
            return {"message": "Business not found"}, 404

        # Date filters
        date_filter = []
        if args["start_date"]:
            start_date = datetime.strptime(args["start_date"], "%Y-%m-%d")
            date_filter.append(Debt.created_at >= start_date)
        if args["end_date"]:
            end_date = datetime.strptime(args["end_date"], "%Y-%m-%d")
            date_filter.append(Debt.created_at <= end_date)

        # Base query (only this business)
        base_query = db.session.query(Debt).join(Customer).filter(Customer.business_id == business_id, *date_filter)

        # --- SUMMARY ---
        total_debts = base_query.count()
        total_amount = db.session.query(func.sum(Debt.total)).join(Customer).filter(Customer.business_id == business_id, *date_filter).scalar() or 0
        total_paid = db.session.query(func.sum(Debt.amount_paid)).join(Customer).filter(Customer.business_id == business_id, *date_filter).scalar() or 0
        total_balance = total_amount - total_paid
        status_counts = dict(db.session.query(Debt.status, func.count(Debt.id)).join(Customer).filter(Customer.business_id == business_id, *date_filter).group_by(Debt.status).all())
        recovery_rate = (total_paid / total_amount * 100) if total_amount > 0 else 0

        # --- SALES TEAM PERFORMANCE ---
        team_performance = (
            db.session.query(
                User.name.label("salesperson"),
                func.sum(Debt.total).label("total_assigned"),
                func.sum(Debt.amount_paid).label("total_collected"),
                func.count(Debt.id).label("debts_count")
            )
            .join(Debt, Debt.created_by == User.id)
            .join(Customer, Customer.id == Debt.customer_id)
            .filter(Customer.business_id == business_id, *date_filter)
            .group_by(User.name)
            .order_by(func.sum(Debt.amount_paid).desc())
            .all()
        )
        team_data = [{
            "salesperson": name,
            "total_assigned": float(total or 0),
            "total_collected": float(collected or 0),
            "debts_count": debts_count
        } for name, total, collected, debts_count in team_performance]

        # --- OVERDUE ESCALATIONS ---
        overdue_list = db.session.query(Debt).join(Customer).filter(
            Customer.business_id == business_id,
            Debt.balance > 0,
            Debt.due_date < datetime.utcnow()
        ).order_by(Debt.due_date.asc()).all()
        overdue_data = [{
            "customer": d.customer.customer_name,
            "due_date": d.due_date.isoformat() if d.due_date else None,
            "balance": d.balance,
            "salesperson": d.created_by_user.name
        } for d in overdue_list]

        # --- COLLECTION EFFICIENCY ---
        collection_efficiency = recovery_rate

        return {
            "summary": {
                "total_debts": total_debts,
                "total_amount": total_amount,
                "total_paid": total_paid,
                "total_balance": total_balance,
                "status_breakdown": status_counts,
                "recovery_rate": recovery_rate
            },
            "team_performance": team_data,
            "overdue_escalations": overdue_data,
            "collection_efficiency": collection_efficiency
        }

api.add_resource(ManagerDashboard, '/dashboard-manager')