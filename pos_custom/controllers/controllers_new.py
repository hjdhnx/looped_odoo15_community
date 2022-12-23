# -*- coding: utf-8 -*-
from genericpath import exists
from odoo import http
from odoo.http import request, Response
import json
from odoo.exceptions import AccessError
from odoo.addons.web.controllers.main import Database
from odoo.addons.pos_custom.controllers.login import validate_token
from ast import literal_eval
from odoo.addons.auth_signup.models.res_partner import SignupError
from odoo.tools.misc import ustr
import odoorpc
import werkzeug.wrappers
import hashlib
import logging

import os
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


_logger = logging.getLogger(__name__)


class PosCustomNewAPI(http.Controller):

    @validate_token
    @http.route("/api/add_address", methods=["POST"], type="json", auth="none", csrf=False)
    def api_login(self, **kw):       
        title = kw.get('title')
        details = kw.get('details')
        latlong = kw.get('latlong')
        _required_values = all([title, details, latlong])
        if not _required_values:
            # Response.status = "403"
            response = {
                        "code": "403",
                        "message": "Either of the following are missing [Title, Details, Latlong].."
                        }                                 
            return response
        request_user_id = request.env['res.users'].browse(request.uid)
        other_address_obj = request.env['other.address']
        if request_user_id:  
            other_address_obj.create({  
                                    'partner_id': request_user_id.partner_id.id, 
                                    'title': title, 
                                    'details': details, 
                                    'latlong': latlong, 
                                    })
            # Response.status = "200"
            response = {
                        "code": "200",
                        "message": "User address added successfully",
                        }
            return response

    @validate_token
    @http.route(['/api/forget_password'], type='json', methods=['POST'], auth="none", csrf=False)
    def forget_password(self, new_password):
        user_id_obj = request.env['res.users'].browse(request.uid)
        if new_password:
            if user_id_obj:
                user_id_obj.sudo().write({'password': new_password,})   
                # Response.status = "200"
                response = {"code": "200", "message": "User Password Updated successfully!",}
                return response  
            else:
                # Response.status = "400"
                response = {"code": "400", "message": "Invalid User ID!",}
                return response 
        else:
            # Response.status = "401"
            response = {"code": "401", "message": "Required: New Password",}
            return response

    @validate_token
    @http.route('/pos_custom/insert_delivery_order', type='json', methods=['POST'], auth="none", csrf=False)
    def insert_delivery_order(self, **kw):
        """ API to insert order from Mobile App (delivery) to Odoo """
        order_obj = request.env['sale.order'].sudo()
        status = {}
        for order in kw.get('order'):
            partner_id = request.env['res.users'].sudo().search([('id', '=', order.get('user_id'))]).partner_id
            line_vals = []
            for line in order.get('lines'):
                product_id = request.env['product.product'].sudo().search([('id', '=', line.get('product_id'))])
                line_vals.append((0, 0, {'product_id': product_id.id, 
                                        'name': product_id.name, 
                                        'product_uom_qty': int(line.get('product_uom_qty', 0.0)), 
                                        'price_unit': int(line.get('price_unit', 0.0)), 
                                        }))
            order_created = order_obj.create({  'partner_id': partner_id.id, 
                                                'partner_invoice_id': partner_id.id, 
                                                'partner_shipping_id': partner_id.id, 
                                                'note': order.get('note'),
                                                'warehouse_id': int(order.get('warehouse_id')),
                                                'pricelist_id': int(order.get('pricelist_id')),
                                                'order_line': line_vals,
                                                })
            order_created.action_confirm()
            status.update({"order_created": order_created.id,}) 
        # Response.status = "200"
        response = {"code": "200", "message": "Order created successfully!", "status": status}
        return response

    @validate_token
    @http.route(['/pos_custom/get_all_delivery_category'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_delivery_category(self, **kw):
        """ API to return all delivery category data. """
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        public_category_obj = request.env['product.public.category'].sudo()
        public_category_records = public_category_obj.search([('id', 'not in', kw.get('delivery_category_ids'))])
        result = []
        for public_category in public_category_records:
            result += [{
                        'id': public_category.id,
                        'name': public_category.name,
                        'parent_id': public_category.parent_id.id,
                        'website_id': public_category.website_id.id,
                        'sequence': public_category.sequence,
                        'branch_id': public_category.branch_id.id,
                        'invisible_in_ui': public_category.invisible_in_ui,
                        'website_image_1920': base_url + '/web/image?' + 'model=product.public.category&id=' + str(
                            public_category.id) + '&field=image_1920',
                        'image_128':base_url + '/web/image?' + 'model=product.public.category&id=' + str(
                            public_category.id) + '&field=image_128',                            
                    }]
        # Response.status = "200"
        return result

    @http.route("/api/custom_signup", type='json', methods=['POST'], auth="none", csrf=False)
    def custom_signup(self, **kw):
        name = kw.get('name')
        password = kw.get("password")
        email = kw.get("email")
        mobile = kw.get("mobile")
        _credentials_includes_in_headers = all([name, password, email, mobile])
        if not _credentials_includes_in_headers:
            # Response.status = "403"
            result = {   
                            "code": "403",
                            "message": "Either of the following are missing [name, password, email, mobile]..",
                        }
            return result
        values = { key: kw.get(key) for key in ('name', 'password') }
        values['login'] = kw.get('login')
        values['email'] = email #or values.get('name')
        values['active'] = 1
        values['notification_type'] = 'email'
        values['company_id'] = 1
        values['company_ids'] = [1]
        values['branch_id'] = 1
        values['is_portal'] = 1

        url = "109.205.182.152" 
        port = 8001    
        username = 'deliveryapp' 
        password = 'deliveryapp'   
                   
        # url = "localhost"   
        # port = 8015   
        # username = 'mobileapp' 
        # password = 'mobileapp' 

        db = "combotech" 
        odoo = odoorpc.ODOO(url, port=port)
        odoo.login(db, username, password)
        user_obj = odoo.env['res.users']
        exist_user = user_obj.search([('login', '=', values.get('login'))], limit=1)
        if exist_user:
            odoo.logout()
            # for user in user_obj.browse(exist_user):            
            # 
                # token_expiry_date = datetime.now() + timedelta(days=1)
                # rbytes = os.urandom(40)
                # token = "{}_{}".format("access_token", str(hashlib.sha1(rbytes).hexdigest()))
                # vals = {
                #         "user_id": user.id,
                #         "scope": "userinfo",
                #         "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                #         "token": token,
                #         }
                # access_obj = odoo.env['api.access_token']
                # access_token = odoo.execute('api.access_token', 'create', [vals]) 
                # for token in access_obj.browse(access_token):  
                #     new_token = token.token        
            #             
            # Response.status = "401"
            result = {   
                            "code": "401",
                            "message": "User Already exist.",
                            # "user_id": user.id,
                            # "login": user.login,
                            # "name": user.name,
                            # "email": user.partner_id.email,
                            # "mobile": user.partner_id.mobile,
                            # "access_token": new_token,
                        }
            return result             
        # partner_obj = odoo.env['res.partner']
        # exist_mobile = partner_obj.search([('mobile', '=', kw.get("mobile"))], limit=1)
        # if mobile:
        #     # Response.status = "402"
        #     result = [
        #                 {   
        #                     "code": "402",
        #                     "message": "This mobile number already exists..",
        #                 }
        #             ] 
        #     return result                                              
        group_obj = odoo.env['res.groups']
        group_portal = group_obj.search([('name', '=', 'Portal')], limit=1)
        for group in group_obj.browse(group_portal):
            group_portal = group.id
        values['groups_id'] = [group_portal]
        group_public = group_obj.search([('name', '=', 'Internal User')], limit=1)
        for group in group_obj.browse(group_public):
            group_public = group.id                   
        try:
            user_id = odoo.execute('res.users', 'create', [values])   
            if user_id:  
                created_user = user_obj.search([('id', '=', user_id)], limit=1)   
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url') 
                for user in user_obj.browse(created_user):  
                    user.partner_id.write({'user_id': user_id, 
                                            'email': kw.get('email'), 
                                            'mobile': kw.get('mobile'), 
                                            })
                # 
                    token_expiry_date = datetime.now() + timedelta(days=365) + timedelta(hours=2)
                    rbytes = os.urandom(40)
                    token = "{}_{}".format("access_token", str(hashlib.sha1(rbytes).hexdigest()))
                    vals = {
                            "user_id": user.id,
                            "scope": "userinfo",
                            # "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            "token_expiry_date": token_expiry_date,
                            "token": token,
                            }
                    access_obj = odoo.env['api.access_token']
                    access_token = odoo.execute('api.access_token', 'create', [vals]) 
                    for token in access_obj.browse(access_token):  
                        new_token = token.token        
                #                                             
                    # Response.status = "200"
                    result = {   
                                    "code": "200",
                                    "message": "Sign-up Done Successfully.",
                                    "user_id": user.id,
                                    "login": user.login,
                                    "name": user.name,
                                    "email": user.partner_id.email,
                                    "mobile": user.partner_id.mobile,
                                    "image_1920": base_url + '/web/image?' + 'model=res.partner&id=' + 
                                        str(user.partner_id.id) + '&field=image_1920',                                    
                                    "access_token": new_token,
                                }
                    return result             
        except Exception as e:
        #     created_user = user_obj.search([('id', '=', user_id)], limit=1)    
        #     for user in user_obj.browse(created_user):  
        #         user.partner_id.unlink()         
        #         user.unlink() 
            # Response.status = "401"
            result = {   
                            "code": "401",
                            "message": ustr(e),
                        }
            return result

    @validate_token
    @http.route(['/pos_custom/update_pin'], type='json', methods=['POST'], auth="none", csrf=False)
    def update_pin(self, user_id, pin):
        if user_id and pin:
            user_id_obj = request.env['res.users'].sudo().search([('id', '=', user_id)])
            if user_id_obj:
                user_id_obj.write({'security_pin': pin,})
                # Response.status = "200"
                response = {"code": "200", "message": "User Pin Updated successfully!",}
                return response
            else:
                # Response.status = "400"
                response = {"code": "400", "message": "Invalid User ID!",}
                return response                 
        else:
            # Response.status = "401"
            response = {"code": "401", "message": "Required: User_ID , Pin Code",}
            return response        

    @validate_token
    @http.route(['/pos_custom/get_all_pos_promotion_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_pos_promotion_data_api(self, **kw):
        """  API to return all pos promotion data."""

        
        # pos_promotion_obj = request.env['pos.promotion'].sudo()
        # pos_promotion_records = pos_promotion_obj.search([('applied_app', '=', kw.get('applied_app')),('id', 'not in', kw.get('pos_promotion_ids'))])
        pos_id = kw.get('pos_id',False)
        if not pos_id:
            result = {  
                        "message":"POS ID not Provided",
                    }
            # Response.status = "401"
            return result

        check_pos_id = request.env['pos.config'].sudo().search([('id','=',pos_id)])
         
        if not check_pos_id:
            result = {  
                        "message":"POS ID not Found",
                    }
            # Response.status = "401"
            return result

        promotion_ids = check_pos_id.promotion_ids.ids

        pos_promotion_obj = request.env['pos.promotion'].sudo()
        pos_promotion_records = pos_promotion_obj.search([('id', 'in', promotion_ids)])
        
        result = []

        for pos_promotion in pos_promotion_records:
            special_time = []
            if pos_promotion.special_times:
                if pos_promotion.from_time:
                    special_time.append(str(  '{0:02.0f}:{1:02.0f}'.format(*divmod(pos_promotion.from_time * 60, 60))))
                
                if pos_promotion.from_time:
                    special_time.append(str(  '{0:02.0f}:{1:02.0f}'.format(*divmod(pos_promotion.to_time * 60, 60))))
            
            special_day = []
            if pos_promotion.special_days:
                if pos_promotion.monday:
                    special_day.append("monday")
                if pos_promotion.tuesday:
                    special_day.append("tuesday")
                if pos_promotion.wednesday:
                    special_day.append("wednesday")
                if pos_promotion.thursday:
                    special_day.append("thursday")
                if pos_promotion.friday:
                    special_day.append("friday")
                if pos_promotion.saturday:
                    special_day.append("saturday")
                if pos_promotion.sunday:
                    special_day.append("sunday")

            result += [{
                'id': pos_promotion.id,
                
                'name_en': pos_promotion.name,
                'name_ar': pos_promotion.name_ar,
                'active': pos_promotion.active,
                'start_date': pos_promotion.start_date,
                'end_date': pos_promotion.end_date,
                'amount_total': pos_promotion.amount_total,
                'type': pos_promotion.type,
                'method': pos_promotion.method,
                'discount_first_order': pos_promotion.discount_first_order,
                'product_id': pos_promotion.product_id.id,
                "discount_order_ids":
                    [
                        {
                            'id': discount_order.id,
                            'minimum_amount': discount_order.minimum_amount,
                            'discount': discount_order.discount,
                            'promotion_id': discount_order.promotion_id.id,
                        } for discount_order in pos_promotion.discount_order_ids
                    ],
                "discount_category_ids":
                    [
                        {
                            'id': discount_category.id,
                            'category_id': discount_category.category_id.id,
                            'discount': discount_category.discount,
                            'promotion_id': discount_category.promotion_id.id,
                        } for discount_category in pos_promotion.discount_category_ids
                    ],
                "discount_ecommerce_category_ids":
                    [
                        {
                            'id': discount_ecommerce_category.id,
                            'category_id': discount_ecommerce_category.category_id.id,
                            'discount': discount_ecommerce_category.discount,
                            'promotion_id': discount_ecommerce_category.promotion_id.id,
                        } for discount_ecommerce_category in pos_promotion.discount_ecommerce_category_ids
                    ],
                "discount_quantity_ids":
                    [
                        {
                            'id': discount_quantity.id,
                            'product_id': discount_quantity.product_id.id,
                            'quantity': discount_quantity.quantity,
                            'discount': discount_quantity.discount,
                            'promotion_id': discount_quantity.promotion_id.id,
                        } for discount_quantity in pos_promotion.discount_quantity_ids
                    ],
                "gift_condition_ids":
                    [
                        {
                            'id': gift_condition.id,
                            'product_id': gift_condition.product_id.id,
                            'minimum_quantity': gift_condition.minimum_quantity,
                            'promotion_id': gift_condition.promotion_id.id,
                        } for gift_condition in pos_promotion.gift_condition_ids
                    ],
                "gift_free_ids":
                    [
                        {
                            'id': gift_free.id,
                            'product_id': gift_free.product_id.id,
                            'quantity_free': gift_free.quantity_free,
                            'promotion_id': gift_free.promotion_id.id,
                            'type': gift_free.type,
                        } for gift_free in pos_promotion.gift_free_ids
                    ],
                "discount_condition_ids":
                    [
                        {
                            'id': discount_condition.id,
                            'product_id': discount_condition.product_id.id,
                            'minimum_quantity': discount_condition.minimum_quantity,
                            'promotion_id': discount_condition.promotion_id.id,
                        } for discount_condition in pos_promotion.discount_condition_ids
                    ],
                "discount_apply_ids":
                    [
                        {
                            'id': discount_apply.id,
                            'product_id': discount_apply.product_id.id,
                            'type': discount_apply.type,
                            'discount': discount_apply.discount,
                            'promotion_id': discount_apply.promotion_id.id,
                        } for discount_apply in pos_promotion.discount_apply_ids
                    ],
                "price_ids":
                    [
                        {
                            'id': price.id,
                            'product_id': price.product_id.id,
                            'minimum_quantity': price.minimum_quantity,
                            'price_down': price.price_down,
                            'promotion_id': price.promotion_id.id,
                        } for price in pos_promotion.price_ids
                    ],
                "special_category_ids":
                    [
                        {
                            'id': special_category.id,
                            # 'product_ids': [ product.id for product in special_category.product_ids ],
                            'product_id': special_category.product_id.id,
                            'category_id': special_category.category_id.id,
                            'type': special_category.type,
                            'promotion_id': special_category.promotion_id.id,
                            # 'list_price': special_category.list_price,
                            # 'qty_apply': special_category.qty_apply,
                            'count': special_category.count,
                            'discount': special_category.discount,
                            'qty_free': special_category.qty_free,
                        } for special_category in pos_promotion.special_category_ids
                    ],
                "discount_lowest_price": pos_promotion.discount_lowest_price,
                "multi_buy_ids":
                    [
                        {
                            'id': multi_buy.id,
                            'product_ids': [
                                product.id for product in multi_buy.product_ids
                            ],
                            'promotion_id': multi_buy.promotion_id.id,
                            'list_price': multi_buy.list_price,
                            'qty_apply': multi_buy.qty_apply,
                        } for multi_buy in pos_promotion.multi_buy_ids
                    ],
                "product_ids":
                    [
                        product.id for product in pos_promotion.product_ids
                    ],

                "minimum_items": pos_promotion.minimum_items,
                "special_customer_ids":
                    [
                        special_customer.id for special_customer in pos_promotion.special_customer_ids
                    ],
                "promotion_birthday": pos_promotion.promotion_birthday,
                "promotion_birthday_type": pos_promotion.promotion_birthday_type,
                "promotion_group": pos_promotion.promotion_group,
                "promotion_group_ids":
                    [
                        promotion_group.id for promotion_group in pos_promotion.promotion_group_ids
                    ],
                "state": pos_promotion.state,
                "special_days": pos_promotion.special_days,
                
                "special_times": pos_promotion.special_times,
                "special_times":special_time,
                "special_day":special_day,
                "from_time": pos_promotion.from_time,
                "to_time": pos_promotion.to_time,
                "branch_id": pos_promotion.branch_id.id,
                "applied_app": pos_promotion.applied_app,
            }]

        
        # Response.status = "200"
        data = {
                    'message': "Get All POS Promotion Successfully",
                    'body': result                    
                }     
        return data



    @validate_token
    @http.route(['/pos_custom/get_all_pos_promotion_image'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_pos_promotion_image(self, **kw):
        """  API to return all pos promotion data."""

        
        # pos_promotion_obj = request.env['pos.promotion'].sudo()
        # pos_promotion_records = pos_promotion_obj.search([('applied_app', '=', kw.get('applied_app')),('id', 'not in', kw.get('pos_promotion_ids'))])
        pos_id = kw.get('pos_id',False)
        if not pos_id:
            result = {  
                        "message":"POS ID not Provided",
                    }
            # Response.status = "401"
            return result

        check_pos_id = request.env['pos.config'].sudo().search([('id','=',pos_id)])
         
        if not check_pos_id:
            result = {  
                        "message":"POS ID not Found",
                    }
            # Response.status = "401"
            return result

        promotion_ids = check_pos_id.promotion_ids.ids

        pos_promotion_obj = request.env['pos.promotion'].sudo()
        pos_promotion_records = pos_promotion_obj.search([('id', 'in', promotion_ids)])
        
        result = []

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for pos_promotion in pos_promotion_records:
            for image in pos_promotion.promotion_image_ids:
            
                result += [{
                    'promotion_id': pos_promotion.id,
                    'promotion_image':base_url + '/web/image?' + 'model=product.image&id=' + str(
                                image.id) + '&field=image_1920',
                    'line_id': image.id,
                    
                    
                    
                }]

        
        # Response.status = "200"
        data = {
                    'message': "Get Promotion in Successfully",
                    'body': result                    
                }     
        return data


    @validate_token
    @http.route(['/pos_custom/get_pos_cds_product_image'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_pos_cds_product_image(self, **kw):
        """  API to return all pos promotion data."""

        
        pos_id = kw.get('pos_id',False)
        if not pos_id:
            result = {  
                        "message":"POS ID not Provided",
                    }
            # Response.status = "401"
            return result

        check_pos_id = request.env['pos.config'].sudo().search([('id','=',pos_id)])
         
        if not check_pos_id:
            result = {  
                        "message":"POS ID not Found",
                    }
            # Response.status = "401"
            return result

        
        
        result = []

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for product in check_pos_id.product_promotion_ids:
            
            result += [{
                    'product_id': product.id,
                    
                    "product_image":base_url + '/web/image?' + 'model=product.product&id=' + str(product.id) + '&field=image_1920',
                                
                    
                    
                    
                    
                }]

        
        # Response.status = "200"
        data = {
                    'message': "Get Product Images Successfully",
                    'body': result                    
                }     
        return data


    @validate_token
    @http.route(['/pos_custom/get_all_pos_security_role_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_pos_security_role_data_api(self, **kw):
        """ API to return all pos security role data. """
        pos_security_role_obj = request.env['pos.security.role'].sudo()
        role_ids = kw.get('role_ids',False)
        domain = []

        if role_ids:
            domain.append(('id','in',role_ids))
        
        pos_security_role_records = pos_security_role_obj.search(domain)
        data = []
        for pos_security_role in pos_security_role_records:
            data += [{
                'id': pos_security_role.id,
                'key': pos_security_role.key,
                'name_ar':pos_security_role.name_ar,
                'name_en': pos_security_role.name,
                # 'desc': pos_security_role.desc,
                
                # 'is_default_value': pos_security_role.is_default_value,
                # 'company_id': pos_security_role.company_id.id,

                    
            }]
        


        result = {
                        'message': "Get All Roles Successfully",
                        'body': data                        
                        }
        # Response.status = "200"
        return result


    @validate_token
    @http.route('/pos_custom/create_pos_security_role', type='json', methods=['POST'], auth="none", csrf=False)
    def create_printer(self,**kw):
        """ Create Pos Security Role"""
        #add use_type in create
        pos_security_role_obj = request.env['pos.security.role'].sudo()

        rules = kw.get('rules',False)
        if not rules:
            # Response.status = "403"
            result = {  
                        "message":"Rules Name not Provided",
                    }
            return result
        for rule in rules:
            pos_security_role_obj.create({'name':rule})
            
        
        # Response.status = "200"
        result = {  
                      "message": "All Rules Uploaded Successfully"

        

                        }
        return result


    @validate_token
    @http.route(['/pos_custom/get_all_pos_security_group_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_pos_security_group_data_api(self, **kw):
        """ API to return all pos security group data. """
        pos_security_group_obj = request.env['pos.security.group'].sudo()
        pos_security_group_records = pos_security_group_obj.search([('id', 'not in', kw.get('security_group_ids'))])
        result = []
        for pos_security_group in pos_security_group_records:
            result += [{
                        'id': pos_security_group.id,
                        'name': pos_security_group.name,
                        'arbic_name': pos_security_group.arbic_name,
                        "pos_role_ids":
                            [ pos_role.id for pos_role in pos_security_group.pos_role_ids ],
                        "pos_user_ids":
                            [ pos_user.id for pos_user in pos_security_group.pos_user_ids ],
                        'company_id': pos_security_group.company_id.id,
                    }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_pos_category_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_pos_category_data_api(self, **kw):
        """ API to return all pos category data. """
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        pos_category_obj = request.env['pos.category'].sudo()
        # pos_category_records = pos_category_obj.search([('id', 'not in', kw.get('pos_category_ids'))])
        domain = []

        domain.append(('invisible_in_ui','=',False))

        exclude_pos_id = kw.get('pos_id',False)

        if exclude_pos_id:
            domain.append(('exclude_pos_ids','not in',[exclude_pos_id,]))

        

        pos_category_records = pos_category_obj.search(domain)
        data = []
        for pos_category in pos_category_records:
            data += [{
                        'id': pos_category.id,
                        'name': pos_category.name,
                        'arbic_name': pos_category.arbic_name,
                        'image_128':base_url + '/web/image?' + 'model=pos.category&id=' + str(
                            pos_category.id) + '&field=image_128',
                        'parent_id': pos_category.parent_id.id,
                        'sequence': pos_category.sequence,
                        "exclude_pos_ids":
                            [
                                exclude_pos.id for exclude_pos in pos_category.exclude_pos_ids
                            ],
                        "restaurant_printer_ids":
                            [
                                restaurant_printer.id for restaurant_printer in pos_category.restaurant_printer_ids
                            ],
                        'invisible_in_ui': pos_category.invisible_in_ui,
                        'website_image_1920': base_url + '/web/image?' + 'model=pos.category&id=' + str(
                            pos_category.id) + '&field=image_1920',
                        'is_published': pos_category.is_published,
                    }]
        result = {
                        'message': "Get All POS Category Successful",
                        'body': data                        
                        }
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_restaurant_floor_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_restaurant_floor_data_api(self, **kw):
        """ API to return all restaurant floor data. """
        # base_url = request.env['ir.config_parameter'].get_param('web.base.url')

        pos_id = kw.get('pos_id',False)
        if not pos_id:
            # Response.status = "403"
            result = {  
                        "message":"POS ID not Provided",
                    }
            return result

        pos_config_obj = request.env['pos.config'].sudo()
        pos_config_record = pos_config_obj.search(
            [('id', '=', pos_id)])
        
        if not pos_config_record:
            result = {   
                        "message":"Sorry POS ID Not Found ",
                        }
            # Response.status = "401"
            return result

            
        restaurant_floor_obj = request.env['restaurant.floor'].sudo()
        restaurant_floor_records = restaurant_floor_obj.search([('id', 'in', pos_config_record.pos_floor_ids.ids)])
        result = {
                    'message': "Get Floors Successful",
                    'body': [
                            {
                                'id': restaurant_floor.id,
                                'name_ar': restaurant_floor.arbic_name,
                                'name_em': restaurant_floor.name,
                                'viewport_h': restaurant_floor.viewport_h,
                                'viewport_w': restaurant_floor.viewport_w,
                                "tables": [
                                    {
                                        'id': table.id,
                                        'name_ar': table.arbic_name,
                                        'name_en': table.name,
                                        'seats': table.seats,
                                        'locked': table.locked,
                                        'shape': table.shape,
                                        'position_h': table.position_h,
                                        'position_v': table.position_v,
                                        'width': table.width,
                                        'height': table.height,
                                    } for table in restaurant_floor.table_ids
                                ]

                            } for restaurant_floor in restaurant_floor_records
                    ],

                    # 'pos_config_id': restaurant_floor.pos_config_id.id,
                    # 'pricelist_id': restaurant_floor.pricelist_id.id,
                    # 'background_color': restaurant_floor.background_color,
                    # "table_ids":
                    #     [
                    #         {   
                    #             'barcode_url': table.barcode_url,
                    #             'qr_image': base_url + '/web/image?' + 'model=restaurant.table&id=' + str(
                    #                 table.id) + '&field=image_1920',
                    #             'pricelist_id': table.pricelist_id.id,
                    #             'user_ids':
                    #                 [ user.id for user in table.user_ids ],
                    #             'color': table.color,
                    #         } for table in restaurant_floor.table_ids
                    #     ],
        }
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_customer_by_mobile'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_customer_by_mobile(self, **kw):
        """ API to return customer data by mobile """
        customer_obj = request.env['res.partner'].sudo()
        mobile_or_name = kw.get('mobile_or_name',False)
        if not mobile_or_name:
            # Response.status = "401"
            response = {
                        "message": "Sorry , Please Provide name or mobile to search"
                        }                                 
            return response
        customer_records = customer_obj.search(['|',('mobile', 'ilike', mobile_or_name ),('name', 'ilike', mobile_or_name )],)
        if customer_records:
            result = {
                        'message': "Get customer data by mobile successful",
                        'body': [
                                    {
                                        'id': customer.id,
                                        'name': customer.name,
                                        # 'arbic_name': customer.arbic_name,
                                        'mobile': customer.mobile,
                                        'balance': customer.wallet_balance,
                                    } for customer in customer_records
                                ]
                        }
            # Response.status = "200"
        else:
            result = {
                        'message': "No data found.",
                        'body': []                        
                        }
            # Response.status = "200"            
        return result


    @validate_token
    @http.route(['/pos_custom/login_customer_by_mobile'], type='json', methods=['POST'], auth="none", csrf=False)
    def login_customer_by_mobile(self, **kw):
        """ API to return customer data by mobile """
        customer_obj = request.env['res.partner'].sudo()
        mobile_number = kw.get('mobile_number',False)
        if not mobile_number:
            # Response.status = "401"
            response = {
                        "message": "Sorry , Please Provide Mobile Number to search"
                        }                                 
            return response
        customer_records = customer_obj.search([('mobile', '=', mobile_number )],)
        if customer_records:
            result = {
                        'message': "Get customer data successful",
                        'body': [
                                    {
                                        'id': customer.id,
                                        'name': customer.name,
                                        'mobile': customer.mobile,
                                        'wallet_balance': customer.wallet_balance,
                                    } for customer in customer_records
                                ]
                        }
            # Response.status = "200"
        else:
            result = {
                        'message': "No data found.",
                        'body': []                        
                        }
            # Response.status = "200"            
        return result


    @validate_token
    @http.route(['/pos_custom/check_customer_mobile'], type='json', methods=['POST'], auth="none", csrf=False)
    def check_customer_mobile(self, **kw):
        customer_obj = request.env['res.partner'].sudo()
        mobile = kw.get('mobile_number',False)
        if not mobile:
            # Response.status = "401"
            response = {
                        "message": "Sorry , Please Provide Mobile Number to search"
                        }                                 
            return response
        customer_records = customer_obj.search([('mobile', '=', mobile )],)
        message =  "No data found."
        is_found = False

        if customer_records:
            message =  "data found successfully."
            is_found = True
        
        result = {

                    'message': message,
                    'body': {
                    'find_number': is_found,
                    }
                  
                                            
                    }
        # Response.status = "200"            
        return result


    @validate_token
    @http.route(['/pos_custom/get_all_customers'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_customers(self, **kw):
        """ API to return all customer data. """
        # base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        customer_obj = request.env['res.partner'].sudo()
        customer_records = customer_obj.search([('customer_rank', '>=', 1)])
        result = {
                    'message': "Get all customers successful",
                    'body': [
                            {
                                'id': customer.id,
                                'name': customer.name,
                                # 'arbic_name': customer.arbic_name,
                                'mobile': customer.mobile,
                                'balance': customer.wallet_balance,
                                # 'image_1920': base_url + '/web/image?' + 'model=res.partner&id=' + str(
                                #     customer.id) + '&field=image_1920',
                                # 'street': customer.street,
                                # 'street2': customer.street2,
                                # 'city': customer.city,
                                # 'state_id': customer.state_id.id,
                                # 'zip': customer.zip,
                                # 'country_id': customer.country_id.id,
                                # 'vat': customer.vat,
                                # 'branch_id': customer.branch_id.id,
                                # 'phone': customer.phone,                                    
                                # 'email': customer.email,
                                # 'website': customer.website,
                                # "category_id":
                                #     [ category.id for category in customer.category_id ],
                                # 'company_id': customer.company_id.id,
                                # 'pos_total_amount': customer.pos_total_amount,
                            } for customer in customer_records
                            ]
                    }
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_product_category_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_product_category_data_api(self, **kw):
        """ API to return all product category data. """
        product_category_obj = request.env['product.category'].sudo()
        product_category_records = product_category_obj.search([('id', 'not in', kw.get('product_category_ids'))])
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        result = {
                    'message': "Get all product category Successfully",
                    'body':
                            [
                                {
                                    'id': product_category.id,
                                    'name': product_category.name,
                                    'arabic_name': product_category.arabic_name,
                                    'image_128':base_url + '/web/image?' + 'model=product.category&id=' + str(
                                        product_category.id) + '&field=image_128',                                    
                                    # 'parent_id': product_category.parent_id.id,
                                    # 'removal_strategy_id': product_category.removal_strategy_id.id,
                                    # 'property_cost_method': product_category.property_cost_method,
                                    # 'property_valuation': product_category.property_valuation,
                                    # 'property_account_creditor_price_difference_categ': product_category.property_account_creditor_price_difference_categ.id,
                                    # 'property_account_expense_categ_id': product_category.property_account_expense_categ_id.id,
                                    # 'property_account_income_categ_id': product_category.property_account_income_categ_id.id,
                                    # 'property_stock_account_input_categ_id': product_category.property_stock_account_input_categ_id.id,
                                    # 'property_stock_account_output_categ_id': product_category.property_stock_account_output_categ_id.id,
                                    # 'property_stock_valuation_account_id': product_category.property_stock_valuation_account_id.id,
                                } for product_category in product_category_records
                            ],                     
                }                     
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_product_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_product_data_api(self, **kw):
        """ API to return all product data. """
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        product_type = []
        product_type = ['normal','has_addons']
        product_obj = request.env['product.product'].sudo()
        product_records = product_obj.search([
            # ('id', 'not in', kw.get('product_ids'))
            ('product_type','in',product_type),
             ('available_in_pos','=',True),
            ])
        result = {
                    'message': "Get products Successful",
                    'body':
                            [
                                {
                                'id': product.id,
                                "image_url":base_url + '/web/image?' + 'model=product.product&id=' + str(product.id) + '&field=image_1920',
                                "company_id":product.company_id.id,
                                "company_name":product.company_id.name,
                                # 'name_ar': product.name_ar,
                                'name_ar': product.other_lang_name,
                                # 'name_en': product.with_context(hierarchical_naming=True).display_name,
                                'name_en': product.name,
                                'sale_ok': product.sale_ok,
                                'purchase_ok': product.purchase_ok,
                                'tax_id':product.taxes_id.ids,
                                "product_template_id":product.product_tmpl_id.id,
                                "price_of_one":product.list_price,
                                'price_list': [
                                            {   
                                                'id': pricelist_item.pricelist_id.id, 
                                                'name_ar': pricelist_item.pricelist_id.arbic_name, 
                                                'name_en': pricelist_item.pricelist_id.name, 
                                                'price': pricelist_item.fixed_price, 
                                            } for pricelist_item in product.pricelist_item_ids],                                
                                'categ_id': product.pos_categ_id.id,
                                'type': product.product_type,   
                                "notes":[{
                                    'id': note.id,
                                    'name_en': note.name,
                                    'name_ar': note.arbic_name,
                                    
                                } for note in product.pos_categ_id.product_note_ids ],                                                                          
                                'extra': [
                                            {   
                                                'id': extra_product.id, 
                                                'category_id': extra_product.pos_categ_id.id, 
                                                'name_ar': extra_product.name_ar, 
                                                'name_en': extra_product.name, 
                                                'price': extra_product.list_price, 
                                                'tax_ids':extra_product.taxes_id.ids,
                                            } for extra_product in product.extra_products],
                                'combo_items': [
                                            {   
                                                'title_id': combo.title_id.id, 
                                                'name_en': combo.title_id.name,
                                                'name_ar': combo.title_id.arabic_name,
                                                'product_ids': [
                                                                    {
                                                                        'product_id': product.id, 
                                                                        'name_en': product.name,
                                                                        'name_ar': product.other_lang_name,
                                                                        'extra_price': product.list_price, 
                                                                    } for product in combo.product_ids
                                                                ] ,
                                                'min_qty': combo.min_qty, 
                                                'max_qty': combo.max_qty, 
                                            } for combo in product.product_combo_ids], 
                                # 'variants': [
                                #             {   
                                #                 'id': variant.id, 
                                #                 'name_en': variant.name, 
                                #                 'name_ar': variant.arabic_name, 
                                #                 'price': variant.price_extra, 
                                #                 "image_url":base_url + '/web/image?' + 'model=product.product&id=' + str(product.id) + '&field=image_1920',
                                #             } for variant in product.product_template_value_ids],                                            

            
                                } for product in product_records
                            ],                     
                }                    
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_product_template_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_product_template_data_api(self, **kw):
        """ API to return all product data. """
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        product_type = ['normal','has_addons']
        product_obj = request.env['product.template'].sudo()
        product_product_obj = request.env['product.product'].sudo()



        domain = [('available_in_pos','=',True),('invisible_in_ui','=',False)]
        

        if product_type:
            domain.append(('product_type','in',product_type))

        

        exclude_pos_id = kw.get('exclude_pos_id',False)

        if exclude_pos_id:
            domain.append(('exclude_template_config_ids','not in',[exclude_pos_id,]))


        product_records = product_obj.search(domain)
        result = {
                    'message': "Get products Successful",
                    'body':
                            [
                                {
                                'id': product.id,
                                "image_url":base_url + '/web/image?' + 'model=product.template&id=' + str(product.id) + '&field=image_1920&last_image_edit='+str(product.image_edit_date).replace(" ",""),
                                "company_id":product.company_id.id,
                                "company_name":product.company_id.name,
                                # 'name_ar': product.name_ar,
                                'name_ar': product.other_lang_name,
                                # 'name_en': product.with_context(hierarchical_naming=True).display_name,
                                'name_en': product.name,
                                'sale_ok': product.sale_ok,
                                'purchase_ok': product.purchase_ok,
                                'tax_id':product.taxes_id.ids,
                                "price_of_one":product.list_price,
                                "prepare_time":product.preparation_time,
                                'price_list': [
                                            {   
                                                'id': pricelist_item.pricelist_id.id, 
                                                'name_ar': pricelist_item.pricelist_id.arbic_name, 
                                                'name_en': pricelist_item.pricelist_id.name, 
                                                'price': pricelist_item.fixed_price, 
                                            } for pricelist_item in product.pricelist_item_ids],                                
                                'categ_id': product.pos_categ_id.id,
                                'type': product.product_type,   
                                "notes":[{
                                    'id': note.id,
                                    'name_en': note.name,
                                    'name_ar': note.arbic_name,
                                    
                                } for note in product.pos_categ_id.product_note_ids ],                                                                          
                                'extra': [
                                            {   
                                                'id': extra_product.id, 
                                                'category_id': extra_product.pos_categ_id.id, 
                                                'name_ar': extra_product.name_ar, 
                                                'name_en': extra_product.name, 
                                                'price': extra_product.list_price, 
                                                'tax_ids':extra_product.taxes_id.ids,
                                            } for extra_product in product.extra_products],
                                'combo_items': [
                                            {   
                                                'title_id': combo.title_id.id, 
                                                'name_en': combo.title_id.name,
                                                'name_ar': combo.title_id.arabic_name,
                                                'product_ids': [
                                                                    {
                                                                        'product_id': product.id, 
                                                                        'name_en': product.name,
                                                                        'name_ar': product.other_lang_name,
                                                                        'extra_price': product.list_price, 
                                                                    } for product in combo.product_ids
                                                                ] ,
                                                'min_qty': combo.min_qty, 
                                                'max_qty': combo.max_qty, 
                                            } for combo in product.product_combo_ids], 
                                'variant_id':product_product_obj.search([('product_tmpl_id','=',product.id)]).id if len(product.product_variant_ids) <= 1 else False,
                                'variants': [
                                            {   
                                                'id': variant.id, 
                                                'name_en': variant.display_name, #display name insted of real name to get full name of variant encluding attributes
                                                'name_ar': variant.other_lang_name, 
                                                'price': variant.lst_price, 
                                                "image_url":base_url + '/web/image?' + 'model=product.product&id=' + str(variant.id) + '&field=image_1920&last_image_edit='+str(variant.image_edit_date).replace(" ",""),
                                            } for variant in product.product_variant_ids] if len(product.product_variant_ids) > 1 and product.available_in_pos else [],    

                                # 'variants': [
                                #             {   
                                #                 'id': variant.id, 
                                #                 'name_en': variant.name, 
                                #                 'name_ar': variant.arabic_name, 
                                #                 'price': variant.price_extra, 
                                #                 "image_url":base_url + '/web/image?' + 'model=product.product&id=' + str(product.id) + '&field=image_1920',
                                #             } for variant in product.product_template_value_ids],                                           

            
                                } for product in product_records
                            ],                     
                }                    
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_restaurant_printer_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_restaurant_printer_data_api(self, **kw):
        """ API to return all restaurant printer data. """
        restaurant_printer_obj = request.env['restaurant.printer'].sudo()
        restaurant_printer_records = restaurant_printer_obj.search([('id', 'not in', kw.get('restaurant_printer_ids'))])
        result = []
        for restaurant_printer in restaurant_printer_records:
            result += [{
                'id': restaurant_printer.id,
                'name': restaurant_printer.name,
                'printer_type': restaurant_printer.printer_type,
                'proxy_ip': restaurant_printer.proxy_ip,
                'use_type': restaurant_printer.use_type,
                'default_printer': restaurant_printer.default_printer,
                'epson_printer_ip': restaurant_printer.epson_printer_ip,
                'pos_order_type_ids':
                    [
                        pos_order_type.id for pos_order_type in restaurant_printer.pos_order_type_ids
                    ],
                'pos_config_ids':
                    [
                        pos_config.id for pos_config in restaurant_printer.pos_config_ids
                    ],
                'product_categories_ids':
                    [
                        product_categories.id for product_categories in restaurant_printer.product_categories_ids
                    ],
            }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_pos_multi_session_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_pos_multi_session_data_api(self, **kw):
        """ API to return all pos multi session data. """
        pos_multi_session_obj = request.env['pos.multi_session'].sudo()
        pos_multi_session_records = pos_multi_session_obj.search([('id', 'in', kw.get('multi_session_id'))])
        multi_session_list = []
        for pos_multi_session in pos_multi_session_records:
            multi_session_list.append({
                                        'id': pos_multi_session.id,
                                        'name': pos_multi_session.name,
                                        'pos_ids':
                                            [
                                                {
                                                'id':  pos.id,
                                                'name':  pos.name,
                                                } for pos in pos_multi_session.pos_ids
                                            ]
                                            ,
                                        'floor_ids':
                                            [
                                                {
                                                    'id': floor.id,
                                                    'name': floor.name,
                                                    'name_ar': floor.arbic_name,
                                                } for floor in pos_multi_session.floor_ids
                                            ],
                                        'table_blocking': pos_multi_session.table_blocking,
                                        'multi_session_active': pos_multi_session.multi_session_active,
                                        'sync_server': pos_multi_session.sync_server,
                                        'company_id': { 
                                                        'id': pos_multi_session.company_id.id,
                                                        'name': pos_multi_session.company_id.name,
                                                    },
                                    })
        # Response.status = "200"
        result = {  
                    "message": "Get Multiple Session Successfully.",
                    "body" : multi_session_list
                    }        
        return result

