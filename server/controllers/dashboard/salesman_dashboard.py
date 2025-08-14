from flask_restful import Resource, reqparse, Api
from flask import g
from flask_jwt_extended import get_jwt_identity
from server.models import db, Customer, Debt, ChangeLog
from server.utils.decorators import role_required
from server.utils.roles import ROLE_SALESPERSON
from sqlalchemy import func
from datetime import datetime
from . import dashboard_bp

api = Api(dashboard_bp)


class SalesmanDashboard(Resource):
    @role_required(ROLE_SALESPERSON)
    def get(self):
        # Parse query parameters
        parser = reqparse.RequestParser()
        parser.add_argument("start_date", type=str, required=False, location="args")
        parser.add_argument("end_date", type=str, required=False, location="args")
        args = parser.parse_args()

        user_id = g.current_user.id  # Populated by role_required decorator

        # Date filters
        date_filter = []
        if args["start_date"]:
            start_date = datetime.strptime(args["start_date"], "%Y-%m-%d")
            date_filter.append(Debt.created_at >= start_date)
        if args["end_date"]:
            end_date = datetime.strptime(args["end_date"], "%Y-%m-%d")
            date_filter.append(Debt.created_at <= end_date)

        # Base query - debts assigned to this salesman
        base_query = Debt.query.filter(Debt.created_by == user_id, *date_filter)

        # --- SUMMARY ---
        total_debts = base_query.count()
        total_amount = (
            db.session.query(func.sum(Debt.total))
            .filter(Debt.created_by == user_id, *date_filter)
            .scalar() or 0
        )
        total_paid = (
            db.session.query(func.sum(Debt.amount_paid))
            .filter(Debt.created_by == user_id, *date_filter)
            .scalar() or 0
        )
        total_balance = total_amount - total_paid
        status_counts = dict(
            db.session.query(Debt.status, func.count(Debt.id))
            .filter(Debt.created_by == user_id, *date_filter)
            .group_by(Debt.status)
            .all()
        )
        recovery_rate = (total_paid / total_amount * 100) if total_amount > 0 else 0

        # --- PERSONAL CUSTOMER PORTFOLIO ---
        customers = (
            db.session.query(Customer.customer_name, Customer.phone, func.sum(Debt.balance))
            .join(Debt, Debt.customer_id == Customer.id)
            .filter(Debt.created_by == user_id, *date_filter)
            .group_by(Customer.id)
            .all()
        )
        customer_data = [
            {"name": name, "phone": phone, "total_balance": float(balance or 0)}
            for name, phone, balance in customers
        ]

        # --- UPCOMING PAYMENTS ---
        upcoming = (
            base_query.filter(Debt.balance > 0, Debt.due_date >= datetime.utcnow())
            .order_by(Debt.due_date.asc())
            .limit(10)
            .all()
        )
        upcoming_data = [
            {
                "customer": d.customer.customer_name,
                "due_date": d.due_date.isoformat() if d.due_date else None,
                "balance": float(d.balance),
            }
            for d in upcoming
        ]

        # --- COMMUNICATION HISTORY ---
        communications = (
            ChangeLog.query.filter_by(changed_by=user_id)
            .order_by(ChangeLog.timestamp.desc())
            .limit(10)
            .all()
        )
        comm_data = [
            {"timestamp": c.timestamp.isoformat(), "details": c.details}
            for c in communications
        ]

        # --- PERFORMANCE VS TARGET ---
        target_amount = 5000  # TODO: fetch dynamically from a targets table
        achievement_percent = (total_paid / target_amount * 100) if target_amount > 0 else 0

        return {
            "summary": {
                "total_debts": total_debts,
                "total_amount": total_amount,
                "total_paid": total_paid,
                "total_balance": total_balance,
                "status_breakdown": status_counts,
                "recovery_rate": recovery_rate,
            },
            "customers": customer_data,
            "upcoming_payments": upcoming_data,
            "communications": comm_data,
            "performance_vs_target": {
                "target_amount": target_amount,
                "collected": total_paid,
                "achievement_percent": achievement_percent,
            },
        }


api.add_resource(SalesmanDashboard, "/dashboard-salesman")
