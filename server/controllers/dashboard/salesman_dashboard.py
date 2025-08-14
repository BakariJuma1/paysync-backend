from flask_restful import Resource, reqparse, Api
from flask import g
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
        user_id = g.current_user.id  # Populated by role_required decorator

        # --- Parse query parameters ---
        parser = reqparse.RequestParser()
        parser.add_argument("start_date", type=str, required=False, location="args")
        parser.add_argument("end_date", type=str, required=False, location="args")
        args = parser.parse_args()

        # --- Build date filters ---
        date_filters = []
        if args.get("start_date"):
            start_date = datetime.strptime(args["start_date"], "%Y-%m-%d")
            date_filters.append(Debt.created_at >= start_date)
        if args.get("end_date"):
            end_date = datetime.strptime(args["end_date"], "%Y-%m-%d")
            date_filters.append(Debt.created_at <= end_date)

        # --- Base debt query ---
        base_query = Debt.query.filter(Debt.created_by == user_id, *date_filters)

        # --- SUMMARY ---
        total_debts = base_query.count()

        total_amount = db.session.query(func.coalesce(func.sum(Debt.total), 0))\
            .filter(Debt.created_by == user_id, *date_filters).scalar()

        total_paid = db.session.query(func.coalesce(func.sum(Debt.amount_paid), 0))\
            .filter(Debt.created_by == user_id, *date_filters).scalar()

        total_balance = total_amount - total_paid

        status_counts = dict(
            db.session.query(Debt.status, func.count(Debt.id))
            .filter(Debt.created_by == user_id, *date_filters)
            .group_by(Debt.status)
            .all()
        )

        recovery_rate = (total_paid / total_amount * 100) if total_amount > 0 else 0

        # --- CUSTOMER PORTFOLIO ---
        customers_query = (
            db.session.query(
                Customer.customer_name,
                Customer.phone,
                func.coalesce(func.sum(Debt.total - Debt.amount_paid), 0).label("balance")
            )
            .join(Debt, Debt.customer_id == Customer.id)
            .filter(Debt.created_by == user_id, *date_filters)
            .group_by(Customer.id)
        )

        customer_data = [
            {"name": name, "phone": phone, "total_balance": float(balance)}
            for name, phone, balance in customers_query
        ]

        # --- UPCOMING PAYMENTS ---
        upcoming_query = base_query.filter(
            Debt.balance > 0,
            Debt.due_date >= datetime.utcnow()
        ).order_by(Debt.due_date.asc()).limit(10)

        upcoming_data = [
            {
                "customer": debt.customer.customer_name,
                "due_date": debt.due_date.isoformat() if debt.due_date else None,
                "balance": float(debt.balance),
            }
            for debt in upcoming_query
        ]

        # --- COMMUNICATION HISTORY ---
        comm_query = (
            ChangeLog.query.filter_by(changed_by=user_id)
            .order_by(ChangeLog.timestamp.desc())
            .limit(10)
        )

        comm_data = [
            {"timestamp": c.timestamp.isoformat(), "details": c.details}
            for c in comm_query
        ]

        # --- PERFORMANCE VS TARGET ---
        target_amount = 5000  # TODO: fetch dynamically from a targets table
        achievement_percent = (total_paid / target_amount * 100) if target_amount > 0 else 0

        return {
            "summary": {
                "total_debts": total_debts,
                "total_amount": float(total_amount),
                "total_paid": float(total_paid),
                "total_balance": float(total_balance),
                "status_breakdown": status_counts,
                "recovery_rate": recovery_rate,
            },
            "customers": customer_data,
            "upcoming_payments": upcoming_data,
            "communications": comm_data,
            "performance_vs_target": {
                "target_amount": target_amount,
                "collected": float(total_paid),
                "achievement_percent": achievement_percent,
            },
        }


api.add_resource(SalesmanDashboard, "/dashboard-salesman")
