from flask_restful import Resource, Api
from flask import request, make_response, g
from flask_jwt_extended import get_jwt_identity
from server.utils.decorators import role_required
from server.utils.roles import ROLE_OWNER
from server.models import db, Debt, User, Business, Customer, Payment, ChangeLog
from . import  export_bp
from server.utils.business_pdf import generate_dashboard_pdf
from server.controllers.dashboard.owner_dashboard import OwnerDashboard  

api = Api(export_bp)

class ExportBusinessData(Resource):
    @role_required(ROLE_OWNER)
    def get(self):
      
        user_id = get_jwt_identity()
        owner = User.query.get_or_404(user_id)
       
        g.current_user = owner  
        dashboard_data = OwnerDashboard().get()
        
        pdf_buffer = generate_dashboard_pdf(dashboard_data)
        
        
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=business_{owner.business_id}_report.pdf'
        return response

api.add_resource(ExportBusinessData, "/export/business")
