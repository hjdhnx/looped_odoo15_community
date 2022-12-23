import json
import logging
import functools
import werkzeug.wrappers
from datetime import datetime, timedelta
from odoo import http
from odoo.addons.pos_custom.controllers.common import invalid_response, valid_response
from odoo.exceptions import AccessDenied, AccessError
from odoo.http import request, Response


_logger = logging.getLogger(__name__)

def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token1 = False
        if request.httprequest.headers.get("access_token",False):
            access_token1 = request.httprequest.headers.get("access_token") 
        if request.httprequest.headers.get("access-token",False):
            access_token1 = request.httprequest.headers.get("access-token") 
        if not access_token1:
            # return invalid_response("access_token_not_found", "missing access token in request header", 401)
            # Response.status = "401"
            response = {"code": "401", "message": "missing access token in request header..",
            "er1":str(request.httprequest),"er2":str(request.httprequest.headers)}
            return response
        # access_token_data = request.env["api.access_token"].sudo().search([("token", "=", access_token)],
        #                                                                   order="id DESC", limit=1)
        # if access_token_data.find_or_create_token(user_id=access_token_data.user_id.id) != access_token:
        access_token2 = request.env["api.access_token"].sudo().search([("token", "=", access_token1)], limit=1)
        if access_token2:
            if not access_token2.is_valid():        
                # return invalid_response("access_token..", "token seems to have expired or invalid", 401)
                # Response.status = "403"
                response = {"code": "403", "message": "token seems to have expired or invalid..",}
                return response
        else:
            # Response.status = "403"
            response = {"code": "403", "message": "token seems to have expired or invalid..",}
            return response                
        # request.session.uid = access_token_data.user_id.id
        request.uid = access_token2.user_id.id
        return func(self, *args, **kwargs)
    return wrap

    # if request.env.user.id == request.env.ref('base.public_user').id:
    #     return request.render('web.login', {})

class AccessToken(http.Controller):
    @http.route("/api/cashier_login", methods=["POST"], type="json", auth="none", csrf=False)
    def cashier_login(self, **kw):
        # db = kw.get('database')
        user_id = kw.get('user_id')
        security_pin = kw.get('security_pin')
        pos_id = kw.get('pos_id')
        _credentials_includes_in_headers = all([user_id, security_pin,])
        if not _credentials_includes_in_headers:
            # Response.status = "403"
            response = {
                        "message": "Either of the following are missing [user_id, security_pin,].."
                        }                                 
            return response
        user_id = request.env['res.users'].sudo().search([('id','=',user_id),('security_pin','=',security_pin)])
        
        if not user_id:
            # Response.status = "403"
            response = {
                        "message": "User ID not Found or Security PIN not Correct"
                        }                                 
            return response
        
        
        exist_pos_id = user_id.available_pos_ids.filtered(lambda x: int(pos_id) in x.ids)
        if not exist_pos_id:
            # Response.status = "403"   
            response = {
                        "message": "You have no access to this pos."
                        }                              
            return response            
        # access_token_id = request.env["api.access_token"].find_or_create_token(user_id=uid, create=True)
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # Response.status = "200"
        
        time_now = datetime.now()
        request.env['res.users.pos.log'].sudo().create({
            'user_id':user_id.id,
            'pos_config_id':pos_id,
            'login_date':time_now
        })

        response = {
                    "message": "Cashier Found successfully.",
                    'body': {         
                    "uid": user_id.id,
                    "name": user_id.name,
                    "email": user_id.partner_id.email,
                    "mobile": user_id.partner_id.mobile,
                    "image_1920": base_url + '/web/image?' + 'model=res.partner&id=' + 
                        str(user_id.partner_id.id) + '&field=image_1920',
                    "pos_user_type": user_id.pos_user_type,
                    "security_group": [
                                        {
                                        'id': security_group.id,
                                        'name': security_group.name,
                                        'roles':[
                                                    {
                                                        'id': role.id,
                                                        'key': role.key,
                                                        'name_ar':role.name_ar,
                                                        'name_en': role.name,
                                                        
                                                    } for role in security_group.pos_role_ids
                                                ]
                                        } for security_group in user_id.pos_security_group_ids
                                    ],                    
                    "available_pos": [
                                        {
                                        'id': pos.id,
                                        'name': pos.name,
                                        } for pos in user_id.available_pos_ids
                                    ],
                    # "access_token": access_token,
                    "login_time":str(time_now),
                            }
                    }
        return response

