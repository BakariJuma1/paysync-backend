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
        try:
            user_id = getattr(g.current_user, "id", None)
            if not user_id:
                return {"message": "User not authenticated"}, 401

            parser = reqparse.RequestParser()
            parser.add_argument("start_date", type=str, required=False, location="args")
            parser.add_argument("end_date", type=str, required=False, location="args")
            args = parser.parse_args()

            date_filter = []
            if args.get("start_date"):
                start_date = datetime.strptime(args["start_date"], "%Y-%m-%d")
                date_filter.append(Debt.created_at >= start_date)
            if args.get("end_date"):
                end_date = datetime.strptime(args["end_date"], "%Y-%m-%d")
                date_filter.append(Debt.created_at <= end_date)

            base_query = Debt.query.filter(Debt.created_by == user_id, *date_filter)

            total_debts = base_query.count()
            total_amount = db.session.query(func.sum(Debt.total))\
                .filter(Debt.created_by == user_id, *date_filter).scalar() or 0
            total_paid = db.session.query(func.sum(Debt.amount_paid))\
                .filter(Debt.created_by == user_id, *date_filter).scalar() or 0
            total_balance = total_amount - total_paid
            recovery_rate = (total_paid / total_amount * 100) if total_amount else 0

            # Customers portfolio
            customers = db.session.query(
                Customer.customer_name,
                Customer.phone,
                func.sum(Debt.total - Debt.amount_paid).label("balance")
            ).join(Debt, Debt.customer_id == Customer.id)\
             .filter(Debt.created_by == user_id, *date_filter)\
             .group_by(Customer.id)\
             .all()

            customer_data = [
                {"name": name, "phone": phone, "total_balance": float(balance or 0)}
                for name, phone, balance in customers
            ]

            # Upcoming payments
            upcoming = base_query.filter(Debt.balance > 0, Debt.due_date >= datetime.utcnow())\
                .order_by(Debt.due_date.asc()).limit(10).all()
            upcoming_data = [
                {"customer": d.customer.customer_name, "due_date": d.due_date.isoformat() if d.due_date else None,
                 "balance": float(d.balance)}
                for d in upcoming
            ]

            # Communication history
            communications = ChangeLog.query.filter_by(changed_by=user_id)\
                .order_by(ChangeLog.timestamp.desc()).limit(10).all()
            comm_data = [{"timestamp": c.timestamp.isoformat(), "details": c.details} for c in communications]

            # Performance vs target
            target_amount = 5000  # TODO: fetch dynamically
            achievement_percent = (total_paid / target_amount * 100) if target_amount > 0 else 0

            return {
                "summary": {
                    "total_debts": total_debts,
                    "total_amount": float(total_amount),
                    "total_paid": float(total_paid),
                    "total_balance": float(total_balance),
                    "recovery_rate": recovery_rate
                },
                "customers": customer_data,
                "upcoming_payments": upcoming_data,
                "communications": comm_data,
                "performance_vs_target": {
                    "target_amount": target_amount,
                    "collected": float(total_paid),
                    "achievement_percent": achievement_percent
                }
            }

        except Exception as e:
            import logging
            logging.exception("Error fetching salesman dashboard")
            return {"message": "Error fetching dashboard", "details": str(e)}, 500

api.add_resource(SalesmanDashboard, "/dashboard-salesman")
