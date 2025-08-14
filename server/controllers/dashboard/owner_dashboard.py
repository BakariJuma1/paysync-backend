from flask_restful import Resource, reqparse, Api
from flask import g
from server.models import db, Debt, Payment, User, Business
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER
from sqlalchemy import func
from datetime import datetime, timedelta
from . import dashboard_bp

api = Api(dashboard_bp)

class OwnerDashboard(Resource):
    @role_required(ROLE_OWNER)
    def get(self):
        try:
            # --- Parse query parameters ---
            parser = reqparse.RequestParser()
            parser.add_argument(
                "time_range", type=str, required=False,
                choices=("day", "week", "month", "year")
            )
            args = parser.parse_args()

            owner_id = getattr(g.current_user, "id", None)
            if not owner_id:
                return {"message": "User not authenticated"}, 401

            time_range = args.get("time_range", "month")

            # --- Filter businesses owned by this owner ---
            businesses = Business.query.filter_by(owner_id=owner_id).all()
            business_ids = [b.id for b in businesses]

            if not business_ids:
                return {"message": "No businesses found for this owner"}, 404

            # --- Base debt query ---
            base_query = Debt.query.filter(Debt.business_id.in_(business_ids))

            # --- Apply time range filter ---
            now = datetime.utcnow()
            start_date = None
            if time_range == "day":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_range == "week":
                start_date = now - timedelta(days=now.weekday())
            elif time_range == "month":
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif time_range == "year":
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

            if start_date:
                base_query = base_query.filter(Debt.created_at >= start_date)

            # --- SUMMARY ---
            total_debts = base_query.count()
            total_amount = db.session.query(func.sum(Debt.total))\
                .filter(Debt.business_id.in_(business_ids)).scalar() or 0
            total_paid = db.session.query(func.sum(Debt.amount_paid))\
                .filter(Debt.business_id.in_(business_ids)).scalar() or 0
            total_balance = total_amount - total_paid
            recovery_rate = (total_paid / total_amount * 100) if total_amount else 0

            # --- AVERAGE REPAYMENT TIME ---
            avg_days_query = db.session.query(
                func.avg(func.date_part("day", Payment.payment_date - Debt.created_at))
            ).join(Debt, Debt.id == Payment.debt_id)\
             .filter(Debt.business_id.in_(business_ids))
            avg_repayment_days = avg_days_query.scalar() or 0

            return {
                "summary": {
                    "total_debts": total_debts,
                    "total_amount": float(total_amount),
                    "total_paid": float(total_paid),
                    "total_balance": float(total_balance),
                    "recovery_rate": recovery_rate,
                    "avg_repayment_days": avg_repayment_days,
                }
            }

        except Exception as e:
            # Log the error so you can see it in server logs
            import logging
            logging.exception("Error fetching owner dashboard")
            return {"message": "Error fetching dashboard", "details": str(e)}, 500

api.add_resource(OwnerDashboard, "/dashboard-owner")
