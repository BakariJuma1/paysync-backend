from flask_restful import Resource, reqparse, Api
from flask_jwt_extended import get_jwt_identity
from server.models import db, Customer, Debt, Payment
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER
from sqlalchemy import func
from . import dashboard_bp
from server.utils.dashboard_service import DashboardService
import logging

api = Api(dashboard_bp)

# Configure logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class OwnerDashboard(Resource):
    @role_required(ROLE_OWNER)
    def get(self):
        try:
            owner_id = get_jwt_identity()
            business_ids = DashboardService.get_business_ids(owner_id)

            # Request parser for query params
            parser = reqparse.RequestParser()
            parser.add_argument(
                "time_range",
                type=str,
                required=True,
                location="args",
                choices=("week", "month", "quarter", "year"),
                help="Time range is required and must be: week, month, quarter, year",
            )
            parser.add_argument("start_date", type=str, location="args")  # Optional
            parser.add_argument("end_date", type=str, location="args")    # Optional
            args = parser.parse_args()

            # Get date filter from service
            date_filter = DashboardService.get_date_filters(args)

            return {
                "summary": DashboardService.get_summary_stats(business_ids, date_filter),
                "time_based_analytics": DashboardService.get_time_based_analytics(business_ids, date_filter),
                "customer_segmentation": DashboardService.get_customer_segmentation(business_ids, date_filter),
                "debt_composition_by_category": DashboardService.get_debt_composition(business_ids, date_filter),
                "average_repayment_days": db.session.query(
                    func.avg(func.date_part("day", Payment.payment_date - Debt.created_at))
                )
                .join(Debt)
                .join(Customer)
                .filter(
                    Customer.business_id.in_(business_ids),
                    Debt.balance <= 0,
                    *date_filter
                )
                .scalar() or 0,
                "communication_logs": DashboardService.get_recent_logs(business_ids),
                "upcoming_due_payments": DashboardService.get_upcoming_payments(business_ids),
            }

        except ValueError as e:
            logger.warning(f"Value error in OwnerDashboard: {e}")
            return {"message": str(e)}, 400
        except Exception as e:
            logger.error(f"Error in OwnerDashboard: {e}", exc_info=True)
            return {"message": "Internal server error", "error": str(e)}, 500


api.add_resource(OwnerDashboard, "/dashboard-owner")
