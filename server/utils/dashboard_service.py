from datetime import datetime, timedelta
from sqlalchemy import func, extract
from server.models import db, User, Business, Debt, Customer, Item, ChangeLog, Payment



class DashboardService:
    @staticmethod
    def get_business_ids(owner_id):
        businesses = Business.query.filter_by(owner_id=owner_id).all()
        if not businesses:
            raise ValueError("Business setup required")
        return [b.id for b in businesses]

    @staticmethod
    def get_date_filters(args):
        date_filter = []
        if args.get("start_date"):
            start_date = datetime.strptime(args["start_date"], "%Y-%m-%d")
            date_filter.append(Debt.created_at >= start_date)
        if args.get("end_date"):
            end_date = datetime.strptime(args["end_date"], "%Y-%m-%d")
            date_filter.append(Debt.created_at <= end_date)
        return date_filter

    @staticmethod
    def get_summary_stats(business_ids, date_filter):
        base_query = db.session.query(Debt).join(Customer).filter(
            Customer.business_id.in_(business_ids), *date_filter
        )
        
        total_debts = base_query.count()
        total_amount = db.session.query(func.sum(Debt.total)).join(Customer).filter(
            Customer.business_id.in_(business_ids), *date_filter
        ).scalar() or 0
        total_paid = db.session.query(func.sum(Debt.amount_paid)).join(Customer).filter(
            Customer.business_id.in_(business_ids), *date_filter
        ).scalar() or 0
        
        return {
            "total_debts": total_debts,
            "total_amount": total_amount,
            "total_paid": total_paid,
            "total_balance": total_amount - total_paid,
            "status_breakdown": dict(
                db.session.query(Debt.status, func.count(Debt.id))
                .join(Customer)
                .filter(Customer.business_id.in_(business_ids), *date_filter)
                .group_by(Debt.status)
                .all()
            ),
            "recovery_rate": (total_paid / total_amount * 100) if total_amount > 0 else 0,
            "collection_efficiency": (total_paid / total_amount * 100) if total_amount > 0 else 0
        }

    @staticmethod
    def get_time_based_analytics(business_ids, date_filter):
        trends_monthly = (
            db.session.query(
                extract('year', Debt.created_at).label('year'),
                extract('month', Debt.created_at).label('month'),
                func.sum(Debt.total).label('total')
            )
            .join(Customer)
            .filter(Customer.business_id.in_(business_ids), *date_filter)
            .group_by('year', 'month')
            .order_by('year', 'month')
            .all()
        )
        return [{"year": int(y), "month": int(m), "total": float(t)} for y, m, t in trends_monthly]

    @staticmethod
    def get_customer_segmentation(business_ids, date_filter):
        segmentation = {"high_risk": 0, "medium_risk": 0, "low_risk": 0}
        debts = db.session.query(Debt).join(Customer).filter(
            Customer.business_id.in_(business_ids), *date_filter
        ).all()
        
        for debt in debts:
            if debt.balance > 0:
                days_overdue = (datetime.utcnow() - (debt.due_date or datetime.utcnow())).days
                if days_overdue > 30:
                    segmentation["high_risk"] += 1
                elif 7 < days_overdue <= 30:
                    segmentation["medium_risk"] += 1
                else:
                    segmentation["low_risk"] += 1
        return segmentation

    @staticmethod
    def get_debt_composition(business_ids, date_filter):
        return dict(
            db.session.query(Item.category, func.sum(Item.price * Item.quantity))
            .join(Debt).join(Customer)
            .filter(Customer.business_id.in_(business_ids), *date_filter)
            .group_by(Item.category)
            .all()
        )

    @staticmethod
    def get_recent_logs(business_ids):
        user_ids = [u.id for u in User.query.filter(User.business_id.in_(business_ids)).all()]
        logs = ChangeLog.query.filter(ChangeLog.changed_by.in_(user_ids)).order_by(
            ChangeLog.timestamp.desc()).limit(10).all()
        return [{
            "entity_type": log.entity_type,
            "action": log.action,
            "timestamp": log.timestamp.isoformat(),
            "details": log.details
        } for log in logs]

    @staticmethod
    def get_upcoming_payments(business_ids):
        upcoming = db.session.query(Debt).join(Customer).filter(
            Customer.business_id.in_(business_ids),
            Debt.balance > 0,
            Debt.due_date >= datetime.utcnow(),
            Debt.due_date <= datetime.utcnow() + timedelta(days=7)
        ).all()
        return [{
            "customer": d.customer.customer_name,
            "due_date": d.due_date.isoformat() if d.due_date else None,
            "balance": d.balance
        } for d in upcoming]