class AccessToken(http.Controller):
    @http.route("/api/login", methods=["POST"], type="json", auth="none", csrf=False)
    def api_login(self, **kw):
        # headers = request.httprequest.headers
        # db = headers.get("db")
        db = kw.get('database')
        # username = headers.get("login")
        username = kw.get('username')
        # password = headers.get("password")
        password = kw.get('password')
        _credentials_includes_in_headers = all([db, username, password])
        if not _credentials_includes_in_headers:
            # Response.status = "403"
            response = {
                        "message": "Either of the following are missing [db, username,password].."
                        }                                 
            return response
        try:
            # request.session.logout()#
            request.session.authenticate(db, username, password)
        except AccessError as aee:
            # Response.status = "401"
            response = {
                        "message": "Error: %s" % aee.name
                        }                     
            return response            
        except AccessDenied as ade:
            # Response.status = "401"
            response = {
                        "message": "Login, password or db invalid"
                        }                              
            return response             
        except Exception as e:
            # Response.status = "403"
            response = {
                        "message": "Wrong database name"
                        }             
            return response             
        uid = request.session.uid
        if not uid:
            # Response.status = "401"
            response = {
                        "message": "Authentication failed"
                        }                              
            return response             
        access_token_id = request.env["api.access_token"].find_or_create_token(user_id=uid, create=True)
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # Response.status = "200"
        response = {
                    "message": "Logged in successfully.",
                    'body': {         
                    "uid": uid,
                    "name": request.env.user.name,
                    "email": request.env.user.partner_id.email,
                    "mobile": request.env.user.partner_id.mobile,
                    "image_1920": base_url + '/web/image?' + 'model=res.partner&id=' + 
                        str(request.env.user.partner_id.id) + '&field=image_1920',
                    "access_token": access_token_id.token,
                    "token_expiry_date":access_token_id.token_expiry_date
                    # "user_context": request.session.get_context() if uid else {},
                    # "company_id": request.env.user.company_id.id if uid else None,
                    # "company_ids": request.env.user.company_ids.ids if uid else None,
                    # "partner_id": request.env.user.partner_id.id,
                    # "company_name": request.env.user.company_name,
                    # "country": request.env.user.country_id.name,
                    # "contact_address": request.env.user.contact_address,
                            }
                    }
        return response

    # @validate_token
    @http.route(['/api/logout'], type='http', auth="none", csrf=False)
    def api_logout(self):
        try:

            access_token1 = False
            if request.httprequest.headers.get("access_token",False):
                access_token1 = request.httprequest.headers.get("access_token") 
            if request.httprequest.headers.get("access-token",False):
                access_token1 = request.httprequest.headers.get("access-token") 

            access_token = request.env["api.access_token"].sudo().search([("token", "=", access_token1)], limit=1)
            if access_token:
                if access_token.is_valid():
                    access_token.token_expiry_date = datetime.now()
                    request.session.logout()
                    # Response.status = "200"
                    return valid_response("Logout Successfully.",)                                       
                else:
                    # Response.status = "403" 
                    return invalid_response("Invalid access token.",)              
            else:
                # Response.status = "403"
                return invalid_response("Invalid access token..",)                            
        except AccessError as aee:
            # Response.status = "403"
            response = {"code": "403", "message": "Error: %s" % aee.name,}
            return response 
