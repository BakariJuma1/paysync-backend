from flask_restful import Resource, reqparse, Api
from flask import g
from server.models import db, Business, Debt, Payment, User
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER
from sqlalchemy import func
from datetime import datetime, timedelta
from . import dashboard_bp

api = Api(dashboard_bp)


class OwnerDashboard(Resource):
    @role_required(ROLE_OWNER)
    def get(self):
        # --- Parse query parameters from GET ---
        parser = reqparse.RequestParser()
        parser.add_argument(
            "time_range", type=str, required=False,
            choices=("day", "week", "month", "year"),
            location="args"
        )
        args = parser.parse_args()

        owner_id = g.current_user.id
        time_range = args.get("time_range", "month")

        businesses = Business.query.filter_by(owner_id=owner_id).all()
        business_ids = [b.id for b in businesses]

        base_query = Debt.query.join(Payment, isouter=True).filter(Debt.business_id.in_(business_ids))

        # --- Time range filter ---
        now = datetime.utcnow()
        if time_range == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == "week":
            start_date = now - timedelta(days=now.weekday())
        elif time_range == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif time_range == "year":
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = None

        if start_date:
            base_query = base_query.filter(Debt.created_at >= start_date)

        total_debts = base_query.count()
        total_amount = db.session.query(func.sum(Debt.total)).filter(Debt.business_id.in_(business_ids)).scalar() or 0
        total_paid = db.session.query(func.sum(Debt.amount_paid)).filter(Debt.business_id.in_(business_ids)).scalar() or 0
        total_balance = total_amount - total_paid
        recovery_rate = (total_paid / total_amount * 100) if total_amount else 0

        avg_days_query = (
            db.session.query(func.avg(func.date_part("day", Payment.payment_date - Debt.created_at)))
            .join(Debt, Debt.id == Payment.debt_id)
            .filter(Debt.business_id.in_(business_ids))
        )
        avg_repayment_days = avg_days_query.scalar() or 0

        team_performance_query = (
            db.session.query(
                User.name.label("salesperson"),
                func.count(Debt.id).label("debts_count"),
                func.sum(Debt.total).label("total_assigned"),
                func.sum(Debt.amount_paid).label("total_collected")
            )
            .join(Debt, Debt.created_by == User.id)
            .filter(Debt.business_id.in_(business_ids))
            .group_by(User.name)
            .order_by(func.sum(Debt.amount_paid).desc())
        )
        team_data = [
            {
                "salesperson": row.salesperson,
                "debts_count": row.debts_count,
                "total_assigned": float(row.total_assigned or 0),
                "total_collected": float(row.total_collected or 0),
            }
            for row in team_performance_query
        ]

        overdue_query = Debt.query.filter(
            Debt.business_id.in_(business_ids),
            Debt.balance > 0,
            Debt.due_date < datetime.utcnow()
        ).order_by(Debt.due_date.asc())
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
                "recovery_rate": recovery_rate,
                "avg_repayment_days": avg_repayment_days,
            },
            "team_performance": team_data,
            "overdue_debts": overdue_data,
        }


api.add_resource(OwnerDashboard, "/dashboard-owner")
