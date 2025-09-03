from cmath import log
from flask_restful import Resource, reqparse, Api
from flask import g
from server.models import db, Business, Debt, Payment, User, Customer,ChangeLog
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER
from sqlalchemy import func, case,desc
from datetime import datetime, timedelta
from . import dashboard_bp

api = Api(dashboard_bp)

class OwnerDashboard(Resource):
    @role_required(ROLE_OWNER)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "time_range",
            type=str,
            required=False,
            choices=("day", "week", "month", "year"),
            location="args"
        )
        parser.add_argument("start_date", type=str, required=False, location="args")
        parser.add_argument("end_date", type=str, required=False, location="args")
        args = parser.parse_args()
        
        time_range = args.get("time_range", "month")
        start_date = args.get("start_date")
        end_date = args.get("end_date")

        owner_id = g.current_user.id

        # All businesses owned by this owner
        businesses = Business.query.filter_by(owner_id=owner_id).all()
        business_ids = [b.id for b in businesses]

        if not business_ids:
            return {"message": "No businesses found for this owner"}, 404

        # Base query filters
        base_filters = [Customer.business_id.in_(business_ids)]
        date_filters = []

        # Apply date range filter
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            date_filters.append(Debt.created_at >= start_date_obj)
        
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            date_filters.append(Debt.created_at <= end_date_obj)

        # Apply time range filter if no specific dates
        if not start_date and not end_date:
            now = datetime.utcnow()
            if time_range == "day":
                start_date_obj = now.replace(hour=0, minute=0, second=0, microsecond=0)
                date_filters.append(Debt.created_at >= start_date_obj)
            elif time_range == "week":
                start_date_obj = now - timedelta(days=now.weekday())
                date_filters.append(Debt.created_at >= start_date_obj)
            elif time_range == "month":
                start_date_obj = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                date_filters.append(Debt.created_at >= start_date_obj)
            elif time_range == "year":
                start_date_obj = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                date_filters.append(Debt.created_at >= start_date_obj)

        # SUMMARY
        total_debts = Debt.query.select_from(Debt).join(Customer, Debt.customer_id == Customer.id).filter(
            Customer.business_id.in_(business_ids),
            *date_filters
        ).count()
        
        total_amount = db.session.query(func.sum(Debt.total))\
            .select_from(Debt)\
            .join(Customer, Debt.customer_id == Customer.id)\
            .filter(Customer.business_id.in_(business_ids), *date_filters)\
            .scalar() or 0
        
        total_paid = db.session.query(func.sum(Debt.amount_paid))\
            .select_from(Debt)\
            .join(Customer, Debt.customer_id == Customer.id)\
            .filter(Customer.business_id.in_(business_ids), *date_filters)\
            .scalar() or 0
        
        total_balance = total_amount - total_paid
        recovery_rate = (total_paid / total_amount * 100) if total_amount > 0 else 0

        # STATUS BREAKDOWN (for pie chart)
        status_breakdown = dict(
            db.session.query(Debt.status, func.count(Debt.id))
            .select_from(Debt)
            .join(Customer, Debt.customer_id == Customer.id)
            .filter(Customer.business_id.in_(business_ids), *date_filters)
            .group_by(Debt.status)
            .all()
        )

        # TOP DEBTORS
        top_debtors_query = (
            db.session.query(
                Customer.customer_name,
                Customer.phone,
                func.sum(Debt.balance).label("total_balance"),
                Debt.status
            )
            .select_from(Debt)
            .join(Customer, Debt.customer_id == Customer.id)
            .filter(Customer.business_id.in_(business_ids), *date_filters, Debt.balance > 0)
            .group_by(Customer.id, Customer.customer_name, Customer.phone, Debt.status)
            .order_by(func.sum(Debt.balance).desc())
            .limit(10)
            .all()
        )
        
        top_debtors = [
            {
                "customer": customer,
                "phone": phone,
                "amount": float(total_balance),
                "status": status
            }
            for customer, phone, total_balance, status in top_debtors_query
        ]

        # UPCOMING PAYMENTS
        upcoming_payments_query = (
            db.session.query(
                Customer.customer_name,
                Debt.due_date,
                Debt.balance
            )
            .select_from(Debt)
            .join(Customer, Debt.customer_id == Customer.id)
            .filter(
                Customer.business_id.in_(business_ids),
                *date_filters,
                Debt.balance > 0,
                Debt.due_date >= datetime.utcnow(),
                Debt.due_date <= datetime.utcnow() + timedelta(days=30)
            )
            .order_by(Debt.due_date.asc())
            .limit(10)
            .all()
        )
        
        upcoming_payments = [
            {
                "customer": customer,
                "due_date": due_date.isoformat() if due_date else None,
                "amount": float(balance)
            }
            for customer, due_date, balance in upcoming_payments_query
        ]

        # PERFORMANCE VS TARGET (mock data )
        performance_vs_target = {
            "target_amount": total_amount * 1.2,  
            "collected": total_paid,
            "achievement_percent": (total_paid / (total_amount * 1.2) * 100) if total_amount > 0 else 0
        }

        # RECENT COMMUNICATIONS (mock data - you'll need to implement actual communication logs)
        logs = (
            ChangeLog.query.filter(
                ChangeLog.entity_type == "Debt",
                ChangeLog.action == "reminder",
                ChangeLog.timestamp >= start_date_obj if start_date else True,
                ChangeLog.timestamp <= end_date_obj if end_date else True, 
            )
            .order_by(ChangeLog.timestamp.desc())
            .limit(10)
            .all()
        )
        communication_logs = [
            {
                "message": f"{log.details.get('reminder_type','')} reminder via {log.details.get('channel','')} ({log.details.get('status','')})",
                "timestamp": log.timestamp.isoformat(),
                "debt_id": log.entity_id
            }
            for log in logs
        ]

        # AVERAGE REPAYMENT TIME
        avg_days_query = (
            db.session.query(func.avg(func.date_part("day", Payment.payment_date - Debt.created_at)))
            .join(Debt, Debt.id == Payment.debt_id)
            .join(Customer)
            .filter(Customer.business_id.in_(business_ids), *date_filters)
        )
        avg_repayment_days = avg_days_query.scalar() or 0

        # SALES TEAM PERFORMANCE
        team_performance_query = (
            db.session.query(
                User.name.label("salesperson"),
                func.count(Debt.id).label("debts_count"),
                func.sum(Debt.total).label("total_assigned"),
                func.sum(Debt.amount_paid).label("total_collected")
            )
            .join(Debt, Debt.created_by == User.id)
            .join(Customer)
            .filter(Customer.business_id.in_(business_ids), *date_filters)
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

        # OVERDUE DEBTS
        overdue_query = Debt.query.select_from(Debt).join(Customer, Debt.customer_id == Customer.id).filter(
            Customer.business_id.in_(business_ids),
            *date_filters,
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
            "business":{
                 "name":businesses[0].name
            },
            "summary": {
                "total_debts": total_debts,
                "total_amount": float(total_amount),
                "total_paid": float(total_paid),
                "total_balance": float(total_balance),
                "recovery_rate": recovery_rate,
                "avg_repayment_days": avg_repayment_days,
                "status_breakdown": status_breakdown
            },
            "performance_vs_target": performance_vs_target,
            "customer_segmentation": {
                "top_debtors": top_debtors
            },
            "upcoming_due_payments": upcoming_payments,
            "communication_logs": communication_logs,
            "team_performance": team_data,
            "overdue_debts": overdue_data,
        }

api.add_resource(OwnerDashboard, "/dashboard-owner")