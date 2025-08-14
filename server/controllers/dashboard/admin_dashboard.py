from flask_restful import Resource, reqparse, Api
from server.models import db, User, Business, Customer, Debt
from server.utils.decorators import role_required
from server.utils.roles import ROLE_ADMIN
from sqlalchemy import func
from datetime import datetime
from . import dashboard_bp

api = Api(dashboard_bp)

class ManagerDashboard(Resource):
    @role_required(ROLE_ADMIN)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("business_id", type=int, required=True, location="args")
        parser.add_argument("start_date", type=str, required=False, location="args")
        parser.add_argument("end_date", type=str, required=False, location="args")
        args = parser.parse_args()

        business_id = args["business_id"]

        business = Business.query.get(business_id)
        if not business:
            return {"message": "Business not found"}, 404

        # Date filters
        date_filter = []
        if args.get("start_date"):
            start_date = datetime.strptime(args["start_date"], "%Y-%m-%d")
            date_filter.append(Debt.created_at >= start_date)
        if args.get("end_date"):
            end_date = datetime.strptime(args["end_date"], "%Y-%m-%d")
            date_filter.append(Debt.created_at <= end_date)

        base_query = Debt.query.join(Customer).filter(Customer.business_id == business_id, *date_filter)

        total_debts = base_query.count()
        total_amount = db.session.query(func.sum(Debt.total)).join(Customer).filter(Customer.business_id == business_id, *date_filter).scalar() or 0
        total_paid = db.session.query(func.sum(Debt.amount_paid)).join(Customer).filter(Customer.business_id == business_id, *date_filter).scalar() or 0
        total_balance = sum(d.balance for d in base_query.all())
        recovery_rate = (total_paid / total_amount * 100) if total_amount else 0

        status_counts = dict(
            db.session.query(Debt.status, func.count(Debt.id))
            .join(Customer)
            .filter(Customer.business_id == business_id, *date_filter)
            .group_by(Debt.status)
            .all()
        )

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

        team_data = [
            {
                "salesperson": name,
                "total_assigned": float(total or 0),
                "total_collected": float(collected or 0),
                "debts_count": debts_count
            }
            for name, total, collected, debts_count in team_performance
        ]

        overdue_list = base_query.filter(Debt.balance > 0, Debt.due_date < datetime.utcnow()).order_by(Debt.due_date.asc()).all()
        overdue_data = [
            {
                "customer": d.customer.customer_name,
                "due_date": d.due_date.isoformat() if d.due_date else None,
                "balance": d.balance,
                "salesperson": d.created_by_user.name
            }
            for d in overdue_list
        ]

        return {
            "summary": {
                "total_debts": total_debts,
                "total_amount": float(total_amount),
                "total_paid": float(total_paid),
                "total_balance": float(total_balance),
                "status_breakdown": status_counts,
                "recovery_rate": recovery_rate
            },
            "team_performance": team_data,
            "overdue_escalations": overdue_data,
            "collection_efficiency": recovery_rate
        }

api.add_resource(ManagerDashboard, "/dashboard-manager")
