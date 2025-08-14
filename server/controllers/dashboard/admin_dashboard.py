from flask_restful import Resource, reqparse, Api
from flask import g
from server.models import db, User, Business, Customer, Debt
from server.utils.decorators import role_required
from server.utils.roles import ROLE_ADMIN
from datetime import datetime
from sqlalchemy import func
from . import dashboard_bp

api = Api(dashboard_bp)


class ManagerDashboard(Resource):
    @role_required(ROLE_ADMIN)
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

        # --- Date filters ---
        date_filters = []
        if args.get("start_date"):
            start_date = datetime.strptime(args["start_date"], "%Y-%m-%d")
            date_filters.append(Debt.created_at >= start_date)
        if args.get("end_date"):
            end_date = datetime.strptime(args["end_date"], "%Y-%m-%d")
            date_filters.append(Debt.created_at <= end_date)

        # --- Base query ---
        base_query = Debt.query.join(Customer).filter(Customer.business_id == business_id, *date_filters)

        # --- SUMMARY ---
        total_debts = base_query.count()

        total_amount = db.session.query(func.coalesce(func.sum(Debt.total), 0)).join(Customer).filter(
            Customer.business_id == business_id, *date_filters
        ).scalar()

        total_paid = db.session.query(func.coalesce(func.sum(Debt.amount_paid), 0)).join(Customer).filter(
            Customer.business_id == business_id, *date_filters
        ).scalar()

        total_balance = total_amount - total_paid

        # Debt status breakdown
        status_counts = dict(
            db.session.query(Debt.status, func.count(Debt.id))
            .join(Customer)
            .filter(Customer.business_id == business_id, *date_filters)
            .group_by(Debt.status)
            .all()
        )

        recovery_rate = (total_paid / total_amount * 100) if total_amount > 0 else 0

        # --- TEAM PERFORMANCE ---
        team_query = (
            db.session.query(
                User.name.label("salesperson"),
                func.sum(Debt.total).label("total_assigned"),
                func.sum(Debt.amount_paid).label("total_collected"),
                func.count(Debt.id).label("debts_count")
            )
            .join(Debt, Debt.created_by == User.id)
            .join(Customer, Customer.id == Debt.customer_id)
            .filter(Customer.business_id == business_id, *date_filters)
            .group_by(User.name)
            .order_by(func.sum(Debt.amount_paid).desc())
        )

        team_data = [
            {
                "salesperson": row.salesperson,
                "total_assigned": float(row.total_assigned or 0),
                "total_collected": float(row.total_collected or 0),
                "debts_count": row.debts_count
            }
            for row in team_query
        ]

        # --- OVERDUE ESCALATIONS ---
        overdue_query = base_query.filter(Debt.balance > 0, Debt.due_date < datetime.utcnow())\
            .order_by(Debt.due_date.asc())

        overdue_data = [
            {
                "customer": debt.customer.customer_name,
                "due_date": debt.due_date.isoformat() if debt.due_date else None,
                "balance": float(debt.balance),
                "salesperson": debt.created_by_user.name
            }
            for debt in overdue_query
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
