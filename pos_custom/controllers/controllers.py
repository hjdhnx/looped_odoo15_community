# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json
from odoo.exceptions import AccessError
from odoo.addons.web.controllers.main import Database
from odoo.addons.pos_custom.controllers.login import validate_token
from odoo.addons.pos_custom.controllers.common import invalid_response, valid_response
from odoo import fields
from datetime import datetime, timedelta
import hashlib
import logging
import os
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib



_logger = logging.getLogger(__name__)

def execute(connector, method, *args):
    res = False
    try:
        res = getattr(connector, method)(*args)
    except socket.error as error:
        _logger.critical('Error while executing the method "execute". Error: ' + str(error))
        raise error
    return res

class posCustomAPI(http.Controller):

    @validate_token
    @http.route('/pos_custom/get_updated_orders',type='json', methods=['POST'], auth="none", csrf=False)
    def get_updated_orders(self, **kw):
        """ get pos updated orders """
        tracking_orders_obj = request.env['tracking.orders'].sudo()
        tracking_orders_record = tracking_orders_obj.search([('user_id', '=', request.uid)])
        data = []
        for tracking_order in tracking_orders_record:
            data += [{
                        'id': tracking_order.id,
                        'order_id': tracking_order.order_id.id,
                        'session_id': tracking_order.session_id.id,
                        'pos_id': tracking_order.pos_config_id.id,
                        'updated_on': tracking_order.write_date,
                        'updated_by': tracking_order.write_uid.id,
                    }]
        # Response.status = "200"
        result = {
                    'message': "Get All Updated Orders Successfully",
                    'body': data                    
                }     
        return result

    @validate_token
    @http.route('/pos_custom/create_draft_order', type='json', methods=['POST'], auth="none", csrf=False)
    def create_draft_order(self, **kw):
        """ API to create draft order from Mobile App to Odoo """
        order_obj = request.env['pos.order'].sudo()
        product_obj = request.env['product.product'].sudo()
        payment_obj = request.env['pos.payment'].sudo()
        
        order = kw.get('configuration')
        # for order in kw.get('configuration'):
        session = request.env['pos.session'].sudo().search([('id', '=', order.get('session_id')), ('state', '=', 'opened')])
        if not session:
            result = { 
                        "message":"Invalid session.", 
                        }
            # Response.status = "403"
            return result


        if not order.get('pos_id',False):
            result = {  
                        "message":"POS ID not Provided",
                    }
            # Response.status = "401"
            return result   
   
        pos_check = request.env['pos.config'].sudo().search([('id', '=', order.get('pos_id'))])
        if not pos_check:
            result = { 
                        "message":"Invalid POS Not Found.", 
                        }
            # Response.status = "403"  
            return result

        if not order.get('pricelist_id',False):
            result = {  
                        "message":"Pricelist ID not Provided",
                    }
            # Response.status = "401"
            return result   
   
        pricelist_check = request.env['product.pricelist'].sudo().search([('id', '=', order.get('pricelist_id'))])
        if not pricelist_check:
            result = { 
                        "message":"Invalid Pricelist Not Found.", 
                        }
            # Response.status = "403"  
            return result
        
        if not order.get('user_id',False):
            result = {  
                        "message":"User ID not Provided",
                    }
            # Response.status = "401"
            return result  

        
        if not order.get('order_type_id',False):
            result = {  
                        "message":"Order Type ID not Provided",
                    }
            # Response.status = "401"
            return result  
        
        order_type_check = request.env['pos.order_type'].sudo().search([('id', '=', order.get('order_type_id'))])

        if not order_type_check:
            result = {  
                        "message":"Order Type ID not Found",
                    }
            # Response.status = "401"
            return result 

        
        # if not order.get('discount_type_id',False):
        #     result = {  
        #                 "message":"Discount Type ID not Provided",
        #             }
        #     # Response.status = "401"
        #     return result  

        # discount_program_check = request.env['pos.discount_program'].sudo().search([('id', '=', order.get('discount_type_id'))])
        
        # if not discount_program_check:
        #     result = {  
        #                 "message":"Discount Type not Found",
        #             }
        #     # Response.status = "401"
        #     return result 
            

        
        combo_title_obj = request.env['combo.title'].sudo()
        
        line_vals = []
        payment_ids = []
        for line in kw.get('items'):
            product = product_obj.search([('id', '=', line.get('product_id'))])
            if not product:
                result = { 
                            "message":"Product ID not found.", 
                            }
                # Response.status = "403"
                return result    
            account_tax_ids = request.env['account.tax'].sudo().search([('id','in',line.get('tax_ids'))]) 
            
            extra_line_vals = []
            for extra_line in line.get('extras',[]):
                
                extra_line_vals.append(
                    (0,0,{
                            "main_product_id": product.id,
                            "product_id": extra_line.get('product_id'),
                            "name_ar": extra_line.get('name_ar'),
                            "name_en": extra_line.get('name_en'),
                            "quantity": extra_line.get('qty',0),
                            "price": extra_line.get('unit_price'),
                            "subtotal": extra_line.get('subtotal'),
                            "total_price": extra_line.get('total'),
                            "tax_ids":extra_line.get('tax_ids'),
                            
                            

                    })
                )

            
            addons_line_vals = []
            for addons_line in line.get('addons',[]):
                # product_line_vals = []
                # for product_line in addons_line.get('product_ids',[]):
                #     product_line_vals.append(  (0,0,{
                #          'product_id':product_line.get('product_id') ,
                #          'qty':product_line.get('qty',1) ,
                #         #  'extra_price':product_line.get('extra_price',0) ,
                            
                            
                #            })   )
                
                
                # title_record_id =  combo_title_obj.search(
                #     [('id','=',addons_line.get('title_id',False) )]   )
                # if not title_record_id:
                    
                #     result = { 
                #             "message":"Sorry , Tilte ID Provide With Addons not Found.", 
                #             }
                #     # Response.status = "403"
                #     return result    
                
                addons_line_vals.append(
                    (0,0,{
                            "main_product_id": product.id,
                            'product_id':addons_line.get('product_id') ,
                            'qty':addons_line.get('qty',1) ,
                        #   "title_id": addons_line.get('title_id'),
                        #   "line_addons_ids":product_line_vals,

                    })
                )
            

                
            
            line_vals.append((0, 0, {
                                    # 'name': product.name, 
                                    'full_product_name': product.display_name, 
                                    'product_id': product.id, 
                                    'name_ar': line.get('name_ar'),
                                    'name_en': line.get('name_en'),
                                    'qty': line.get('qty'),
                                    'main_product_id': line.get('main_product_id'),
                                    'price_unit': line.get('unit_price'),
                                    'tax_ids_after_fiscal_position': account_tax_ids.ids,
                                    'price_subtotal': line.get('subtotal'),
                                    'price_subtotal_incl': line.get('total'),
                                    'customer_note': line.get('customer_note',False),
                                    'custom_note': line.get('custom-note',False),
                                    # 'product_line_ids':product_line_vals,
                                    'product_note_ids':line.get('note_ids',[]),
                                    'product_extra_ids':extra_line_vals,
                                    'product_addons_ids':addons_line_vals,
                                    'is_show':line.get('is_show',False),
                                    'status':line.get('status',False),
                                    'is_send_to_kitchen':line.get('is_send_to_kitchen',False),
                                    'item_kitchen_state':line.get('item_kitchen_state',False),
                                    
                                    }
                                ))
            # print(">>>>>>>>>line_vals ",line_vals)
        # 1/0     
        order_pricing = kw.get('pricing')      
        payment_method_obj = request.env['pos.payment.method'].sudo()                
        for payment in order_pricing.get('payments'):
            payment_method_exist = payment_method_obj.search([('id', '=', payment.get('payment_method_id'))])
            if not payment_method_exist:
                result = { 
                            "message":"Payment Method ID not found.", 
                            }
                # Response.status = "403"
                return result                                        
            payment_ids.append((0, 0, {
                                        'payment_method_id': payment_method_exist.id, 
                                        'amount': payment.get('amount'),
                                        # 'branch_id': payment.get('branch_id'),
                                        'payment_time':payment.get('payment_time',False)
                                        }
                                ))   
        
        
        order_created = order_obj.create({    
                                    # 'name': session.config_id.name + '/' + session.name, 
                                    'session_id':order.get('session_id'), 
                                    'is_order_updated':order.get('is_order_updated',False),
                                    'date_order': order.get('order_date',False), 
                                    'user_id': order.get('user_id'), 
                                    'notes': order.get('notes'), 
                                    'order_type_id': order.get('order_type_id'),
                                    'discount_type_id': order.get('discount_type_id',False),
                                    
                                    "coupon_id": order.get('coupon_id'),
                                    'qr_code': order.get('qr_code'),
                                    'pricelist_id': order.get('pricelist_id'), 
                                    'partner_id': order.get('customer_id'), 
                                    'table_id': order.get('table_id'), 
                                    'note': order.get('note'),
                                    
                                    
                                    "amount_subtotal": order_pricing.get('amount_subtotal',0),
                                    "amount_promotion": order_pricing.get('amount_promotion',0),
                                    "amount_coupon": order_pricing.get('amount_coupon',0),
                                    "amount_discount": order_pricing.get('amount_discount',0),
                                    "amount_wallet": order_pricing.get('amount_wallet',0),
                                    # "amount_discount_total": order_pricing.get('amount_discount_total',0),
                                    # "amount_subtotal_discounted": order_pricing.get('amount_subtotal_discounted',0),
                                    "amount_tax": order_pricing.get('amount_tax',0),
                                    "amount_total": order_pricing.get('amount_total',0),
                                    "amount_paid": order_pricing.get('amount_total',0),
                                    "amount_return": order_pricing.get('amount_return',0),
                                    "return_to_wallet": order.get('return_to_wallet',False),

                                    # "amount_paid": order_pricing.get('amount_paid',0),
                                    # "amount_return": order_pricing.get('amount_return',0),


                                    
                                    'branch_id': order.get('branch_id'),
                                    'customer_count': 1,
                                    'd_o_number': order.get('d_o_number'),
                                        
                                    # 'coupon_id': order.get('coupon_id'),
                                    'return_reason_id': order.get('return_reason_id'),
                                    'return_order_id' : order.get('return_order_id'),
                                    # 'pos_reference': order.get('pos_reference'),
                                    # 'mobile_ref': order.get('mobile_ref'),
                                    'payment_ids': payment_ids,
                                    'lines': line_vals,
                                    'note' : kw.get('note',False),
                                    'state':order.get('status','draft'),
                                    'order_kitchen_state':order.get('order_kitchen_state',False),
                                        
                                        })
    
        
        response = {  
                        "message": "Order is drafted successfully.", 
                        "body" : {
                        "Order_id": order_created.id,
                        "order_no": order_created.pos_reference_custom,
                        }
                    } 
        # Response.status = "200"
        return response

    @validate_token
    @http.route('/pos_custom/create_order_return', type='json', methods=['POST'], auth="none", csrf=False)
    def create_order_return(self, **kw):
        """ API to create return order """
        order_obj = request.env['pos.order'].sudo()
        order_id = kw.get('order_id',False)
        product_items = kw.get('product_item',False)
        if not order_id:
            result = {  
                        "message":"Order ID not Provided",
                    }
            # Response.status = "401"
            return result   
   
        order_id = request.env['pos.order'].sudo().search([('id', '=', order_id)])
        if not order_id:
            result = { 
                        "message":"Invalid Order ID Not Found.", 
                        }
            # Response.status = "403"  
            return result
        
        if not product_items:
            result = {  
                        "message":"Product Items IDs not Provided",
                    }
            # Response.status = "401"
            return result  
        

        product_obj = request.env['product.product'].sudo()
        
        
        order = kw.get('configuration')
        # for order in kw.get('configuration'):
        
        

        
        line_vals = []
        amount_total = 0
        for line in product_items:
            product = product_obj.search([('id', '=', line.get('id'))])
            if not product:
                result = { 
                            "message":"Product ID not found.", 
                            }
                # Response.status = "403"
                return result    
            # account_tax_ids = request.env['account.tax'].sudo().search([('id','in',line.get('tax_ids_after_physical_position'))]) 
            qty =  line.get('qty')
            price_unit = line.get('price_unit') * -1
            price_subtotal = qty * price_unit
            amount_total = amount_total + price_subtotal
            line_vals.append((0, 0, {
                                    # 'name': product.name, 
                                    'full_product_name': product.name, 
                                    'product_id': product.id, 
                                    'qty': qty,
                                    'price_unit': price_unit,
                                    # 'tax_ids_after_fiscal_position': account_tax_ids.ids,
                                    'price_subtotal': price_subtotal,
                                    'price_subtotal_incl': price_subtotal,
                                    # 'customer_note': line.get('customer_note'),
                                    # 'product_line_ids':product_line_vals,
                                    
                                    }
                                ))
        
        order_created = order_obj.create(
            {  
                # 'name': session.config_id.name + '/' + session.name, 
                'session_id': order_id.session_id.id, 
                'user_id': order_id.user_id.id, 
                'order_type_id': order_id.order_type_id.id,
                # 'qr_code': order.get('qr_code'),
                'pricelist_id': order_id.pricelist_id.id, 
                'partner_id': order_id.partner_id.id, 
                'table_id': order_id.table_id.id, 
                # 'note': order.get('note'),
                'amount_total': amount_total, 
                'amount_tax': 0, 
                'amount_paid': 0,
                'amount_return': 0,                                            
                'branch_id': order_id.branch_id.id,
                'customer_count': 1,
                # 'd_o_number': order.get('d_o_number'),
                # 'discount_type_id': order.get('discount_type_id'),
                    
                # 'coupon_id': order.get('coupon_id'),
                'return_reason_id': order.get('return_reason_id'),
                'return_order_id' : order.get('return_order_id'),
                # 'pos_reference': order.get('pos_reference'),
                # 'mobile_ref': order.get('mobile_ref'),
                # 'payment_ids': payment_ids,
                'lines': line_vals,
                # 'note':kw.get('note',False),
                    })

        response = {  
                        "message": "Order is Return successfully.", 
                        "body" : {
                        "order_id": order_created.id
                        }
                    } 
        # Response.status = "200"
        return response

    @validate_token
    @http.route('/pos_custom/update_order', type='json', methods=['POST'], auth="none", csrf=False)
    def update_order(self, **kw):
        """ API to create draft order from Mobile App to Odoo """
        order_obj = request.env['pos.order'].sudo()
        product_obj = request.env['product.product'].sudo()
        payment_obj = request.env['pos.payment'].sudo()
        
        order = kw.get('configuration')
        
        if not order.get('order_id',False):
            result = {  
                        "message":"Order ID not Provided",
                    }
            # Response.status = "401"
            return result  

        order_id = order_obj.search([('id','=',order.get('order_id',False))])
        
        if not order_id:
            result = { 
                        "message":"Invalid Order ID Not Found.", 
                        }
            # Response.status = "403"  
            return result
            

        if not order.get('pricelist_id',False):
            result = {  
                        "message":"Pricelist ID not Provided",
                    }
            # Response.status = "401"
            return result   
   
        pricelist_check = request.env['product.pricelist'].sudo().search([('id', '=', order.get('pricelist_id'))])
        if not pricelist_check:
            result = { 
                        "message":"Invalid Pricelist Not Found.", 
                        }
            # Response.status = "403"  
            return result
        
        if not order.get('user_id',False):
            result = {  
                        "message":"User ID not Provided",
                    }
            # Response.status = "401"
            return result  

        
        if not order.get('order_type_id',False):
            result = {  
                        "message":"Order Type ID not Provided",
                    }
            # Response.status = "401"
            return result  

        order_type_check = request.env['pos.order_type'].sudo().search([('id', '=', order.get('order_type_id'))])
        
        if not order_type_check:
            result = {  
                        "message":"Order Type ID not Found",
                    }
            # Response.status = "401"
            return result 

        
        # if not order.get('discount_type_id',False):
        #     result = {  
        #                 "message":"Discount Type ID not Provided",
        #             }
        #     # Response.status = "401"
        #     return result  

        # discount_program_check = request.env['pos.discount_program'].sudo().search([('id', '=', order.get('discount_type_id'))])
        
        # if not discount_program_check:
        #     result = {  
        #                 "message":"Discount Type not Found",
        #             }
        #     # Response.status = "401"
        #     return result 

        exist_id = order_obj.search([('id', '=', order.get('order_id'))])
        combo_title_obj = request.env['combo.title'].sudo()
        if exist_id:
            line_vals = []
            payment_ids = []
            for line in kw.get('items'):
                product = product_obj.search([('id', '=', line.get('product_id'))])
                if not product:
                    result = { 
                                "message":"Product ID not found.", 
                                }
                    # Response.status = "403"
                    return result    
                account_tax_ids = request.env['account.tax'].sudo().search([('id','in',line.get('tax_ids'))]) 
                
                extra_line_vals = []
                for extra_line in line.get('extras',[]):
                    
                    extra_line_vals.append(
                        (0,0,{
                              "main_product_id": product.id,
                                "product_id": extra_line.get('product_id'),
                                "name_ar": extra_line.get('name_ar'),
                                "name_en": extra_line.get('name_en'),
                                "quantity": extra_line.get('qty',0),
                                "price": extra_line.get('unit_price'),
                                "subtotal": extra_line.get('subtotal'),
                                "total_price": extra_line.get('total'),
                                "tax_ids":extra_line.get('tax_ids'),
                                
                                

                        })
                    )

                
                addons_line_vals = []
                for addons_line in line.get('addons',[]):
                    # product_line_vals = []
                    # for product_line in addons_line.get('product_ids',[]):
                    #     product_line_vals.append(  (0,0,{
                    #          'product_id':product_line.get('product_id') ,
                    #          'qty':product_line.get('qty',1) ,
                    #         #  'extra_price':product_line.get('extra_price',0) ,
                             
                             
                    #            })   )
                    
                    
                    # title_record_id =  combo_title_obj.search(
                    #     [('id','=',addons_line.get('title_id',False) )]   )
                    # if not title_record_id:
                        
                    #     result = { 
                    #             "message":"Sorry , Tilte ID Provide With Addons not Found.", 
                    #             }
                    #     # Response.status = "403"
                    #     return result    
                    
                    addons_line_vals.append(
                        (0,0,{
                               "main_product_id": product.id,
                               'product_id':addons_line.get('product_id') ,
                               'qty':addons_line.get('qty',1) ,
                            #   "title_id": addons_line.get('title_id'),
                            #   "line_addons_ids":product_line_vals,

                        })
                    )
                

                    
                
                line_vals.append((0, 0, {
                                        # 'name': product.name, 
                                        'full_product_name': product.display_name, 
                                        'product_id': product.id, 
                                        'name_ar': line.get('name_ar'),
                                        'name_en': line.get('name_en'),
                                        'main_product_id': line.get('main_product_id'),
                                        'qty': line.get('qty'),
                                        'price_unit': line.get('unit_price'),
                                        'tax_ids_after_fiscal_position': account_tax_ids.ids,
                                        'price_subtotal': line.get('subtotal'),
                                        'price_subtotal_incl': line.get('total'),
                                        'customer_note': line.get('customer_note',False),
                                        'custom_note': line.get('custom-note',False),
                                        # 'product_line_ids':product_line_vals,
                                        'product_note_ids':line.get('note_ids',[]),
                                        'product_extra_ids':extra_line_vals,
                                        'product_addons_ids':addons_line_vals,
                                        'is_show':line.get('is_show',False),
                                        'status':line.get('status',False),
                                        'is_send_to_kitchen':line.get('is_send_to_kitchen',False),
                                        'item_kitchen_state':line.get('item_kitchen_state',False),
                                       
                                        }
                                    ))
                # print(">>>>>>>>>line_vals ",line_vals)
            # 1/0     
            order_pricing = kw.get('pricing')      
            payment_method_obj = request.env['pos.payment.method'].sudo()                
            for payment in order_pricing.get('payments'):
                payment_method_exist = payment_method_obj.search([('id', '=', payment.get('payment_method_id'))])
                if not payment_method_exist:
                    result = { 
                                "message":"Payment Method ID not found.", 
                                }
                    # Response.status = "403"
                    return result                                        
                payment_ids.append((0, 0, {
                                            'payment_method_id': payment_method_exist.id, 
                                            'amount': payment.get('amount'),
                                            # 'branch_id': payment.get('branch_id'),
                                            'payment_time':payment.get('payment_time',False)
                                            }
                                    ))   
            
            order_id.lines.unlink()
            order_id.payment_ids.unlink()
            order_id.write({  
                                        # 'name': session.config_id.name + '/' + session.name, 
                                        # 'session_id': session.id, 
                                        'is_order_updated':order.get('is_order_updated',False),
                                        'user_id': order.get('user_id'), 
                                        'date_order': order.get('order_date',False), 
                                        'notes': order.get('notes'), 
                                        'order_type_id': order.get('order_type_id'),
                                        'discount_type_id': order.get('discount_type_id'),
                                        
                                        "coupon_id": order.get('coupon_id'),
                                        'qr_code': order.get('qr_code'),
                                        'pricelist_id': order.get('pricelist_id'), 
                                        'partner_id': order.get('customer_id'), 
                                        'table_id': order.get('table_id'), 
                                        'note': order.get('note'),
                                        
                                        
                                        "amount_subtotal": order_pricing.get('amount_subtotal',0) ,
                                        "amount_promotion": order_pricing.get('amount_promotion',0),
                                        "amount_coupon": order_pricing.get('amount_coupon',0),
                                        "amount_discount": order_pricing.get('amount_discount',0),
                                        "amount_wallet": order_pricing.get('amount_wallet',0),
                                        # "amount_discount_total": order_pricing.get('amount_discount_total',0),
                                        # "amount_subtotal_discounted": order_pricing.get('amount_subtotal_discounted',0),
                                        "amount_tax": order_pricing.get('amount_tax',0),
                                        "amount_total": order_pricing.get('amount_total',0),
                                        "amount_paid": order_pricing.get('amount_total',0),
                                        "amount_return": order_pricing.get('amount_return',0),
                                        "return_to_wallet": order.get('return_to_wallet',False),

                                        # "amount_paid": order_pricing.get('amount_paid',0),
                                        # "amount_return": order_pricing.get('amount_return',0),


                                        
                                        'branch_id': order.get('branch_id'),
                                        'customer_count': 1,
                                        'd_o_number': order.get('d_o_number'),
                                            
                                        # 'coupon_id': order.get('coupon_id'),
                                        'return_reason_id': order.get('return_reason_id'),
                                        'return_order_id' : order.get('return_order_id'),
                                        # 'pos_reference': order.get('pos_reference'),
                                        # 'mobile_ref': order.get('mobile_ref'),
                                        'payment_ids': payment_ids,
                                        'lines': line_vals,
                                        'note':kw.get('note',False),
                                        'order_kitchen_state':order.get('order_kitchen_state',False),
                                        'state':order.get('status','draft')
                                            })
        
        response = {  
                        "message": "Order is Updated successfully.", 
                        "body" : {
                        "Order_id": order_id.id
                        }
                    } 
        # Response.status = "200"
        return response




    @validate_token
    @http.route('/pos_custom/update_order_state', type='json', methods=['POST'], auth="none", csrf=False)
    def update_order_state(self, **kw):
        """ API to update order state """
        order_obj = request.env['pos.order'].sudo()
        
        
        orders = kw.get('orders')

        for order in orders:

        
            if not order.get('order_id',False):
                result = {  
                            "message":"Order ID not Provided",
                        }
                # Response.status = "401"
                return result  

            order_id = order_obj.search([('id','=',order.get('order_id',False))])
            
            if not order_id:
                result = { 
                            "message":"Invalid Order ID Not Found.", 
                            }
                # Response.status = "403"  
                return result
            
            if not order.get('state',False):
                result = {  
                            "message":"State not Provided",
                        }
                # Response.status = "401"
                return result

            if order.get('state',) not in ['draft','send_to_kitchen','ready','cancel','paid','done','invoiced','scrap']:
                result = {  
                            "message":"State Value Error",
                        }
                # Response.status = "401"
                return result
            
            
            order_id.write({'state':order.get('state',False)
                                            })
        
        response = {  
                        "message": "Order State is Updated successfully.", 
                        
                    } 
        # Response.status = "200"
        return response


    @validate_token
    @http.route('/pos_custom/update_order_kitchen_state', type='json', methods=['POST'], auth="none", csrf=False)
    def update_order_kitchen_state(self, **kw):
        """ API to update order Kitchen state """
        order_obj = request.env['pos.order'].sudo()
        
        
        orders = kw.get('orders')

        for order in orders:

        
            if not order.get('order_id',False):
                result = {  
                            "message":"Order ID not Provided",
                        }
                # Response.status = "401"
                return result  

            order_id = order_obj.search([('id','=',order.get('order_id',False))])
            
            if not order_id:
                result = { 
                            "message":"Invalid Order ID Not Found.", 
                            }
                # Response.status = "403"  
                return result
            
            if not order.get('order_kitchen_state',False):
                result = {  
                            "message":"State not Provided",
                        }
                # Response.status = "401"
                return result

            
            
            
            order_id.write({'order_kitchen_state':order.get('order_kitchen_state',False)
                                            })
        
        response = {  
                        "message": "Order Kitchen State is Updated successfully.", 
                        
                    } 
        # Response.status = "200"
        return response




    @validate_token
    @http.route('/pos_custom/update_order_item_state', type='json', methods=['POST'], auth="none", csrf=False)
    def update_order_item_state(self, **kw):
        """ API to update order state """
        order_obj = request.env['pos.order'].sudo()
        order_line_obj = request.env['pos.order.line'].sudo()
        
        
        order_id = kw.get('order_id',False)
        items = kw.get('items',False)

        # for order in orders:

        
        if not order_id:
            result = {  
                        "message":"Order ID not Provided",
                    }
            # Response.status = "401"
            return result  

        order_id = order_obj.search([('id','=',order_id)])
        
        if not order_id:
            result = { 
                        "message":"Invalid Order ID Not Found.", 
                        }
            # Response.status = "403"  
            return result

        for line in items:
            for order_line in order_id.lines.filtered(lambda rec:rec.product_id.id == line.get('item_id')):
                order_line.item_kitchen_state = line.get('kitchen_state')
                

        

        
        
        response = {  
                        "message": "Items State in is Updated successfully.", 
                        
                    } 
        # Response.status = "200"
        return response


    @validate_token
    @http.route('/pos_custom/update_order_item_state', type='json', methods=['POST'], auth="none", csrf=False)
    def update_order_item_state(self, **kw):
        """ API to update order state """
        order_obj = request.env['pos.order'].sudo()
        order_line_obj = request.env['pos.order.line'].sudo()
        
        
        order_id = kw.get('order_id',False)
        items = kw.get('items',False)

        # for order in orders:

        
        if not order_id:
            result = {  
                        "message":"Order ID not Provided",
                    }
            # Response.status = "401"
            return result  

        order_id = order_obj.search([('id','=',order_id)])
        
        if not order_id:
            result = { 
                        "message":"Invalid Order ID Not Found.", 
                        }
            # Response.status = "403"  
            return result

        for line in items:
            for order_line in order_id.lines.filtered(lambda rec:rec.product_id.id == line.get('item_id')):
                order_line.item_kitchen_state = line.get('kitchen_state')
                

        

        
        
        response = {  
                        "message": "Items State in is Updated successfully.", 
                        
                    } 
        # Response.status = "200"
        return response

    # @validate_token
    @http.route(['/pos_custom/login_pos_pin'], type='json', methods=['POST'], auth="none", csrf=False)
    def login_pos_pin(self, **kw,):
        pos_config_obj = request.env['pos.config'].sudo()
        pos_config_records = pos_config_obj.search([('server_pin_code', '=', kw.get('pin_code'))], limit=1)
        result = []
        if pos_config_records:
            for pos_config in pos_config_records:
                # 
                pos_user = request.env['res.users'].sudo().browse(pos_config.pos_user.id)
                # token_expiry_date = datetime.now() + timedelta(days=365) + timedelta(hours=2)
                # rbytes = os.urandom(40)
                # token = "{}_{}".format("access_token", str(hashlib.sha1(rbytes).hexdigest()))
                # vals = {
                #         "user_id": pos_user.id,
                #         "scope": "userinfo",
                #         # "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                #         "token_expiry_date": token_expiry_date,
                #         "token": token,
                #         }
                
                
                access_token = request.env["api.access_token"].find_or_create_token(user_id=pos_user.id, create=True)

        

                # access_token = request.execute('api.access_token', 'create', [vals]) 
                # for token in access_obj.browse(access_token):  
                # for token in access_obj.browse(access_token.id):  
                #     new_token = token.token        
                #                
                result = {
                            'message': "logged in successfully",
                            'body':{
                                        'pos_id': pos_config.id,
                                        "access_token": access_token.token,
                                        "token_expiry_date":access_token.token_expiry_date
                        }  
                        }              
            # Response.status = "200"
            return result
        else:
            # Response.status = "404"
            result = {
                        'message': 'Not a valid pin code: ' + kw.get('pin_code'),
                    }  
            return result

    @validate_token
    @http.route('/pos_custom/update_user_password', type='json', methods=['POST'], auth="none", csrf=False)
    def update_user_password(self, **kw):
        """ API to update order state """
        user_obj = request.env['res.users'].sudo()
        
        
        user_id = kw.get('user_id',False)
        security_code = kw.get('security_code',False)
        new_security_code = kw.get('new_security_code',False)
        confirm_new_security_code = kw.get('confirm_new_security_code',False)

        

        
        if not user_id:
            result = {  
                        "message":"User ID not Provided",
                    }
            # Response.status = "401"
            return result  

        user_id = user_obj.search([('id','=',user_id)])
        
        if not user_id:
            result = { 
                        "message":"Invalid User ID Not Found.", 
                        }
            # Response.status = "403"  
            return result
        
        if not security_code:
            result = {  
                        "message":"Security Code not Provided",
                    }
            # Response.status = "401"
            return result
        
        if not new_security_code:
            result = {  
                        "message":"New Security Code not Provided",
                    }
            # Response.status = "401"
            return result
        
        if not confirm_new_security_code:
            result = {  
                        "message":"Confirm New Security Code not Provided",
                    }
            # Response.status = "401"
            return result


        if user_id.security_pin != security_code:
            result = {  
                        "message":"Sorry !!, You didn't provide correct Security Pin code",
                    }
            # Response.status = "401"
            return result
        
        if new_security_code != confirm_new_security_code:
            result = {  
                        "message":"Sorry !!, New Security Code didn't Match Confirm Security Code.",
                    }
            # Response.status = "401"
            return result
        
        if user_id.security_pin != security_code:
            result = {  
                        "message":"Sorry !!, Same Securty Code !!, Nothing Change.",
                    }
            # Response.status = "401"
            return result
        
        
        user_id.write({'security_pin':new_security_code})
        
        response = {  
                        "message": "User Password Updated successfully.", 
                        
                    } 
        # Response.status = "200"
        return response


    @validate_token
    @http.route(['/pos_custom/get_config'], type='json', methods=['POST'],  auth="none", csrf=False)
    def get_config(self, **kw,):

        pos_id = kw.get('pos_id',False)
        if not pos_id:
            result = {  
                        "message":"POS ID not Provided",
                    }
            # Response.status = "401"
            return result   
        pos_config_obj = request.env['pos.config'].sudo()
        
        pos_config = pos_config_obj.search([('id', '=', pos_id)])
        
        if not pos_config:
            result = { 
                        "message":"Invalid POS Not Found.", 
                        }
            # Response.status = "403"  
            return result


        result = []
        
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        result = {
                    'message': "get POS successfully",
                    'body':{
                                'pos_id': pos_config.id,
                                "is_pos_restaurant": pos_config.module_pos_restaurant,
                                'is_main_kitchen': pos_config.is_main_kitchen,
                                "is_order_printer": pos_config.is_order_printer,
                                'name': pos_config.name,
                                "branch_id": pos_config.branch_id.id,
                                "branch_name": pos_config.branch_id.name,
                                "branch_address": pos_config.branch_id.address,
                                "company_id": pos_config.company_id.id,
                                "logo": base_url + '/web/image?' + 'model=res.company&id=' + str(pos_config.company_id.id) + '&field=logo',
                                "tax_en_name": pos_config.company_id.account_sale_tax_id.name,
                                "tax_ar_name": pos_config.company_id.account_sale_tax_id.arabic_name,
                                "company_name": pos_config.company_id.name,
                                'company_phone':pos_config.company_id.phone,
                                'company_mobile':pos_config.company_id.mobile,
                                'company_email':pos_config.company_id.email,
                                'company_street':pos_config.company_id.street,
                                'company_street2':pos_config.company_id.street2,
                                'company_city':pos_config.company_id.city,
                                'company_state_id':pos_config.company_id.state_id.id,
                                'company_state_name':pos_config.company_id.state_id.name,
                                'company_zip':pos_config.company_id.zip,
                                'company_registry':pos_config.company_id.company_registry,
                                'company_tax':pos_config.company_id.vat,
                                "discount_password":pos_config.pin_code,
                                # 'discount_product_id': pos_config.discount_product_id.id,
                                'discount_product_id': pos_config.discount_program_product_id.id,
                                "database_url": pos_config.pos_url, # + "/web/login",
                                "database": pos_config.pos_database,
                                'multi_session_id': pos_config.multi_session_id.id,
                                'floor_and_table': pos_config.is_table_management,
                                'tax_included':True if pos_config.iface_tax_included == 'total' else False,
                                'discount_programs': pos_config.discount_program_active,
                                'split_table_availability': pos_config.allow_split_table,
                                'transfer_table_availability': pos_config.allow_transfer_table,
                                'custom_discount_availability': pos_config.is_allow_custom_disc,
                                'header_and_footer': pos_config.is_header_or_footer,
                                'pricelist_id': pos_config.pricelist_id.id,
                                'use_advance_pricelist':pos_config.use_pricelist,
                                "promotion_active":pos_config.promotion_auto_add,
                                # "order_type_ids":[ order_type.id for order_type in pos_config.order_type_ids ],
                                "default_type_order_type_id":pos_config.default_type_order_type_id.id,
                                "order_type_active":pos_config.order_type_active,
                                "available_pricelists": [
                                            {
                                                "id": advance_pricelist.id,
                                                "name_ar": advance_pricelist.arbic_name,
                                                "name_en": advance_pricelist.name
                                            } for advance_pricelist in pos_config.available_pricelist_ids
                                            
                                        ],

                                "payment_methods":
                                    [
                                        {
                                            'id': payment_method.id,
                                            'type': payment_method.type,
                                            'split_trans':payment_method.split_transactions,
                                            'name_en': payment_method.name,
                                            'name_ar': payment_method.arbic_name,
                                            'image': base_url + '/web/image?' + 'model=pos.payment.method&id=' + str(payment_method.id) + '&field=image_1920',
        
                                            
                
                                        } for payment_method in pos_config.payment_method_ids
                                    ], 
                                "return_payment_methods":
                                    [
                                        {
                                            'id': payment_method.id,
                                            'type': payment_method.type,
                                            'split_trans':payment_method.split_transactions,
                                            'name_en': payment_method.name,
                                            'name_ar': payment_method.arbic_name,
                                            'image': base_url + '/web/image?' + 'model=pos.payment.method&id=' + str(payment_method.id) + '&field=image_1920',
        
                                            
                
                                        } for payment_method in pos_config.return_payment_method_ids
                                    ],  
                                "active_wallet":pos_config.active_wallet,
                                "wallet_program":
                                    
                                        {
                                            'id': pos_config.wallet_id.id,
                                            'name': pos_config.wallet_id.name,
                                            
                                            'order_amount_type': pos_config.wallet_id.order_amount_type,
                                            'type': pos_config.wallet_id.type,
                                            'every_fixed_amount':pos_config.wallet_id.order_amount_type_fixed,
                                            'every_quantity_amount':pos_config.wallet_id.order_amount_type_quant,
                                            'wallet_amount':pos_config.wallet_id.order_amount_type_fixed_amount,
                                            'percentage':pos_config.wallet_id.order_amount_type_perc,
                                            
                                            'product_ids':
                                                [
                                                    {
                                                        'product_id': product.product_id.id,
                                                        'product_name': product.product_id.name,
                                                        'every_fixed_amount':product.order_amount_type_fixed,
                                                        'every_quantity_amount':product.order_amount_type_quant,
                                                        'wallet_amount':product.order_amount_type_fixed_amount,
                                                        'percentage':product.order_amount_type_perc,
                                                    } for product in pos_config.wallet_id.product_ids
                                                ],
                                            'category_ids':
                                                [
                                                    {
                                                        'category_id': category.pos_category_id.id,
                                                        'category_name': category.pos_category_id.name,
                                                        'every_fixed_amount':category.order_amount_type_fixed,
                                                        'every_quantity_amount':category.order_amount_type_quant,
                                                        'wallet_amount':category.order_amount_type_fixed_amount,
                                                        'percentage':category.order_amount_type_perc,
                                                    } for category in pos_config.wallet_id.category_ids
                                                ],
                                            'ecom_category_ids':
                                                [
                                                    {
                                                        'ecom_category_id': ecom_category.ecom_category_id.id,
                                                        'ecom_category_name': ecom_category.ecom_category_id.name,
                                                        'every_fixed_amount':ecom_category.order_amount_type_fixed,
                                                        'every_quantity_amount':ecom_category.order_amount_type_quant,
                                                        'wallet_amount':ecom_category.order_amount_type_fixed_amount,
                                                        'percentage':ecom_category.order_amount_type_perc,
                                                    } for ecom_category in pos_config.wallet_id.ecom_category_ids
                                                ]
                                        }  if pos_config.wallet_id else False,                                                                                    
                            }
                }                
        # Response.status = "200"
        return result
        
    @validate_token
    @http.route('/pos_custom/check_coupon', type='json', methods=['POST'], auth="none", csrf=False)
    def check_coupon(self, **kw):
        """ check coupon validity"""
        pos_gift_coupon_obj = request.env['pos.gift.coupon'].sudo()
        pos_gift_coupon_obj_obj_records = pos_gift_coupon_obj.search([('c_barcode', '=', kw.get('coupon_barcode'))],limit=1)
        result = []
        if pos_gift_coupon_obj_obj_records:
            for gift_coupon in pos_gift_coupon_obj_obj_records:
                remain_count = gift_coupon.coupon_apply_times - len(gift_coupon.order_ids)
                if remain_count > 0 and gift_coupon.expiry_date.date() > fields.Date.today():
                    valid = True
                else:
                    valid = False            
                result += [{
                    'active': gift_coupon.active,
                    'coupon_allow_times': gift_coupon.coupon_apply_times,
                    'coupon_applied_times': len(gift_coupon.order_ids),
                    'expiry_date': gift_coupon.expiry_date.date(),
                    'customer_id':gift_coupon.partenr_id.id,
                    'valid': valid,
                }]
            # Response.status = "200"
        else:
            # Response.status = "404"
            result = [{
                        'Not Found': kw.get('coupon_barcode'),
                    }]
        return result

    @validate_token
    @http.route('/pos_custom/streaming_order', type='json', methods=['POST'], auth="none", csrf=False)
    def streaming_order(self, **kw):
        """ API to sync streaming order from delivery App to Odoo """
        streaming_order_obj = request.env['streaming.order'].sudo()
        status = {}
        for streaming_order in kw.get('streaming_orders'):
            create_status = streaming_order_obj.create({
                                                        'name': streaming_order.get('name'), 
                                                        })
            status.update({create_status.name: create_status.id,})
        # Response.status = "200"
        response = {"code": "200", "message": "streaming order created successfully.", "status": status}
        return response

    # @validate_token
    # @http.route('/pos_custom/get_all_coupon', type='json', methods=['POST'], auth="none", csrf=False)
    # def get_all_coupon(self, **kw):
    #     """ get all pos gift coupon """
    #     pos_id = kw.get('pos_id',False)
    #     if not pos_id:
    #         result = {  
    #                     "message":"POS ID not Provided",
    #                 }
    #         # Response.status = "401"
    #         return result

    #     check_pos_id = request.env['pos.config'].sudo().search([('id','=',pos_id)])
         
    #     if not check_pos_id:
    #         result = {  
    #                     "message":"POS ID not Found",
    #                 }
    #         # Response.status = "401"
    #         return result
        
        
    #     pos_gift_coupon_obj = request.env['pos.gift.coupon']
    #     # pos_gift_coupon_obj_obj_records = pos_gift_coupon_obj.sudo().search([('applied_app', '=', kw.get('applied_app')),('id', 'not in', kw.get('coupon_ids'))])
        
    #     pos_gift_coupon_obj_obj_records = pos_gift_coupon_obj.sudo().search(
    #         [('applied_pos_ids','in',check_pos_id.ids)]
    #         )
    #     data = []
    #     for gift_coupon in pos_gift_coupon_obj_obj_records:
    #         data += [{
    #             'id': gift_coupon.id,
    #             'name': gift_coupon.name,
    #             'product_id': gift_coupon.product_id.id,
    #             'active': gift_coupon.active,
    #             'coupon_apply_times': gift_coupon.coupon_apply_times,
    #             # 'applied_app': gift_coupon.applied_app,
    #             'c_barcode': gift_coupon.c_barcode,
    #             'amount_type': gift_coupon.amount_type,
    #             'apply_coupon_on': gift_coupon.apply_coupon_on,
    #             'issue_date': gift_coupon.issue_date,
    #             'exp_dat_show': gift_coupon.exp_dat_show,
    #             'expiry_date': gift_coupon.expiry_date,
    #             'amount': gift_coupon.amount,
    #             'partner_true': gift_coupon.partner_true,
    #             'partner_id': gift_coupon.partner_id.id,
    #             'is_categ': gift_coupon.is_categ,
    #             'categ_ids':[ category.id for category in gift_coupon.categ_ids ],
    #             'max_amount': gift_coupon.max_amount,
    #             'coupon_desc': gift_coupon.coupon_desc,
    #             'description': gift_coupon.description,
    #         }]

    #     # Response.status = "200"
    #     result = {
    #                 'message': "Get All POS Coupons Successfully",
    #                 'body': data                    
    #             }     
    #     return result
        
    #     return result

    
    @validate_token
    @http.route('/pos_custom/get_all_coupon', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_coupon(self, **kw):
        """ get all pos gift coupon """
        pos_id = kw.get('pos_id',False)

        #applied_app = kw.get('applied_app',False)
        #if not applied_app:
        #    result = {  
        #                "message":"Sorry Applied App not Provided",
        #            }
        #    # Response.status = "401"
        #    return result
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
        
        
        pos_gift_coupon_obj = request.env['pos.gift.coupon'].sudo()
        pos_gift_coupon_records = pos_gift_coupon_obj.search(
            [('applied_pos_ids','in',check_pos_id.ids),
            #('applied_app', '=', applied_app),
]
            )
        data = []
        

            
        
        for record in pos_gift_coupon_records:
            gift_coupon = record
            remain_count = gift_coupon.coupon_apply_times - len(gift_coupon.order_ids)
            
            valid = True
            
            if (remain_count <= 0):
                valid = False
            
            if (gift_coupon.exp_dat_show and fields.Date.today() > gift_coupon.expiry_date.date() ):
                valid = False
            
            
            
            
            amount_type = 'amount' if  gift_coupon.amount_type == 'fix' else 'percentage'
            amount = gift_coupon.amount
            
            data.append({
                        "coupon_id": gift_coupon.id,
                        "coupon_name": gift_coupon.name,
                        "customer_id":gift_coupon.partner_id.id,
                        "valid": valid,
                        "discount": {
                            "type": amount_type,
                            "value": amount,
                            "max_amount":gift_coupon.max_amount,
                        }
                    }
                    )
        
        result =  {
                "message": "Get all coupons success",
                "body": data,
        
            }
        
        # Response.status = "200"
        
        return result

    @validate_token
    @http.route('/pos_custom/get_all_pos_coupon', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_pos_coupon(self, **kw):
        """ get all pos gift coupon """

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
            

        pos_gift_coupon_obj = request.env['pos.gift.coupon'].sudo()
        pos_gift_coupon_obj_obj_records = pos_gift_coupon_obj.search(
            [('','','')]
            )
        result = []
        for gift_coupon in pos_gift_coupon_obj_obj_records:
            result += [{
                'id': gift_coupon.id,
                'name': gift_coupon.name,
                'product_id': gift_coupon.product_id.id,
                'active': gift_coupon.active,
                'coupon_apply_times': gift_coupon.coupon_apply_times,
                # 'applied_app': gift_coupon.applied_app,
                'c_barcode': gift_coupon.c_barcode,
                'amount_type': gift_coupon.amount_type,
                'apply_coupon_on': gift_coupon.apply_coupon_on,
                'issue_date': gift_coupon.issue_date,
                'exp_dat_show': gift_coupon.exp_dat_show,
                'expiry_date': gift_coupon.expiry_date,
                'amount': gift_coupon.amount,
                'partner_true': gift_coupon.partner_true,
                'partner_id': gift_coupon.partner_id.id,
                'is_categ': gift_coupon.is_categ,
                'categ_ids':[ category.id for category in gift_coupon.categ_ids ],
                'max_amount': gift_coupon.max_amount,
                'coupon_desc': gift_coupon.coupon_desc,
                'description': gift_coupon.description,
            }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route('/pos_custom/sync_scrap_order', type='json', methods=['POST'], auth="none", csrf=False)
    def sync_scrap_order(self, **kw):
        """ API to sync scrap orders from Mobile App to Odoo """
        scrap_obj = request.env['stock.scrap'].sudo()
        status = {}
        required_values = ['name', 'product_id', 'scrap_qty', 'location_id', 'scrap_location_id', 'scrap_reason_id', 'pos_session_id', 'pos_config_id']
        for order in kw.get('scrap_orders'):
            session = request.env['pos.session'].sudo().search([('id', '=', order.get('pos_session_id')), ('state', '=', 'opened')])
            if not session:
                # Response.status = "403"
                result = { 
                            "code": "403",
                            "message":"Invalid session.", 
                            }
                return result                
            exist_id = scrap_obj.search([('id', '=', order.get('id'))])
            if not exist_id:
                missing_values = self._check_required_values(data=order, keys=required_values)
                if missing_values:
                    message = "Missing parameters: %s !" % ', '.join(missing_values)
                    status.update({order.get('name'): message})
                    continue
                scrap_order_created = scrap_obj.create({  
                                                        'name': order.get('name'), 
                                                        'product_id': order.get('product_id'), 
                                                        'scrap_qty': order.get('scrap_qty'), 
                                                        'location_id': order.get('location_id'), 
                                                        'scrap_location_id': order.get('scrap_location_id'), 
                                                        'origin': order.get('origin'),
                                                        'scrap_reason_id': order.get('scrap_reason_id'),
                                                        'pos_session_id': order.get('pos_session_id'),
                                                        'pos_config_id': order.get('pos_config_id'),
                                                        'product_uom_id': request.env['product.product'].sudo().search([('id', '=', order.get('product_id'))]).product_tmpl_id.uom_id.id,
                                                    })
                status.update({scrap_order_created.name: scrap_order_created and True or False})
        # Response.status = "200"
        response = {"code": "200", "message": "Scrap Orders created successfully!",}
        return response

    @validate_token
    @http.route('/pos_custom/all_get_scrap_reason', type='json', methods=['POST'], auth="none", csrf=False)
    def all_get_scrap_reason(self, **kw):
        """ get scrap reason """
        scrap_reason_obj = request.env['pos.scrap_reason'].sudo()
        scrap_reason_obj_records = scrap_reason_obj.search([('id', 'not in', kw.get('scrap_reason_ids'))])
        data = []
        for scrap_reason in scrap_reason_obj_records:
            data += [{
                'id': scrap_reason.id,
                'en_name': scrap_reason.short_name,
                'ar_name': scrap_reason.arbic_name,
                'desc': scrap_reason.desc,
            }]
        # Response.status = "200"
        
        result = {
        "message": "Get all companies successfully.",
        "body" : data
            }


        return result

    @validate_token
    @http.route('/pos_custom/all_get_key_type', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_key_type(self, **kw):
        """ get key type """
        key_type_obj = request.env['key.type'].sudo()
        key_type_obj_records = key_type_obj.search([('id', 'not in', kw.get('key_type_ids'))])
        result = []
        for key_type in key_type_obj_records:
            result += [{
                'id': key_type.id,
                'name': key_type.name,
            }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route('/pos_custom/all_get_pos_type', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_pos_type(self, **kw):
        """ get pos type """
        pos_type_obj = request.env['pos.type'].sudo()
        pos_type_obj_records = pos_type_obj.search([('id', 'not in', kw.get('pos_type_ids'))])
        result = []
        for pos_type in pos_type_obj_records:
            result += [{
                'id': pos_type.id,
                'name': pos_type.name,
            }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route('/pos_custom/get_all_price_list', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_price_list(self, **kw):
        """ get all price_list """
        pricelist_obj = request.env['product.pricelist'].sudo()
        pricelist_records = pricelist_obj.search([('id', 'not in', kw.get('price_list_ids'))])
        result = []
        for pricelist in pricelist_records:
            result += [{
                'id': pricelist.id,
                'name': pricelist.name,
                'arbic_name': pricelist.arbic_name,
                "item_ids":
                    [
                        {
                            'id': item.id,
                            'product_tmpl_id': item.product_tmpl_id.id,
                            'product_id': item.product_id.id,
                            'min_quantity': item.min_quantity,
                            'fixed_price': item.fixed_price,
                            'date_start': item.date_start,
                            'date_end': item.date_end,
                        } for item in pricelist.item_ids
                    ],                            
                'country_group_ids':[
                                        country_group.id for country_group in pricelist.country_group_ids
                                    ],  
                'website_id': pricelist.website_id.id,
                'selectable': pricelist.selectable,
                'code': pricelist.code,
            }]
        # Response.status = "200"
        return result

    
    @validate_token
    @http.route('/pos_custom/get_pos_price_list',type='json', methods=['POST'], auth="none", csrf=False)
    def get_pos_price_list(self, **kw):
        """ get pos price_list """

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

        
        pricelist_records = pos_config_record.available_pricelist_ids
        data = []
        for pricelist in pricelist_records:
            data += [{
                'id': pricelist.id,
                'name': pricelist.name,
                'arbic_name': pricelist.arbic_name,
                "item_ids":
                    [
                        {
                            'id': item.id,
                            'product_tmpl_id': item.product_tmpl_id.id,
                            'product_id': item.product_id.id,
                            'min_quantity': item.min_quantity,
                            'fixed_price': item.fixed_price,
                            'date_start': item.date_start,
                            'date_end': item.date_end,
                        } for item in pricelist.item_ids
                    ],                            
                'country_group_ids':[
                                        country_group.id for country_group in pricelist.country_group_ids
                                    ],  
                'website_id': pricelist.website_id.id,
                'selectable': pricelist.selectable,
                'code': pricelist.code,
            }]
        # Response.status = "200"
        result = {
                    'message': "Get All  POS Pricelist Successfully",
                    'body': data                    
                }     
        return result

    @validate_token
    @http.route('/pos_custom/get_all_product_note', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_product_note(self, **kw):
        """ get all product note """
        pos_product_note_obj = request.env['pos.product_note'].sudo()
        pos_product_note_obj_records = pos_product_note_obj.search([('id', 'not in', kw.get('product_note_ids'))])
        result = []
        for product_note in pos_product_note_obj_records:
            result += [{
                'id': product_note.id,
                'name': product_note.name,
                'arbic_name': product_note.arbic_name,
                'pos_category_ids':[
                                    category.id for category in product_note.pos_category_ids
                                ]
            }]
        # Response.status = "200"
        return result

    def _check_required_values(self, data=None, keys=None):
        missing_data = []
        if keys and data:
            for key in keys:
                if not all([key in data, data.get(key)]):
                    missing_data.append(key)
        return missing_data or False

    @validate_token
    @http.route('/pos_custom/sync_orders', type='json', methods=['POST'], auth="none", csrf=False)
    def create_orders(self, **kw):
        """ API to sync orders from Mobile App to Odoo """
        order_obj = request.env['pos.order'].sudo()
        product_obj = request.env['product.product'].sudo()
        status = {}
        for order in kw.get('orders'):
            session = request.env['pos.session'].sudo().search([('id', '=', order.get('session_id')), ('state', '=', 'opened')])
            if not session:
                # Response.status = "403"
                result = { 
                            "code": "403",
                            "message":"Invalid session.", 
                            }
                return result                
            exist_id = order_obj.search([('id', '=', order.get('id'))])
            if not exist_id:
                line_vals = []
                for line in order.get('lines'):
                    product = product_obj.search([('id', '=', line.get('product_id'))])
                    if not product:
                        product = product_obj.create({'name': line.get('full_product_name'),})
                    line_vals.append((0, 0, {'name': order.get('name'), 'product_id': product.id, 'full_product_name': product.name, 'qty': line.get('qty', 0.0), 'price_unit': line.get('price_unit', 0.0), 'price_subtotal': line.get('price_subtotal', 0.0), 'price_subtotal_incl': line.get('price_subtotal_incl', 0.0)}))
                order_created = order_obj.create({  'name': order.get('name'), 'session_id': order.get('session_id'), 
                                                    'user_id': order.get('user_id'), 
                                                    'amount_tax': order.get('amount_tax'), 'amount_total': order.get('amount_total'), 
                                                    'amount_paid': order.get('amount_paid'), 'amount_return': order.get('amount_return'), 
                                                    'order_type_id': order.get('order_type_id'),
                                                    'note': order.get('note'),
                                                    'coupon_id': order.get('coupon_id'),
                                                    'return_reason_id': order.get('return_reason_id'),
                                                    'branch_id': order.get('branch_id'),
                                                    'pos_reference': order.get('pos_reference'),
                                                    'pricelist_id': order.get('pricelist_id'),
                                                    'mobile_ref': order.get('mobile_ref'),
                                                    'lines': line_vals})
                status.update({order_created.mobile_ref: order_created.id,})
        # Response.status = "200"
        response = {"code": "200", "message": "Orders created successfully!", "status": status}
        return response

    @validate_token
    @http.route('/pos_custom/sync_customers', type='json', methods=['POST'], auth="none", csrf=False)
    def sync_customers(self, **kw):
        """
        API to sync customers from Mobile App to Odoo
        """
        cusotmer_obj = request.env['res.partner'].sudo()
        required_values = ['name', 'mobile']
        status = {}
        for customer in kw.get('customers'):
            exist_id = cusotmer_obj.search([('id', '=', customer.get('id'))])
            if exist_id:
                update_status = exist_id.write({'name': customer.get('name'), 'email': customer.get('email'), 'mobile': customer.get('mobile'), 'mobile_ref': customer.get('mobile_ref')})
                status.update({customer.get('id'): update_status})
            else:
                missing_values = self._check_required_values(data=customer, keys=required_values)
                if missing_values:
                    message = "Missing parameters: %s !" % ', '.join(missing_values)
                    status.update({customer.get('name'): message})
                    continue
                create_status = cusotmer_obj.create({'name': customer.get('name'), 
                                                    'email': customer.get('email'), 
                                                    'mobile': customer.get('mobile'),
                                                    'mobile_ref': customer.get('mobile_ref'),
                                                    })
                # status.update({str(create_status.id) + ' , ' + create_status.name : create_status and True or False})
                status.update({create_status.mobile_ref: create_status.id,})
        # Response.status = "200"
        response = {"code": "200", "message": "Update / Create customers done successfully.", "status": status}
        return response

    @http.route('/web/database/get_db_list_via_url', type='json', methods=['POST'], auth="none", csrf=False)
    def get_db_list_via_url(self, **kw):
        uri = kw.get('url')
        db_list = []
        try:
            conn = xmlrpclib.ServerProxy(uri + '/xmlrpc/db')
            db_list = execute(conn, 'list')
        except Exception as e:
            message = {
                        "message": "Wrong url",
                        "real_error":str(e)
                        } 
            # Response.status = "403"   
            return message
        result = []
        result = {
                    'message': "Get all database Successfully",
                    'body':
                                [
                                    {
                                        'name': db,
                                    } for db in db_list
                                ],                     
                }        
        # Response.status = "200"        
        return result

    # @validate_token
    @http.route('/web/database/get_all_dbs', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_dbs_api(self, **kw):
        """ get all databases available """
        

        result = {
                    'message': "Get all database Successfully",
                    'body':
                                [
                                    {
                                        'name': db,
                                    } for db in http.db_list()
                                ],                     
                } 
        # Response.status = "200"
        return result
    
    @validate_token
    @http.route('/pos_custom/get_all_companies', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_companies_api(self, **kw):
        """ get all companies available not in company_ids"""
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        company_obj = request.env['res.company'].sudo()
        # company_records = company_obj.search([('id', 'not in', kw.get('company_ids'))])
        company_records = company_obj.search([])
        
        result = {
            "message": "Get all companies successfully.",
            'body': [{
                    'id': company.id,
                    'name': company.name,
                    "branch_ids":
                        [
                            {
                                'id': branch.id,
                                'name': branch.name,
                                "poss":
                                    [
                                        {
                                        'id': pos_config.id,
                                        'name': pos_config.name,
                                            
                                        } for pos_config in branch.pos_ids
                                    ]
                            } for branch in company.branch_ids
                        ],                
                    } for company in company_records ] }
        # Response.status = "200"
        return result

    @validate_token
    @http.route('/pos_custom/get_all_branches', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_branches_api(self,**kw):
        """ get all branches available not in branche_ids"""
        branch_obj = request.env['res.branch'].sudo()
        branch_records = branch_obj.search([('id', 'not in', kw.get('branche_ids'))])
        result = []
        for branch in branch_records:
            result += [{
                'id': branch.id,
                'name': branch.name,
                'telephone':branch.telephone,
                'address':branch.address,
                'company_id':branch.company_id.id,
                }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route('/pos_custom/get_all_tax_repartition', type='json', methods=['POST'], auth="none", csrf=False)
    def get_tax_repartition_api(self,# **kw
    ):
        """
        get all tax_repartition_line_ids
        """
        tax_repart_obj = request.env['account.tax.repartition.line'].sudo()
        tax_repart_records = tax_repart_obj.search([])
        result = []
        for tax_repart in tax_repart_records:
            result += [{
                'id': tax_repart.id,
                # 'name': tax_repart.name,
                'factor_percent':tax_repart.factor_percent,
                'repartition_type':tax_repart.repartition_type,
                'account_id':tax_repart.account_id.id,
                'tag_ids':tax_repart.tag_ids.ids,
               
                }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route('/pos_custom/get_all_taxes', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_taxes_api(self, **kw):
        """ get all taxes available """
        tax_obj = request.env['account.tax'].sudo()
        domain = []
        
        if kw.get('taxes_ids',False):
            domain.append(
                ('id', 'in', kw.get('taxes_ids') )
                )
        tax_records = tax_obj.search(domain)
        data = []
        for tax in tax_records:
            data += [{
                'id': tax.id,
                'name': tax.name,
                'ar_name': tax.arabic_name,
                'type_tax_use':tax.type_tax_use,
                # 'tax_scope':tax.tax_scope,
                'company_id':tax.company_id.id,
                'company_name':tax.company_id.name,
                'amount_type':tax.amount_type,
                'amount':tax.amount,
                # 'description':tax.description,
                # 'price_include':tax.price_include,
                # 'tax_group_id':tax.tax_group_id.id,
                # 'analytic':tax.analytic,
                # 'country_id':tax.country_id.id,
                # 'include_base_amount':tax.include_base_amount,
                # 'is_base_affected':tax.is_base_affected,
                # 'children_tax_ids':tax.children_tax_ids.ids,
                # 'invoice_repartition_line_ids':tax.invoice_repartition_line_ids.ids,
                # 'refund_repartition_line_ids':tax.refund_repartition_line_ids.ids,
                }]
        result = {  
                    "message": "Get All Taxes Successful.",
                    "body" : data
                    }
        # Response.status = "200"
        return result

    @validate_token
    @http.route('/pos_custom/update_user_data', type='json',  methods=['POST'], auth="none", csrf=False)
    def update_user_data(self, **kw):
        """ update user data """
        user_record = request.env['res.users'].sudo().browse(request.uid)
        result = []
        for user in user_record:
            if kw.get('name'):
                user.name = kw.get('name')   
                user.partner_id.name = kw.get('name')   
            if kw.get('email'):
                user.partner_id.email = kw.get('email')
            if kw.get('mobile'):
                user.partner_id.mobile = kw.get('mobile')                                                                       
            result = {
                        "code": "200",
                        'message': "User data updated successfully.",
                    }
            # Response.status = "200"
            return result 

    @validate_token
    @http.route('/pos_custom/set_primary_address', type='json',  methods=['POST'], auth="none", csrf=False)
    def set_primary_address(self, **kw):
        """ set primary address """
        user_record = request.env['res.users'].browse(request.uid)
        address_obj = request.env['other.address'].sudo()
        address_records = address_obj.search([('partner_id', '=', user_record.partner_id.id)])
        primary_address_record = address_obj.search([('partner_id', '=', user_record.partner_id.id), ('id', '=', kw.get('primary_address_id'))])
        result = []
        if address_records:
            for address in address_records:
                address.is_primary = False
        if primary_address_record:
            for address in primary_address_record:
                address.is_primary = True            
            result = {
                        "code": "200",
                        'message': "primary address set successfully.",
                    }
            # Response.status = "200"
            return result
        else:
            result = {
                        "code": "401",
                        'message': "Primary address ID not found.",
                    }
            # Response.status = "401"  
            return result 

    @validate_token
    @http.route('/pos_custom/del_user_address', type='json',  methods=['POST'], auth="none", csrf=False)
    def del_user_address(self, **kw):
        """ delete user address """
        user_record = request.env['res.users'].browse(request.uid)
        address_obj = request.env['other.address'].sudo()
        address_records = address_obj.search([('partner_id', '=', user_record.partner_id.id), ('id', '=', kw.get('address_id'))])
        result = []
        if address_records:
            for address in address_records:
                address.unlink()
                result = {
                            "code": "200",
                            'message': "related address deleted successfully.",
                        }
            # Response.status = "200"
            return result
        else:
            result = {
                        "code": "401",
                        'message': "Address ID not found.",
                    }
            # Response.status = "401"  
            return result          

    @validate_token
    @http.route('/pos_custom/get_user_address', type='json',  methods=['POST'], auth="none", csrf=False)
    def get_user_address(self):
        """ get user address """
        user_obj = request.env['res.users']
        user_records = user_obj.search([('id', '=', request.uid)])
        result = []
        for address in user_records.other_address_ids:
            result += [{
                        'id': address.id,
                        'title': address.title,
                        'details': address.details,
                        'latlong': address.latlong,
                        'is_primary': address.is_primary,
                    }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route('/pos_custom/get_user_data', type='json',  methods=['POST'], auth="none", csrf=False)
    def get_user_data(self):
        """ get all user data """
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        user_obj = request.env['res.users']
        user_records = user_obj.search([('id', '=', request.uid)])
        for user in user_records:
            result = {
                "code": "200",
                'id': user.id,
                'login': user.login,
                'name': user.name,
                'email': user.partner_id.email,
                'mobile': user.partner_id.mobile,
                'image': base_url + '/web/image?' + 'model=res.users&id=' + str(user.id) + '&field=image_1920',
            }
        # Response.status = "200"
        return result

    @validate_token
    @http.route('/pos_custom/get_all_users', type='json',  methods=['POST'], auth="none", csrf=False)
    def get_all_users_api(self,# **kw
    ):
        """
        get all users available
        """
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        user_obj = request.env['res.users'].sudo()
        user_records = user_obj.search([])
        result = []
        for user in user_records:
            result += [{
                'id': user.id,
                'name': user.name,
                'arabic_name': user.arabic_name,
                'login': user.login,
                'security_pin':user.security_pin,
                'pos_user_type':user.pos_user_type,
                'image': base_url + '/web/image?' + 'model=res.users&id=' + str(user.id) + '&field=image_1920',
                'pos_security_group_ids':[
                    pos_sec.id for pos_sec in user.pos_security_group_ids
                ],
                'company_ids':[
                    company.id for company in user.company_ids
                ]
            }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_return_reason'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_return_reason_api(self, **kw):
        return_reason_obj = request.env['pos.return_reason'].sudo()
        return_reason_records = return_reason_obj.search([('id', 'not in', kw.get('return_reason_ids'))])
        result = []
        for rt_reason in return_reason_records:
            result += [{
                        'id': rt_reason.id,
                        'name': rt_reason.name,
                        'company_id': rt_reason.company_id.id,
                    }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_pos_config_name'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_pos_config_api(self, **kw):
        pos_config_obj = request.env['pos.config'].sudo()
        pos_config_records = pos_config_obj.search([('id', 'not in', kw.get('pos_config_ids'))])
        result = []
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for pos_config in pos_config_records:
            result += [{
                        'id': pos_config.id,
                        'name': pos_config.name,
                        'company_id': pos_config.company_id.id,
                        "logo": base_url + '/web/image?' + 'model=res.company&id=' + str(
                            pos_config.company_id.id) + '&field=logo',
                        'user_ids': pos_config.user_ids.ids,
                        'pos_type_id': pos_config.pos_type_id.id,
                        'iface_tax_included': pos_config.iface_tax_included,
                    }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_floor_names'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_foor_names_api(self, **kw):
        restaurant_floor_obj = request.env['restaurant.floor'].sudo()
        restaurant_floor_records = restaurant_floor_obj.search([('id', 'not in', kw.get('floor_ids'))])
        result = []
        for restaurant_floor in restaurant_floor_records:
            result += [{
                'id': restaurant_floor.id,
                'name': restaurant_floor.name,
            }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_tables'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_tables_api(self, **kw):
        table_records = request.env['restaurant.table'].sudo().search([('id', 'not in', kw.get('table_ids'))])
        result = []
        for table in table_records:
            result += [{
                        'id': table.id,
                        'name': table.name,
                        'seats': table.seats,
                        'floor_id': table.floor_id.id,
                        'locked': table.locked,
                        'shape': table.shape,
                        }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route('/pos_custom/update_table_state', type='json', methods=['POST'], auth="none", csrf=False)
    def streaming_order(self, **kw):
        """ API to to update table state locked or not locked """
        table_id = kw.get('table_id',False)
        locked = kw.get('locked',False) 

        if not table_id:
            # Response.status = "401"
            response =  [
                    {  
                        "code": "401",
                        "message":"Table ID not Provided",
                    }
                    ]
            return response
        
        

        table_obj = request.env['restaurant.table'].sudo()
        
        table_id = table_obj.search([('id','=',table_id)])
        if not table_id:
            # Response.status = "401"
            response = [
                    {  
                        "code": "401",
                        "message":"Table ID Not Found",
                    }
                    ]
            return response

        table_id.locked = locked
        response = {  
                        "message": "Table Locked State Updated successfully.", 
                        "body" : {
                        "table_id": table_id.id,
                        "locked": table_id.locked
                        }
                    } 
        # Response.status = "200"

        return response
        


    @validate_token
    @http.route('/pos_custom/update_unlock_pos_table_state', type='json', methods=['POST'], auth="none", csrf=False)
    def update_unlock_pos_table_state(self, **kw):
        """ API to to update table state locked or not locked """

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


        
        
        

        table_obj = request.env['restaurant.table'].sudo()
        
        table_ids = table_obj.search([('floor_id.pos_config_id','=',pos_config_record.id)])

        for table in table_ids:
            table.locked = False
        

        
        response = {  
                        "message": "All Table UnLocked successfully.", 
                        "body" : {
                        
                        }
                    } 
        # Response.status = "200"

        return response

    @validate_token
    @http.route(['/pos_custom/get_all_driver_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_driver_api(self, **kw):
        pos_driver_obj = request.env['pos.driver'].sudo()
        pos_driver_records = pos_driver_obj.search([('id', 'not in', kw.get('driver_ids'))])
        result = []
        for driver in pos_driver_records:
            result += [{
                'id': driver.id,
                'name': driver.name,
                'code': driver.code,
                'active': driver.active,
                'company_id': driver.company_id.id,
            }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_pos_payment_method_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_pos_payment_method_data_api(self, **kw):
        pos_payment_method_obj = request.env['pos.payment.method'].sudo()
        pos_payment_method_records = pos_payment_method_obj.search([('id', 'not in', kw.get('payment_method_ids'))])
        result = []
        for pos_payment_method in pos_payment_method_records:
            result += [{
                        'id': pos_payment_method.id,
                        'name': pos_payment_method.name,
                        'arbic_name': pos_payment_method.arbic_name,
                        'method_type': pos_payment_method.type,
                        'journal_id': {'id': pos_payment_method.journal_id.id,
                        'name': pos_payment_method.journal_id.name} if pos_payment_method.journal_id else [],
                        'identify_customer':pos_payment_method.split_transactions,
                    }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_discount_program_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_discount_program_data_api(self, **kw):
        discount_program_obj = request.env['pos.discount_program'].sudo()
        discount_program_records = discount_program_obj.search([('id', 'not in', kw.get('discount_program_ids'))])
        result = []
        for discount_program in discount_program_records:
            result += [{
                'id': discount_program.id,
                'name': discount_program.name,
                'discount_type':discount_program.discount_type ,
                'require_customer':discount_program.require_customer,
                # 'customer_restricted':discount_program.customer_restricted,
                'amount':discount_program.amount,
                "pos_category_ids":
                [ categ.id for categ in discount_program.pos_category_ids ],
                "pos_applied":
                [ pos.id for pos in discount_program.pos_applied ],
                'discount_program_product_id': discount_program.discount_program_product_id.id,
            }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_all_pos_order_type_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_pos_order_type_data_api(self, **kw):

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

        
        pos_order_type_records = request.env['pos.order_type'].sudo().search([('id','in',pos_config_record.order_type_ids.ids)])
        pos_order_type_list = []
        for pos_order_type in pos_order_type_records:
            pos_order_type_list.append({
                                        'id': pos_order_type.id,
                                        'name_ar': pos_order_type.arbic_name,
                                        'name_en': pos_order_type.name,
                                        'is_show_customer_info': pos_order_type.is_show_customer_info,
                                        'is_require_information': pos_order_type.is_require_information,
                                        'is_require_driver': pos_order_type.is_require_driver,
                                        'is_auto_open_table_screen': pos_order_type.is_auto_open_table_screen,
                                        'delivary_product_id':pos_order_type.delivary_product_id.id,
                                        'extra_product_id':pos_order_type.extra_product_id.id,
                                        'extra_percentage':pos_order_type.extra_percentage,
                                        'company_id':pos_order_type.company_id.id,
                                        'account_journal_ids': [ account_journal.id for account_journal in pos_order_type.account_journal_ids ],
                                        'payment_method_ids': [ 
                                                                { 
                                                                    'id': method.id,
                                                                    'name': method.name,
                                                                    'arbic_name': method.arbic_name,
                                                                    } for method in pos_order_type.payment_method_ids ],
                                        'customer':
                                                    {
                                                        'id': pos_order_type.customer_id.id,
                                                        'name': pos_order_type.customer_id.name,
                                                        'mobile': pos_order_type.customer_id.mobile,
                                                        'wallet_balance': pos_order_type.customer_id.wallet_balance,
                                                    },

                                        'price_list_id': pos_order_type.pricelist_id.id,
                                        'type':pos_order_type.type,
                                        })
        # Response.status = "200"
        result = {  
                    "message": "Get Order Types Successful.",
                    "body" : pos_order_type_list
                    }        
        return result

    @validate_token
    @http.route(['/pos_custom/pos_users'], type='json', methods=['POST'], auth="none", csrf=False)
    def pos_users(self, pos_config_id):
        pos_config_obj = request.env['pos.config'].sudo()
        pos_records = pos_config_obj.search([('id', '=', pos_config_id)])
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        result = []
        for pos_config in pos_records:
            result = {
                    'message': "Get all POS users Successfully",
                    'body':
                            [
                                {
                                    'id': user.id,
                                    'name': user.name,
                                    'username': user.login,
                                    'image_url': base_url + '/web/image?' + 'model=res.users&id=' + str(user.id) + '&field=image_1920',
                                    'role':user.pos_user_type,
                                    'last_login':user.login_date,
                                } for user in pos_config.user_ids
                            ],                     
                }             
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/get_pos_config_data'], type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_pos_config_data_api(self, pos_config_id,):
        if not pos_config_id:
            return [
                    {  
                        "code": "403",
                        "message":"pos_config_id not Provided",
                    }
                    ]
        pos_config_obj = request.env['pos.config'].sudo()
        pos_config_records = pos_config_obj.search([('id', '=', pos_config_id)])
        result = []
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for pos_config in pos_config_records:
            result += [{
                'id': pos_config.id,
                'name': pos_config.name,
                'pos_type_id': pos_config.pos_type_id.id,
                'is_main_kitchen': pos_config.is_main_kitchen,
                'is_product_calories_active': pos_config.product_calories,
                'allowed_user_ids': [ user.id for user in pos_config.user_ids ],
                'is_table_management':pos_config.is_table_management,
                'floor_ids': [ floor.id for floor in pos_config.pos_floor_ids ],
                "exclude_pos_categ_ids": [ exclude.id  for exclude in pos_config.exclude_pos_categ_ids ],
                "exclude_product_ids": [ exclude.id for exclude in pos_config.pos_floor_ids ],
                # "product_price": pos_config.iface_tax_included,
                "payment_method_ids": [ p_method.id for p_method in pos_config.payment_method_ids ],
                "order_type_payment_method_ids": [ p_method.id for p_method in pos_config.order_type_payment_method_ids ],
                "header": pos_config.receipt_header,
                "footer": pos_config.receipt_footer,
                "discount_program_active": pos_config.discount_program_active,
                "aval_discount_program": [ aval_disc.id for aval_disc in pos_config.aval_discount_program ],
                # "discount_program_product_id": pos_config.discount_program_product_id.id,
                "allow_pin_code":pos_config.allow_pin_code,
                "pin_code":pos_config.pin_code,
                "order_type_active":pos_config.order_type_active,
                "order_type_ids":[ order_type.id for order_type in pos_config.order_type_ids ],
                # "order_type_journal_ids":[ order_type_journal.id for order_type_journal in pos_config.order_type_journal_ids ],
                "default_type_order_type_id":pos_config.default_type_order_type_id.id,
                'pricelist_id': pos_config.pricelist_id.id,
                'iface_tax_included': pos_config.iface_tax_included,
                'manual_discount': pos_config.manual_discount,
                'restrict_price_control': pos_config.restrict_price_control,
                'use_pricelist': pos_config.use_pricelist,
                "available_pricelist_ids":[ pricelist.id for pricelist in pos_config.available_pricelist_ids ],
                'module_pos_discount': pos_config.module_pos_discount,
                # 'discount_product_id': pos_config.discount_product_id.id,
                'discount_pc': pos_config.discount_pc,
                'allow_split_table': pos_config.allow_split_table,
                # 'allow_merge_table': pos_config.allow_merge_table,
                'allow_transfer_table': pos_config.allow_transfer_table,
                "promotion_ids":[ promotion.id for promotion in pos_config.promotion_ids ],
                "promotion_active":pos_config.promotion_auto_add,
                "branch_id": pos_config.branch_id.id,
                "module_pos_restaurant": pos_config.module_pos_restaurant,
                "is_order_printer": pos_config.is_order_printer,
                
                "branch_id": pos_config.branch_id.id,
                "branch_name": pos_config.branch_id.name,
                "branch_address": pos_config.branch_id.address,
                "company_id": pos_config.company_id.id,
                "logo": base_url + '/web/image?' + 'model=res.company&id=' + str(
                            pos_config.company_id.id) + '&field=logo',
                "active_wallet":pos_config.active_wallet,
                "company_name": pos_config.company_id.name,
                'company_phone':pos_config.company_id.phone,
                "discount_product_id": pos_config.discount_program_product_id.id,
                'mobile':pos_config.company_id.mobile,
                'email':pos_config.company_id.email,
                'street':pos_config.company_id.street,
                'street2':pos_config.company_id.street2,
                'city':pos_config.company_id.city,
                'state_id':pos_config.company_id.state_id.id,
                'state_name':pos_config.company_id.state_id.name,
                'zip':pos_config.company_id.zip,
                'company_registry':pos_config.company_id.company_registry,
                'vat':pos_config.company_id.vat,
            }]
        # Response.status = "200"
        return result

    @validate_token
    @http.route(['/pos_custom/pos_open_session'], type='json', auth="none", csrf=False)
    def pos_open_session_api(self,pos_config_id,balance_start,user_id,note):
        payload = request.httprequest.data.decode()
        payload = json.loads(payload)
        params = payload.get("params")
        if not pos_config_id:
            # Response.status = "403"
            result = {  
                        "message":"POS ID not Provided",
                    }
            return result
        pos_config_obj = request.env['pos.config'].sudo()
        pos_config_record = pos_config_obj.search(
            [('id', '=', pos_config_id)])
        
        if not pos_config_record:
            result = {   
                        "message":"Sorry POS ID Not Found ",
                        }
            # Response.status = "401"
            return result

        if not pos_config_record.current_session_id:
            pos_config_record.open_session_cb()
            bank_statement = request.env['account.bank.statement'].sudo().search([('pos_session_id', '=', pos_config_record.current_session_id.id)],limit=1)
            bank_statement.write({'balance_start': balance_start, 'note': note}) 
            pos_config_record.current_session_id.write({'state': 'opened','user_id':user_id}) 
            # Response.status = "200"
            result = {
                        "message":"Session Opened",
                        'body': {
                                    "session_id":pos_config_record.current_session_id.id,
                                    "session_start": pos_config_record.current_session_id.start_at,
                                }                   
                    }                    
        else:
            # Response.status = "403"
            result = {  
                        "message":"You Can't open new session until already opened session become close",
                    }
        return result

    @validate_token
    @http.route(['/pos_custom/pos_close_session'], type='json', auth="none", csrf=False)
    def pos_close_session_api(self,**kw):
        # user_id = request.uid
        # user_obj = request.env['res.users'].sudo().search([('id', '=', user_id)])
        
        pos_config_id = kw.get('pos_config_id',False)
        if not pos_config_id:
            # Response.status = "401"
            result = {  
                        "message":"POS ID not Provided",
                    }
            return result
        
        balance_end_real = kw.get('balance_end',0)
        # if not balance_end_real:
        #     # Response.status = "401"
        #     result = {  
        #                 "message":"Balance End not Provided",
        #             }
        #     return result

        
        counted_cash = kw.get('counted_cash',0)
        # if not counted_cash:
        #     # Response.status = "401"
        #     result = {  
        #                 "message":"Counted Cash not Provided",
        #             }
        #     return result

        notes = kw.get('notes','')
        
        
        
        pos_config_obj = request.env['pos.config'].sudo()
        
        pos_config_record = pos_config_obj.search([('id', '=', pos_config_id)])
        
        if not pos_config_record:
            result = {  
                        "message":"Sorry POS ID Not Found or not related POS",
                    }
            # Response.status = "401"
            return result
        if pos_config_record.current_session_id:
            current_session = pos_config_record.sudo().current_session_id
            
            bank_statement = request.env['account.bank.statement'].sudo().search([('pos_session_id', '=', pos_config_record.current_session_id.id)],limit=1)
            bank_statement.sudo().write({'balance_end_real': balance_end_real})     
            bank_statement.sudo().balance_end_real = balance_end_real      
            if current_session.order_ids.filtered(lambda order:order.state not in 
             ['paid','done','invoiced','cancel','scrap']):
                result = {  
                            "message":"Sorry you can't close, All Orders must be Confirmed and not in Draft State Before Close",
                        }
                # Response.status = "401"
                return result
            
            current_session.sudo().action_pos_session_closing_control()
            
            # current_session.sudo().post_closing_cash_details(counted_cash)
            # current_session.sudo().update_closing_control_state_session(notes)
            # current_session.sudo().close_session_from_ui()
            
            
            # current_session.sudo().action_pos_session_closing_control()
            # current_session.sudo().action_pos_session_close()

            # self.env['pos.close.session.wizard'].with_context()
            # current_session.sudo()._validate_session()
            # current_session.action_pos_session_closing_control(
            # current_session._get_balancing_account(), balance_end_real
            # )
            
        #     wizard = request.env['pos.close.session.wizard'].create({
        #     'amount_to_balance': balance_end_real,
        #     'account_id': current_session._get_balancing_account().id,
        #     'account_readonly': not request.env.user.has_group('account.group_account_readonly'),
        #     'session_id':current_session.id,
        #     'message': ("There is a difference between the amounts to post and the amounts of the orders, it is probably caused by taxes or accounting configurations changes.")
        # })
        #     wizard.close_session_pos()

            if current_session.state != 'closed':
                bank_statement.sudo().balance_end_real = balance_end_real  

                wizard = request.env['pos.close.session.wizard'].create({
                'amount_to_balance': balance_end_real,
                'account_id': current_session._get_balancing_account().id,
                'account_readonly': not request.env.user.has_group('account.group_account_readonly'),
                'session_id':current_session.id,
                'message': ("There is a difference between the amounts to post and the amounts of the orders, it is probably caused by taxes or accounting configurations changes.")
            })
                wizard.close_session_pos()


                if current_session.state != 'closed':

                    # Response.status = "401"
                    result = {   
                            "message":"Session Not Closed",
                            "body" : {
                                "session_id":current_session.id,
                                "session_state":current_session.state,
                                "bank_statement":bank_statement.id,
                                "bank_end_real":bank_statement.balance_end_real,
                                "balance_end_real":balance_end_real,
                                        }
                            }
                    return result

            # Response.status = "200"
            result = {   
                        "message":"Session Closed",
                        "body" : {"session_id":current_session.id,
                        "session_end": pos_config_record.current_session_id.stop_at if pos_config_record.current_session_id.stop_at else fields.Datetime.now(),
                                    }
                        }
            return result
        else:
            # Response.status = "403"
            result = {   
                        "message":"You Can't Close , maybe it's already closed.",
                    }
        return result

    




























    @validate_token
    @http.route('/pos_custom/set_order_scraping', type='json', methods=['POST'], auth="none", csrf=False)
    def set_order_scraping(self, order_id,product_item_ids,**kw):
        """ set order product scraping"""

        scraping_all_order = False
        if not order_id:
            # Response.status = "401"
            result = {  
                        "message":"POS Order ID not Provided",
                    }
            return result
        
        pos_order_id = request.env['pos.order'].sudo().search([('id','=',order_id)])
        
        if not pos_order_id:
            result = {  
                        "message":"Sorry POS Order ID Not Found or not related POS Order",
                    }
            # Response.status = "401"
            return result
        if pos_order_id.state not in ['ready','return','send_to_kitchen']:
            result = {  
                        "message":"Sorry you can't scrap POS Order if order not in state ready,return and send to kitchen",
                    }
            # Response.status = "401"
            return result

        stock_scrap_obj = request.env['stock.scrap'].sudo()

        warehouse = request.env['stock.warehouse'].sudo().search([('company_id', '=', pos_order_id.company_id.id)], limit=1)
        scrap_location_id = request.env['stock.location'].sudo().search([('scrap_location', '=', True), ('company_id', '=', pos_order_id.company_id.id)], limit=1)
        
        if not warehouse.lot_stock_id:
            result = {  
                        "message":"Sorry Default Location Not Found",
                    }
            # Response.status = "401"
            return result
        
        if not scrap_location_id:
            result = {  
                        "message":"Sorry Default Scrap Location ID Not Found",
                    }
            # Response.status = "401"
            return result

        if scraping_all_order:
            for line in pos_order_id.lines:
                stock_scrap_id = stock_scrap_obj.create({
                    'product_id': line.product_id.id,
                    'scrap_qty':line.qty,
                    'pos_session_id':pos_order_id.session_id.id,
                    'pos_config_id':pos_order_id.config_id.id,
                    'pos_order_id':pos_order_id.id,
                    'company_id':pos_order_id.company_id.id,
                    'product_uom_id':request.env['product.product'].sudo().search([('id', '=', line.product_id.id)]).product_tmpl_id.uom_id.id,
                    'location_id':warehouse.lot_stock_id.id,
                    'scrap_location_id':scrap_location_id.id,
                })
                
                # stock_scrap_id.action_validate()
        
        else:
            
            for item in product_item_ids:
                
                
                stock_scrap_id = stock_scrap_obj.create({
                    'product_id': item['id'],
                    'scrap_qty':item['qty'],
                    'pos_session_id':pos_order_id.session_id.id,
                    'pos_config_id':pos_order_id.config_id.id,
                    'pos_order_id':pos_order_id.id,
                    'company_id':pos_order_id.company_id.id,
                    'product_uom_id':request.env['product.product'].sudo().search([('id', '=', item['id'])]).product_tmpl_id.uom_id.id,
                    'location_id':warehouse.lot_stock_id.id,
                    'scrap_location_id':scrap_location_id.id,
                })
                # stock_scrap_id.action_validate()

        
        # Response.status = "200"
        result = {   
                          "message": "Order is scraping successfully"
                        }
        return result


    @validate_token
    @http.route('/pos_custom/scrap_all_order', type='json', methods=['POST'], auth="none", csrf=False)
    def scrap_all_order(self,**kw):
        """ scrap all order"""
        scrap_all_orders_param = kw.get('scrap_all_orders')
        order_id = scrap_all_orders_param.get('order_id',False)
        scrap_reason_id = scrap_all_orders_param.get('scrap_reason_id',False)

        scrap_reason_obj = request.env['pos.scrap_reason'].sudo()

        if not scrap_reason_id:
            # Response.status = "401"
            result = {  
                        "message":"Scrap Reason ID not Provided",
                    }
            return result
        
        scrap_reason_id = scrap_reason_obj.search([('id', '=', scrap_reason_id)])
        
        if not scrap_reason_id:
            result = {  
                        "message":"Sorry Scrap Reason ID Not Found ",
                    }
            # Response.status = "401"
            return result

        if not order_id:
            # Response.status = "401"
            result = {  
                        "message":"POS Order ID not Provided",
                    }
            return result
        
        pos_order_id = request.env['pos.order'].sudo().search([('id','=',order_id)])
        
        if not pos_order_id:
            result = {  
                        "message":"Sorry POS Order ID Not Found or not related POS Order",
                    }
            # Response.status = "401"
            return result
        if pos_order_id.state not in ['ready','return','send_to_kitchen']:
            result = {  
                        "message":"Sorry you can't scrap POS Order if order not in state ready,return or send to kitchen",
                    }
            # Response.status = "401"
            return result

        stock_scrap_obj = request.env['stock.scrap'].sudo()

        warehouse = request.env['stock.warehouse'].sudo().search([('company_id', '=', pos_order_id.company_id.id)], limit=1)
        scrap_location_id = request.env['stock.location'].sudo().search([('scrap_location', '=', True), ('company_id', '=', pos_order_id.company_id.id)], limit=1)
        
        if not warehouse.lot_stock_id:
            result = {  
                        "message":"Sorry Default Location Not Found",
                    }
            # Response.status = "401"
            return result
        
        if not scrap_location_id:
            result = {  
                        "message":"Sorry Default Scrap Location ID Not Found",
                    }
            # Response.status = "401"
            return result

        for line in pos_order_id.lines:
            stock_scrap_id = stock_scrap_obj.create({
                'product_id': line.product_id.id,
                'scrap_qty':line.qty,
                'pos_session_id':pos_order_id.session_id.id,
                'pos_config_id':pos_order_id.config_id.id,
                'pos_order_id':pos_order_id.id,
                'company_id':pos_order_id.company_id.id,
                'product_uom_id':request.env['product.product'].sudo().search([('id', '=', line.product_id.id)]).product_tmpl_id.uom_id.id,
                'location_id':warehouse.lot_stock_id.id,
                'scrap_location_id':scrap_location_id.id,
                'scrap_reason_id':scrap_reason_id.id

            })
            
            # stock_scrap_id.action_validate()
        pos_order_id.state = 'scrap'
        
        
        # Response.status = "200"
        result = {   
                          "message": "Order is scraping successfully"
                        }
        return result


    @validate_token
    @http.route('/pos_custom/product_scarping', type='json', methods=['POST'], auth="none", csrf=False)
    def product_scarping(self,**kw):
        """ scrap specific products"""
        scrap_reason_obj = request.env['pos.scrap_reason'].sudo()
        stock_scrap_obj = request.env['stock.scrap'].sudo()
        warehouse_obj = request.env['stock.warehouse'].sudo()
        location_obj = request.env['stock.location'].sudo()
        product_obj = request.env['product.product'].sudo()

        scrap_all_orders_param = kw.get('scrap_orders',False)
        
        for order in scrap_all_orders_param:
            order_id = order.get('order_id',False)
            scrap_qty = order.get('scrap_qty',False)
            product_id = order.get('product_id',False)
            scrap_reason_id = order.get('scrap_reason_id',False)


            if not scrap_reason_id:
                # Response.status = "401"
                result = {  
                            "message":"Scrap Reason ID not Provided",
                        }
                return result
            
            scrap_reason_id = scrap_reason_obj.search([('id', '=', scrap_reason_id)])
            
            if not scrap_reason_id:
                result = {  
                            "message":"Sorry Scrap Reason ID Not Found ",
                        }
                # Response.status = "401"
                return result

            if not order_id:
                # Response.status = "401"
                result = {  
                            "message":"POS Order ID not Provided",
                        }
                return result
            
            pos_order_id = request.env['pos.order'].sudo().search([('id','=',order_id)])
            
            if not pos_order_id:
                result = {  
                            "message":"Sorry POS Order ID Not Found or not related POS Order",
                        }
                # Response.status = "401"
                return result
            
            if not product_id:
                # Response.status = "403"
                response = {
                            "message": "Product ID Not Provided"
                            }                                 
                return response
            product_id = product_obj.search([('id','=',product_id)])
            
            if not product_id:
                # Response.status = "403"
                response = {
                            "message": "Product ID not Found"
                            }                                 
                return response

            if pos_order_id.state not in ['ready','return','send_to_kitchen']:
                result = {  
                            "message":"Sorry you can't scrap POS Order if order not in state ready,return or send to kitchen",
                        }
                # Response.status = "401"
                return result

            

        
            warehouse = warehouse_obj.search([('company_id', '=', pos_order_id.company_id.id)], limit=1)
            scrap_location_id = location_obj.search([('scrap_location', '=', True), ('company_id', '=', pos_order_id.company_id.id)], limit=1)
            
            if not warehouse.lot_stock_id:
                result = {  
                            "message":"Sorry Default Location Not Found",
                        }
                # Response.status = "401"
                return result
            
            if not scrap_location_id:
                result = {  
                            "message":"Sorry Default Scrap Location ID Not Found",
                        }
                # Response.status = "401"
                return result

            stock_scrap_id = stock_scrap_obj.create({
                'product_id': product_id.id,
                'scrap_qty':scrap_qty,
                'pos_session_id':pos_order_id.session_id.id,
                'pos_config_id':pos_order_id.config_id.id,
                'pos_order_id':pos_order_id.id,
                'company_id':pos_order_id.company_id.id,
                'product_uom_id':product_obj.search([('id', '=', product_id.id)]).product_tmpl_id.uom_id.id,
                'location_id':warehouse.lot_stock_id.id,
                'scrap_location_id':scrap_location_id.id,
                'scrap_reason_id':scrap_reason_id.id

            })
            
            # stock_scrap_id.action_validate()
        
        
        
        # Response.status = "200"
        result = {   
                          "message": "Product in order is scraping successfully"
                        }
        return result


    @validate_token
    @http.route('/pos_custom/get_order_by_status', type='json', methods=['POST'], auth="none", csrf=False)
    def get_order_by_status(self, order_status):
        """ get order by status"""

        if not order_status:
            # Response.status = "401"
            result = {  
                        "message":"Order Status not Provided",
                    }
            return result
        
        pos_order_ids = request.env['pos.order'].sudo().search([('state','=',order_status)])
        
        if not pos_order_ids:
            result = {  
                        "message":"Sorry POS Order Related to Status Not Found",
                        "body":[],
                    }
            # Response.status = "200"
            return result
        
        order_list = []
        pos_payment_obj = request.env['pos.payment'].sudo()
        for order in pos_order_ids:
            
            totals = {}
            
            sub_total = sum([ line.price_subtotal for line in order.lines])
            vat = sum([ line.price_subtotal_incl - line.price_subtotal for line in order.lines])
            total = sub_total + vat

            totals.update({'sub_total':sub_total,'vat':vat,'total':total})
            pos_payments = pos_payment_obj.read_group([('pos_order_id','=',order.id)],['payment_method_id','payment_method_total:sum(amount)'],['payment_method_id'])
            
            payment_methods = [
                {"paymen_method":str(payment['payment_method_id'][1]),
                "payment_amount":payment['payment_method_total']} for payment in pos_payments
            ]
            
            totals.update({'payment_methods':payment_methods})
            
            
            
            
            order_list.append({
                "id": order.id,
                # "code": "10",
                "table_name": order.table_id.name,
                "date": order.date_order,
                "status": order.state,
                "total": order.amount_total,
                "is_show_customer_info": order.order_type_id.is_show_customer_info,
                "is_require_information": order.order_type_id.is_require_information,
                "is_require_driver": order.order_type_id.is_require_driver,
                "is_auto_open_table_screen": order.order_type_id.is_auto_open_table_screen,
                "pricelist_id": order.pricelist_id.id,
                "delivary_product_id": order.order_type_id.delivary_product_id.id,
                "extra_product_id": order.order_type_id.extra_product_id.id,
                "extra_percentage": order.order_type_id.extra_percentage,
                "company_id": order.company_id.id,
                "pos": order.config_id.name,
                # "vat": "465421",
                # "ret": "pos 15457-010",
                "cashier": order.cashier,#need check , chshier or user
                "order_place": order.order_type_id.type,#need check real place not default
                "note": order.note,
                "products": [
                    {
                        "id": line.product_id.id,
                        "name_ar": line.product_id.name_ar,
                        "name_en": line.product_id.name,
                        "qty": line.qty,
                        "price_of_one": line.price_unit,
                        "vat": line.price_subtotal_incl - line.price_subtotal,
                        "subtotal": line.price_subtotal,
                        "total_price": line.price_subtotal_incl,
                        "notes":[{
                                'id': note.id,
                                'name_en': note.name,
                                'name_ar': note.arbic_name,
                                
                        } for note in line.product_note_ids ],
                    "extra": [
                            {   
                                # "id": extra.id,
                                "product_id": extra.product_id.id,
                                "name_ar": extra.product_id.other_lang_name,
                                "name_en": extra.product_id.name,
                                "price": extra.price,
                               "tax": extra.tax_ids.ids,
                                # "is_selected": note.product_id.is_selected
                            } for extra in line.product_extra_ids
                            
                        ],

                        "addons": [
                            
                            {
                                "title_id": addons.title_id.id,
                                "title_ar": addons.title_id.arabic_name,
                                "title_en": addons.title_id.name,
                                # "pos_category_id":addons.id,
                                
                                 "product_ids": [
                                    {
                                        "product_id": product.product_id.id,
                                        "name_ar": product.product_id.other_lang_name,
                                        "name_en": product.product_id.name,
                                        "qty": product.qty,
                                        "extra_price": product.extra_price,
                                        
                                    } for product in addons.line_addons_ids
                                    ]
                            } for addons in line.product_addons_ids
                            ],


                        "note": line.note,
                        
                    } for line in order.lines
                ],
                "order_pricing": totals,
                "address":{
                    'state': order.partner_id.state_id.name,
                    'city': order.partner_id.city,
                    'street': order.partner_id.street,
                    'street2': order.partner_id.street2,
                    'zip': order.partner_id.zip,
                    'country': order.partner_id.country_id.name,
                },
                
                "qr_code": order.qr_code,
            })


        # Response.status = "200"
        result = {  
                     "message": "Get Orders successfully",
                     "body" : order_list,
            
        

                        }
        
        return result
    


    @validate_token
    @http.route('/pos_custom/get_all_orders', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_orders(self,**kw):
        """ get All Orders"""

        data = kw

        pos_id = kw.get('pos_id',False)
        cahier_id = kw.get('cahier_id',False)
        order_status = kw.get('order_status',False)
        session_id = kw.get('session_id',False)
        
        
        domain = []

        #TODO:Need Refactoring
        if pos_id:
            
            config_id = request.env['pos.config'].sudo().search([('id','=',pos_id)])
            
            if not config_id:
                result = {  
                            "message":"Sorry Not Found any POS with Provided POS ID",
                        
                        }
                # Response.status = "401"
                return result

            domain.append(('config_id','=',pos_id))
        
        if session_id:
            
            session_id = request.env['pos.session'].sudo().search([('id','=',session_id)])
            
            if not session_id:
                result = {  
                            "message":"Sorry Not Found any POS Session with Provided POS ID",
                        
                        }
                # Response.status = "401"
                return result

            domain.append(('session_id','=',session_id.id))
        if cahier_id:
            user = request.env['res.users'].sudo().search([('id','=',cahier_id)])
            if not user:
                result = {  
                            "message":"Sorry Not Found any Cahier with Provided User ID",
                        
                        }
                # Response.status = "401"
                return result


            domain.append(('user_id','=',cahier_id))
        if order_status:
            domain.append(('state','in',order_status))
        
        pos_order_ids = request.env['pos.order'].sudo().search(domain)
        
        if not pos_order_ids:
            result = {  
                        "message":"Sorry Not Found any POS Order With Provided Filters",
                        "body": []
                    }
            # Response.status = "200"
            return result
        
        order_list = []
        pos_payment_obj = request.env['pos.payment'].sudo()
        for order in pos_order_ids:
            payment_methode = []
            totals = {}
            
            sub_total = sum([ line.price_subtotal for line in order.lines])
            vat = sum([ line.price_subtotal_incl - line.price_subtotal for line in order.lines])
            total = sub_total + vat

            totals.update({'sub_total':sub_total,'vat':vat,'total':total})
            pos_payments = pos_payment_obj.read_group([('pos_order_id','=',order.id)],['payment_method_id','payment_method_total:sum(amount)'],['payment_method_id'])
            
            payment_methods = [
                {"paymen_method":str(payment['payment_method_id'][1]),
                "payment_amount":payment['payment_method_total']} for payment in pos_payments
            ]
            
            totals.update({'payment_methods':payment_methods})

            for payment in order.payment_ids:
                payment_methode.append({
                    "payment_method_id": payment.payment_method_id.id,
                            "amount": payment.amount,
                            "payment_time": payment.payment_time,
                            "name_ar": payment.payment_method_id.arbic_name,
                            "name_en": payment.payment_method_id.name,
                })
            
            
            
            
            order_list.append({
                "configuration":{
                "order_id": order.id,
                "is_order_updated":order.is_order_updated,
                'notes': order.notes, 
                "order_no": order.pos_reference_custom,
                "order_ref": order.name_custom,
                "session_id": order.session_id.id,
                "branch_id": order.branch_id.id,
                "pos_id": order.config_id.id,
                "user_id": order.user_id.id,
                "order_type_id": order.order_type_id.id,#need check real place not default
                "d_o_number": order.d_o_number,
                "pricelist_id": order.pricelist_id.id,
                
                "coupon_id": order.coupon_id.id,
                "coupon_name": order.coupon_id.name,
                "discount_type_id":order.discount_type_id.id,
                
                "qr_code": order.qr_code,
                
                "customer_id": order.partner_id.id,
		        "customer_name": order.partner_id.name,
                "table_id": order.table_id.id,
                "table_name": order.table_id.name,
                "pos_name": order.config_id.name,
                "cashier_name": order.user_id.name,#need check , chshier or user
                "order_type_name": order.order_type_id.name,#need check real place not default
                "order_date": order.date_order,
                "status": order.state,
                "order_kitchen_state":order.order_kitchen_state,
                "return_to_wallet": order.return_to_wallet,
                'return_reason_id': order.return_reason_id.id,  
                'return_order_id' : order.return_order_id.id,  
                
                },
                # "code": "10",
                
                
                # 'amount_return': order_pricing.get('amount_return'),   
                "pricing":{
                "amount_subtotal": order.amount_subtotal,
                "amount_promotion": order.amount_promotion,
                "amount_coupon": order.amount_coupon,
                "amount_discount": order.amount_discount,
                "amount_wallet": order.amount_wallet,
                "amount_tax": order.amount_tax,
                "amount_total": order.amount_total,
                'amount_return': order.amount_return,
               
                
                # "amount_discount_total": order.amount_discount_total,
                # "amount_subtotal_discounted": order.amount_subtotal_discounted,
                # "amount_paid": order.amount_paid,
                                        
                # "is_show_customer_info": order.order_type_id.is_show_customer_info,
                # "is_require_information": order.order_type_id.is_require_information,
                # "is_require_driver": order.order_type_id.is_require_driver,
                # "is_auto_open_table_screen": order.order_type_id.is_auto_open_table_screen,
                # "delivary_product_id": order.order_type_id.delivary_product_id.id,
                                        
                # "note": order.note,
                # "extra_product_id": order.order_type_id.extra_product_id.id,
                # "extra_percentage": order.order_type_id.extra_percentage,
                # "company_id": order.company_id.id,
                # "company_name": order.company_id.name,
                # "vat": "465421",
                # "ret": "pos 15457-010",
                "payments":payment_methode,
                # "order_pricing": totals,
                },
                "items": [
                    {
                        "product_id": line.product_id.id,
                        'main_product_id': line.main_product_id.id,
                        "qty": line.qty,
                        "name_ar": line.name_ar,
                        "name_en": line.name_en,
                        "unit_price": line.price_unit,
                        
                        "subtotal": line.price_subtotal,
                        "total": line.price_subtotal_incl,
                        "discount": line.discount,
                        
                        "tax_ids": line.tax_ids_after_fiscal_position.ids,
                        "custom_note":line.custom_note,
                        "note_ids":line.product_note_ids.ids,
                        "status":line.status,
                        "is_send_to_kitchen":line.is_send_to_kitchen,
                        "item_kitchen_state":line.item_kitchen_state,
                        "prepare_time":line.product_id.preparation_time,
                        # "notes":[{
                        #         'id': note.id,
                        #         'name_en': note.name,
                        #         'name_ar': note.arbic_name,
                                
                        #     } for note in line.product_note_ids ],
                        # "vat": line.price_subtotal_incl - line.price_subtotal,
                        "addons": [
                            
                            {
                                "product_id": addons.product_id.id,
                                "qty": addons.qty,
                                        
                                # "title_id": addons.title_id.id,
                                # "title_ar": addons.title_id.arabic_name,
                                # "title_en": addons.title_id.name,
                                
                                #  "product_ids": [
                                #     {
                                #         "product_id": product.product_id.id,
                                #         "name_ar": product.product_id.other_lang_name,
                                #         "name_en": product.product_id.name,
                                #         "qty": product.qty,
                                #         "extra_price": product.extra_price,
                                        
                                #     } for product in addons.line_addons_ids
                                #     ]
                            } for addons in line.product_addons_ids
                            ],
                        "extras": [
                            {   
                                # "id": extra.id,
                                "product_id": extra.product_id.id,
                                "qty": extra.quantity,
                                "name_ar": extra.name_ar,
                                "name_en": extra.name_en,
                                "unit_price": extra.price,
                                "subtotal": extra.subtotal,
                                "total_price": extra.total_price,
                                "discount": extra.discount,

                                "tax_ids":extra.tax_ids.ids,
                                
                                # "is_selected": note.product_id.is_selected
                            } for extra in line.product_extra_ids
                            
                        ],

                        


                        "note": line.note,
                    } for line in order.lines if line.is_show
                ],
                
                
            })


        # Response.status = "200"
        result = {  
                     "message": "Get All Orders",
                     "body" : order_list,
            
        

                        }
        
        return result



    @validate_token
    @http.route('/pos_custom/get_last_order', type='json', methods=['POST'], auth="none", csrf=False)
    def get_last_order(self,**kw):
        """ get All Orders"""

        data = kw

        pos_id = kw.get('pos_id',False)
        cahier_id = kw.get('cahier_id',False)
        order_status = kw.get('order_status',False)
        session_id = kw.get('session_id',False)
        
        
        domain = []

        #TODO:Need Refactoring
        if pos_id:
            
            config_id = request.env['pos.config'].sudo().search([('id','=',pos_id)])
            
            if not config_id:
                result = {  
                            "message":"Sorry Not Found any POS with Provided POS ID",
                        
                        }
                # Response.status = "401"
                return result

            domain.append(('config_id','=',pos_id))
        
        if session_id:
            
            session_id = request.env['pos.session'].sudo().search([('id','=',session_id)])
            
            if not session_id:
                result = {  
                            "message":"Sorry Not Found any POS Session with Provided POS ID",
                        
                        }
                # Response.status = "401"
                return result

            domain.append(('session_id','=',session_id.id))
        if cahier_id:
            user = request.env['res.users'].sudo().search([('id','=',cahier_id)])
            if not user:
                result = {  
                            "message":"Sorry Not Found any Cahier with Provided User ID",
                        
                        }
                # Response.status = "401"
                return result


            domain.append(('user_id','=',cahier_id))
        if order_status:
            domain.append(('state','in',order_status))
        
        pos_order_ids = request.env['pos.order'].sudo().search(domain,order='id desc',limit=1)
        
        if not pos_order_ids:
            result = {  
                        "message":"Sorry Not Found any POS Order",
                        "body": []
                    }
            # Response.status = "200"
            return result
        
        order_list = []
        pos_payment_obj = request.env['pos.payment'].sudo()
        for order in pos_order_ids:
            payment_methode = []
            totals = {}
            
            sub_total = sum([ line.price_subtotal for line in order.lines])
            vat = sum([ line.price_subtotal_incl - line.price_subtotal for line in order.lines])
            total = sub_total + vat

            totals.update({'sub_total':sub_total,'vat':vat,'total':total})
            pos_payments = pos_payment_obj.read_group([('pos_order_id','=',order.id)],['payment_method_id','payment_method_total:sum(amount)'],['payment_method_id'])
            
            payment_methods = [
                {"paymen_method":str(payment['payment_method_id'][1]),
                "payment_amount":payment['payment_method_total']} for payment in pos_payments
            ]
            
            totals.update({'payment_methods':payment_methods})

            for payment in order.payment_ids:
                payment_methode.append({
                    "payment_method_id": payment.payment_method_id.id,
                            "amount": payment.amount,
                            "payment_time": payment.payment_time,
                            "name_ar": payment.payment_method_id.arbic_name,
                            "name_en": payment.payment_method_id.name,
                })
            
            
            
            
            order_list.append({
                "configuration":{
                "order_id": order.id,
                "is_order_updated":order.is_order_updated,
                'notes': order.notes, 
                "order_no": order.pos_reference_custom,
                "order_ref": order.name_custom,
                "session_id": order.session_id.id,
                "branch_id": order.branch_id.id,
                "pos_id": order.config_id.id,
                "user_id": order.user_id.id,
                "order_type_id": order.order_type_id.id,#need check real place not default
                "d_o_number": order.d_o_number,
                "pricelist_id": order.pricelist_id.id,
                
                "coupon_id": order.coupon_id.id,
                "coupon_name": order.coupon_id.name,
                "discount_type_id":order.discount_type_id.id,
                
                "qr_code": order.qr_code,
                
                "customer_id": order.partner_id.id,
		        "customer_name": order.partner_id.name,
                "table_id": order.table_id.id,
                "table_name": order.table_id.name,
                "pos_name": order.config_id.name,
                "cashier_name": order.user_id.name,#need check , chshier or user
                "order_type_name": order.order_type_id.name,#need check real place not default
                "order_date": order.date_order,
                "status": order.state,
                "order_kitchen_state":order.order_kitchen_state,
                "return_to_wallet": order.return_to_wallet,  
                
                },
                # "code": "10",
                
                
                # 'amount_return': order_pricing.get('amount_return'),   
                "pricing":{
                "amount_subtotal": order.amount_subtotal,
                "amount_promotion": order.amount_promotion,
                "amount_coupon": order.amount_coupon,
                "amount_discount": order.amount_discount,
                "amount_wallet": order.amount_wallet,
                "amount_tax": order.amount_tax,
                "amount_total": order.amount_total,
                'amount_return': order.amount_return,
               
                
                # "amount_discount_total": order.amount_discount_total,
                # "amount_subtotal_discounted": order.amount_subtotal_discounted,
                # "amount_paid": order.amount_paid,
                                        
                # "is_show_customer_info": order.order_type_id.is_show_customer_info,
                # "is_require_information": order.order_type_id.is_require_information,
                # "is_require_driver": order.order_type_id.is_require_driver,
                # "is_auto_open_table_screen": order.order_type_id.is_auto_open_table_screen,
                # "delivary_product_id": order.order_type_id.delivary_product_id.id,
                                        
                # "note": order.note,
                # "extra_product_id": order.order_type_id.extra_product_id.id,
                # "extra_percentage": order.order_type_id.extra_percentage,
                # "company_id": order.company_id.id,
                # "company_name": order.company_id.name,
                # "vat": "465421",
                # "ret": "pos 15457-010",
                "payments":payment_methode,
                # "order_pricing": totals,
                },
                "items": [
                    {
                        "product_id": line.product_id.id,
                        'main_product_id': line.main_product_id.id,
                        "qty": line.qty,
                        "name_ar": line.name_ar,
                        "name_en": line.name_en,
                        "unit_price": line.price_unit,
                        
                        "subtotal": line.price_subtotal,
                        "total": line.price_subtotal_incl,
                        "discount": line.discount,
                        
                        "tax_ids": line.tax_ids_after_fiscal_position.ids,
                        "custom_note":line.custom_note,
                        "note_ids":line.product_note_ids.ids,
                        "status":line.status,
                        "is_send_to_kitchen":line.is_send_to_kitchen,
                        "item_kitchen_state":line.item_kitchen_state,
                        "prepare_time":line.product_id.preparation_time,
                        # "notes":[{
                        #         'id': note.id,
                        #         'name_en': note.name,
                        #         'name_ar': note.arbic_name,
                                
                        #     } for note in line.product_note_ids ],
                        # "vat": line.price_subtotal_incl - line.price_subtotal,
                        "addons": [
                            
                            {
                                "product_id": addons.product_id.id,
                                "qty": addons.qty,
                                        
                                # "title_id": addons.title_id.id,
                                # "title_ar": addons.title_id.arabic_name,
                                # "title_en": addons.title_id.name,
                                
                                #  "product_ids": [
                                #     {
                                #         "product_id": product.product_id.id,
                                #         "name_ar": product.product_id.other_lang_name,
                                #         "name_en": product.product_id.name,
                                #         "qty": product.qty,
                                #         "extra_price": product.extra_price,
                                        
                                #     } for product in addons.line_addons_ids
                                #     ]
                            } for addons in line.product_addons_ids
                            ],
                        "extras": [
                            {   
                                # "id": extra.id,
                                "product_id": extra.product_id.id,
                                "qty": extra.quantity,
                                "name_ar": extra.name_ar,
                                "name_en": extra.name_en,
                                "unit_price": extra.price,
                                "subtotal": extra.subtotal,
                                "total_price": extra.total_price,
                                "discount": extra.discount,

                                "tax_ids":extra.tax_ids.ids,
                                
                                # "is_selected": note.product_id.is_selected
                            } for extra in line.product_extra_ids
                            
                        ],

                        


                        "note": line.note,
                    } for line in order.lines if line.is_show
                ],
                
                
            })


        # Response.status = "200"
        result = {  
                     "message": "Get All Orders",
                     "body" : order_list,
            
        

                        }
        
        return result



    @validate_token
    @http.route('/pos_custom/get_order_search', type='json', methods=['POST'], auth="none", csrf=False)
    def get_order_search(self,**kw):
        """ get All Orders By Search"""

        
        pos_order_obj = request.env['pos.order']
        
        date_from = kw.get('date_from',False)
        date_to = kw.get('date_to',False)
        order_type_id = kw.get('order_type_id',False)
        order_id = kw.get('order_id',False)
        payment_method_id = kw.get('payment_method',False)
        customer_name = kw.get('customer_name',False)
        session_id = kw.get('session_id',False)
        cashier_name = kw.get('cashier_name',False)
        config_id = kw.get('pos_id',False)
        category_ids = kw.get('category_ids',False)

        multi_session_id = kw.get('multi_session_id',False)


        all_category_ids = request.env['pos.category'].sudo().search([]).ids

        if not category_ids:
            category_ids = all_category_ids
        
        
        domain = []

        
        if config_id:
            domain.append(('session_id.config_id','=',config_id))

        if date_from:
            domain.append(('date_order','>=',date_from))
        
        if date_to:
            domain.append(('date_order','<=',date_to))
            
        if order_type_id:
            domain.append(('order_type_id','=',order_type_id))
        
        if order_id:
            domain.append(('id','=',order_id))
        
        if customer_name:
            domain.append(('partner_id.name','ilike',customer_name))

        if session_id:
            domain.append(('session_id','=',session_id))

        if cashier_name:
            domain.append(('user_id.name','ilike',cashier_name))

        if multi_session_id:
            domain.append(('session_id.config_id.multi_session_id','=',multi_session_id))
        
        pos_order_ids = pos_order_obj.sudo().search(domain)
        
        
        order_list = []
        pos_payment_obj = request.env['pos.payment'].sudo()
        for order in pos_order_ids:
            
            if payment_method_id:
                if not order.payment_ids.filtered(lambda x: x.payment_method_id.id == payment_method_id):
                    continue
            payment_methode = []
            totals = {}
            
            sub_total = sum([ line.price_subtotal for line in order.lines])
            vat = sum([ line.price_subtotal_incl - line.price_subtotal for line in order.lines])
            total = sub_total + vat

            totals.update({'sub_total':sub_total,'vat':vat,'total':total})
            pos_payments = pos_payment_obj.read_group([('pos_order_id','=',order.id)],['payment_method_id','payment_method_total:sum(amount)'],['payment_method_id'])
            
            payment_methods = [
                {"paymen_method":str(payment['payment_method_id'][1]),
                "payment_amount":payment['payment_method_total']} for payment in pos_payments
            ]
            
            totals.update({'payment_methods':payment_methods})

            for payment in order.payment_ids:
                payment_methode.append({
                    "payment_method_id": payment.payment_method_id.id,
                            "amount": payment.amount,
                            "payment_time": payment.payment_time,
                            "name_ar": payment.payment_method_id.arbic_name,
                            "name_en": payment.payment_method_id.name,
                })
            
            
            kds_show = False
            for line in order.lines:
                 if (line.product_id.pos_categ_id.id in category_ids):
                     kds_show = True
            if not kds_show:
                continue
            order_list.append({
                "configuration":{
                "order_id": order.id,
                "is_order_updated":order.is_order_updated,
                
                'notes': order.notes, 
                "order_no": order.pos_reference_custom,
                "order_ref": order.name_custom,
                "session_id": order.session_id.id,
                "branch_id": order.branch_id.id,
                "pos_id": order.config_id.id,
                "user_id": order.user_id.id,
                "order_type_id": order.order_type_id.id,#need check real place not default
                "d_o_number": order.d_o_number,
                "pricelist_id": order.pricelist_id.id,
                
                "coupon_id": order.coupon_id.id,
                "coupon_name": order.coupon_id.name,
                "discount_type_id":order.discount_type_id.id,
                
                "qr_code": order.qr_code,
                
                "customer_id": order.partner_id.id,
		        "customer_name": order.partner_id.name,
                "table_id": order.table_id.id,
                "table_name": order.table_id.name,
                "pos_name": order.config_id.name,
                "cashier_name": order.user_id.name,#need check , chshier or user
                "order_type_name": order.order_type_id.name,#need check real place not default
                "order_date": order.date_order,
                "order_kitchen_state":order.order_kitchen_state,
                "return_to_wallet": order.return_to_wallet,
                'return_reason_id': order.return_reason_id.id,  
                'return_order_id' : order.return_order_id.id,  
                
                "status": order.state,
                },
                # "code": "10",
                
                
                "pricing":{
                "amount_subtotal": order.amount_subtotal,
                "amount_promotion": order.amount_promotion,
                "amount_coupon": order.amount_coupon,
                "amount_discount": order.amount_discount,
                "amount_wallet": order.amount_wallet,
                "amount_tax": order.amount_tax,
                "amount_total": order.amount_total,
                
                "payments":payment_methode,
                },
                "items": [
                    {
                        "product_id": line.product_id.id,
                        'main_product_id': line.main_product_id.id,
                        "prepare_time":line.product_id.preparation_time,
                        "category_id":line.product_id.pos_categ_id.id,
                        "qty": line.qty,
                        "name_ar": line.name_ar,
                        "name_en": line.name_en,
                        "unit_price": line.price_unit,
                        
                        "subtotal": line.price_subtotal,
                        "total": line.price_subtotal_incl,
                        "discount": line.discount,
                        
                        "tax_ids": line.tax_ids_after_fiscal_position.ids,
                        "custom_note":line.custom_note,
                        "note_ids":line.product_note_ids.ids,
                        "status":line.status,
                        "is_send_to_kitchen":line.is_send_to_kitchen,
                        "item_kitchen_state":line.item_kitchen_state,
                        "addons": [
                            
                            {
                                "product_id": addons.product_id.id,
                                "qty": addons.qty,
                                        
                            } for addons in line.product_addons_ids
                            ],
                        "extras": [
                            {   
                                "product_id": extra.product_id.id,
                                "qty": extra.quantity,
                                "name_ar": extra.name_ar,
                                "name_en": extra.name_en,
                                "unit_price": extra.price,
                                "subtotal": extra.subtotal,
                                "total_price": extra.total_price,
                                "discount": extra.discount,

                                "tax_ids":extra.tax_ids.ids,
                                
                            } for extra in line.product_extra_ids
                            
                        ],

                        


                        "custom_note": line.note,
                    } for line in order.lines if line.is_show and (line.product_id.pos_categ_id.id in category_ids)
                ],
                
                
            })


        # Response.status = "200"
        result = {  
                     "message": "Get All Orders By Search",
                     "body" : order_list,
            
        

                        }
        
        return result

    @validate_token
    @http.route('/pos_custom/get_all_qr_code', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_qr_code(self, pos_id):
        """ get order by status"""

        if not pos_id:
            # Response.status = "401"
            result = {  
                        "message":"POS ID not Provided",
                    }
            return result
        
        config_id = request.env['pos.config'].sudo().search([('id','=',pos_id)])

        if not config_id:
            # Response.status = "401"
            result = {  
                        "message":"POS ID not Found in Database",
                    }
            return result

        pos_order_ids = request.env['pos.order'].sudo().search([('config_id','=',pos_id)])
        
        if not pos_order_ids:
            result = {  
                        "message":"Sorry POS Order Related to POS ID Not Found",
                        "body": [],
                    }
            # Response.status = "200"
            return result
        
        order_list = []
        pos_payment_obj = request.env['pos.payment'].sudo()
        for order in pos_order_ids:
            
            totals = {}
            
            sub_total = sum([ line.price_subtotal for line in order.lines])
            vat = sum([ line.price_subtotal_incl - line.price_subtotal for line in order.lines])
            total = sub_total + vat

            totals.update({'sub_total':sub_total,'vat':vat,'total':total})
            pos_payments = pos_payment_obj.read_group([('pos_order_id','=',order.id)],['payment_method_id','payment_method_total:sum(amount)'],['payment_method_id'])
            
            payment_methods = [
                {"paymen_method":str(payment['payment_method_id'][1]),
                "payment_amount":payment['payment_method_total']} for payment in pos_payments
            ]
            
            totals.update({'payment_methods':payment_methods})
            
            
            
            
            order_list.append({
                "id": order.id,
                # "code": "10",
                "table_name": order.table_id.name,
                "date": order.date_order,
                "status": order.state,
                "total": order.amount_total,
                "is_show_customer_info": order.order_type_id.is_show_customer_info,
                "is_require_information": order.order_type_id.is_require_information,
                "is_require_driver": order.order_type_id.is_require_driver,
                "is_auto_open_table_screen": order.order_type_id.is_auto_open_table_screen,
                "pricelist_id": order.pricelist_id.id,
                "delivary_product_id": order.order_type_id.delivary_product_id.id,
                "extra_product_id": order.order_type_id.extra_product_id.id,
                "extra_percentage": order.order_type_id.extra_percentage,
                "company_id": order.company_id.id,
                "pos": order.config_id.name,
                # "vat": "465421",
                # "ret": "pos 15457-010",
                "cashier": order.cashier,#need check , chshier or user
                "order_type": order.order_type_id.type,#need check real place not default
                "note": order.note,
                "products": [
                    {
                        "id": line.product_id.id,
                        "name_ar": line.product_id.name_ar,
                        "name_en": line.product_id.name,
                        "qty": line.qty,
                        "price_of_one": line.price_unit,
                        "vat": line.price_subtotal_incl - line.price_subtotal,
                        "subtotal": line.price_subtotal,
                        "total_price": line.price_subtotal_incl,
                        "note": line.note,
                    } for line in order.lines
                ],
                "order_pricing": totals,
                "address":{
                    'state': order.partner_id.state_id.name,
                    'city': order.partner_id.city,
                    'street': order.partner_id.street,
                    'street2': order.partner_id.street2,
                    'zip': order.partner_id.zip,
                    'country': order.partner_id.country_id.name,
                },
                
                "qr_code": order.qr_code,
            })


        # Response.status = "200"
        result = {  
                     "message": "Get All QR Orders",
                     "body" : order_list,
            
        

                        }
        
        return result



    @validate_token
    @http.route('/pos_custom/set_order_transfere', type='json', methods=['POST'], auth="none", csrf=False)
    def set_order_transfere(self,order_id,table_id,floor_id):
        """ Transfere Order Table"""
        
        if not order_id:
            result = {  
                        "message":"Sorry Order ID Not Provided",
                    }
            # Response.status = "401"
            return result

        if not table_id:
            result = {  
                        "message":"Sorry Table ID Not Provided",
                    }
            # Response.status = "401"
            return result

        if not floor_id:
            result = {  
                        "message":"Sorry Floor ID Not Provided",
                    }
            # Response.status = "401"
            return result

        order_id = request.env['pos.order'].sudo().search([('id','=',order_id)])
        

        if not order_id:
            result = {  
                        "message":"Sorry POS Order With Provided ID Not Found",
                    }
            # Response.status = "401"
            return result
        
        table_id = request.env['restaurant.table'].sudo().search([('id','=',table_id)])

        if not table_id:
            result = {  
                        "message":"Sorry Table With Provided ID Not Found",
                    }
            # Response.status = "401"
            return result

        order_id.table_id = table_id


        # Response.status = "200"
        result = {  
                    "message": "Order Transfered To Table Successfully",

            
        

                        }
        return result




    @validate_token
    @http.route('/pos_custom/get_all_promotion', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_promotion(self,):
        """ get all promotion available"""
        
        promotion_ids = request.env['pos.promotion'].sudo().search([])
        
        if not promotion_ids:
            result = {  
                        "message":"Sorry Promotion Not Found in the System",
                    }
            # Response.status = "401"
            return result
        
        promotion_list = []
        for promotion in promotion_ids:

            promotion_list.append({
                 "id": promotion.id,
                "name_en": promotion.name,
                "name_ar": promotion.name_ar,
                "type": promotion.type ,  # get in full name or just code.

               
                })

        # Response.status = "200"
        result = {  
                    "message": "Get All Promotion Successfully",

                     "body" : promotion_list
            
        

                        }
        return result
    
    @validate_token
    @http.route('/pos_custom/get_promotion', type='json', methods=['POST'], auth="none", csrf=False)
    def get_promotion(self,promotion_id):
        """ get promotion by id"""

        if not promotion_id:
            # Response.status = "401"
            result = {  
                        "message":"Promotion ID not Provided",
                    }
            return result        
        promotion_id = request.env['pos.promotion'].sudo().search([('id','=',promotion_id)])
        
        if not promotion_id:
            result = {  
                        "message":"Sorry Promotion Not Found in the System",
                        
                    }
            # Response.status = "401"
            return result
        special_time = []
        if promotion_id.special_times:
            if promotion_id.from_time:
                special_time.append(str(  '{0:02.0f}:{1:02.0f}'.format(*divmod(promotion_id.from_time * 60, 60))))
            
            if promotion_id.from_time:
                special_time.append(str(  '{0:02.0f}:{1:02.0f}'.format(*divmod(promotion_id.to_time * 60, 60))))
            

        
        special_day = []
        if promotion_id.special_days:
            if promotion_id.monday:
                special_day.append("monday")
            if promotion_id.tuesday:
                special_day.append("tuesday")
            if promotion_id.wednesday:
                special_day.append("wednesday")
            if promotion_id.thursday:
                special_day.append("thursday")
            if promotion_id.friday:
                special_day.append("friday")
            if promotion_id.saturday:
                special_day.append("saturday")
            if promotion_id.sunday:
                special_day.append("sunday")
        
        
        promotion_list = {
            "id": promotion_id.id,
            "name_en": promotion_id.name,
            "name_ar": promotion_id.name_ar,
            "start_date": promotion_id.start_date,
            "end_date": promotion_id.end_date,
            "amount_total": promotion_id.amount_total,
            "type": promotion_id.type ,
            "method": promotion_id.method,
            "discount_first_order": promotion_id.discount_first_order,
            "product_id": promotion_id.product_id.id,
            "special_times":special_time,
            "special_day":special_day,
            "discount_category_ids": [
                {
                    "id": discount_category_id.id,
                    "category_id": discount_category_id.category_id.id,
                    "category_name": discount_category_id.category_id.name,
                    "discount": discount_category_id.discount,
                    "promotion_id": discount_category_id.promotion_id.id,
                }  for discount_category_id in promotion_id.discount_category_ids
            ],
            "minimum_items": promotion_id.minimum_items,
            "special_customer_ids": [
                customer.id for customer in promotion_id.special_customer_ids 
            ],
            "branch_id": promotion_id.branch_id.id

               
                }

        # Response.status = "200"
        result = {  
                    "message": "Get Promotion Successfully",

                     "body" : promotion_list
            
        

                        }
        
        return result




    @validate_token
    @http.route('/pos_custom/create_printer', type='json', methods=['POST'], auth="none", csrf=False)
    def create_printer(self,**kw):
        """ Create Printer"""
        #add use_type in create
        device_name = kw.get('device_name',False)
        
        ip = kw.get('ip',False)
        pos_ids = kw.get('pos_id',False)
        use_type = kw.get('use_type',False) #	cashier , kitchen
        if use_type and use_type not in ['cashier','kitchen']:
            # Response.status = "401"
            result = {  
                        "message":"Sorry use type must be cashier or kitchen",
                    }
            return result 
        if not device_name:
            # Response.status = "401"
            result = {  
                        "message":"Sorry Printer Name not Provided",
                    }
            return result  

        if not ip:
            # Response.status = "401"
            result = {  
                        "message":"Sorry IP not Provided",
                    }
            return result  
        printer_id = request.env['restaurant.printer'].sudo().create(
            {
                'name':device_name,
                'proxy_ip':ip,
                'use_type':use_type,
            }
            )
        
        if pos_ids:
            
            pos_check = request.env['pos.config'].sudo().search([('id', 'in', pos_ids)])
            if not pos_check:
                result = { 
                            "message":"Invalid POS Not Found any.", 
                            }
                # Response.status = "403"  
                return result
            
            printer_id.pos_config_ids = pos_check.ids
        
        
        # Response.status = "200"
        result = {  
                      "message": "Created Device Successfully"

        

                        }
        return result

    


    @validate_token
    @http.route('/pos_custom/get_all_printer', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_printer(self,  **kw):
        """ get all Printer available by pos id"""
        printer_ids = request.env['restaurant.printer'].sudo()
        exist_printer_ids = printer_ids.search([('pos_config_ids', 'in', kw.get('pos_id'))])        
        if not exist_printer_ids:
            result = {  
                        "message":"Sorry Printers Not Found in the System",
                    }
            # Response.status = "401"
            return result
        printer_list = []
        for printer in exist_printer_ids:
            printer_list.append({
                                "id": printer.id,
                                "name": printer.name,
                                "ip":printer.proxy_ip,
                                "printer_type": printer.printer_type, 
                                "use":printer.use_type,
                                'default_printer': printer.default_printer,
                                "main_printer":printer.main_printer,
                                'specific_categories':
                                    [
                                        product_categories.id for product_categories in printer.product_categories_ids
                                    ],                 
                                })
        # Response.status = "200"
        result = {  
                    "message": "Get All Printers Successfully",
                    "body" : printer_list
                    }
        return result



    @validate_token
    @http.route('/pos_custom/update_printer', type='json', methods=['POST'], auth="none", csrf=False)
    def update_printer(self,  **kw):
        """ update Printer available by pos id"""
        printer_ids = request.env['restaurant.printer'].sudo()


        printer_id = kw.get('printer_id',False)

        if not printer_id:
            result = {  
                        "message":"Sorry Printer ID Not Provided",
                    }
            # Response.status = "401"
            return result


        printer_id = printer_ids.search([('id', '=', printer_id)])        
        if not printer_id:
            result = {  
                        "message":"Sorry Printers Not Found in the System",
                    }
            # Response.status = "401"
            return result

        
        name = kw.get('name',False)
        proxy_ip = kw.get('ip',False)
        printer_type = kw.get('printer_type',False)
        use_type = kw.get('use_type',False)
        default_printer = kw.get('default_printer',False)
        main_printer = kw.get('main_printer',False)


        update_data = {}

        if name:
            update_data.update(name=name)
        if proxy_ip:
            update_data.update(proxy_ip=proxy_ip)
        if printer_type:
            update_data.update(printer_type=printer_type)
        if use_type:
            update_data.update(name=use_type)
        if default_printer:
            update_data.update(default_printer=default_printer)
        if main_printer:
            update_data.update(name=main_printer)
        
        printer_id.write(update_data)


        
        # Response.status = "200"
        result = {  
                    "message": "Printer Updated Successfully",
                   
                    }
        return result





    @validate_token
    @http.route('/pos_custom/create_device', type='json', methods=['POST'], auth="none", csrf=False)
    def create_device(self,device_name,ip):
        """ Create Device"""

        if not device_name:
            # Response.status = "401"
            result = {  
                        "message":"Sorry Device Name not Provided",
                    }
            return result  

        if not ip:
            # Response.status = "401"
            result = {  
                        "message":"Sorry IP not Provided",
                    }
            return result  
        device_id = request.env['pos.device'].sudo().create(
            {
                'name':device_name,
                'proxy_ip':ip
            }
            )
        
        
        
        # Response.status = "200"
        result = {  
                      "message": "Device Created Successfully"

        

                        }
        return result

    


    @validate_token
    @http.route('/pos_custom/get_all_payment_device', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_payment_device(self,):
        """ get all Payment Device available"""
        
        device_ids = request.env['pos.device'].sudo().search([])
        
        if not device_ids:
            result = {  
                        "message":"Sorry Devices Not Found in the System",
                    }
            # Response.status = "401"
            return result
        
        device_list = []
        for device in device_ids:

            device_list.append({
                 "id": device.id,
                "name": device.name,
                "ip":device.proxy_ip,
                "pos_id":device.pos_id.id,
                

               
                })

        # Response.status = "200"
        result = {  
                    "message": "Get All Payment Device",

                     "body" : device_list
            
        

                        }
        return result


    # {{baseurl}}


    @validate_token
    @http.route('/pos_custom/delete_order', type='json', methods=['POST'], auth="none", csrf=False)
    def delete_order(self,order_ids):
        """ Delete Orders"""
        pos_order_obj = request.env['pos.order'].sudo()

        for order_id in order_ids:
            if not order_id:
                result = {  
                            "message":"Sorry Order ID Not Provided",
                        }
                # Response.status = "401"
                return result

            order_id = pos_order_obj.search([('id','=',order_id)])
            

            if not order_id:
                result = {  
                            "message":"Sorry POS Order With Provided ID Not Found",
                        }
                # Response.status = "401"
                return result

            if  order_id.state not in ['draft']:
                result = {  
                            "message":"Sorry you can't delete order not in Draft State",
                        }
                # Response.status = "401"
                return result

            payments = request.env['pos.payment'].sudo().search([('pos_order_id','=',order_id.id)])
            if payments:
                payments.unlink()
            order_id.with_context(force_delete=True).unlink()
        

        # Response.status = "200"
        result = {  
                     "message": "Order is deleted successfully"
                        }
        return result


    @validate_token
    @http.route('/pos_custom/send_order_to_kitchen', type='json', methods=['POST'], auth="none", csrf=False)
    def send_order_to_kitchen(self,order_id):
        """ Transfere Order To Kitchen"""
        
        if not order_id:
            result = {  
                        "message":"Sorry Order ID Not Provided",
                    }
            # Response.status = "401"
            return result

        order_id = request.env['pos.order'].sudo().search([('id','=',order_id)])
        

        if not order_id:
            result = {  
                        "message":"Sorry POS Order With Provided ID Not Found",
                    }
            # Response.status = "401"
            return result

        order_id.state = 'send_to_kitchen'

        # order_id.order_kitchen_state = 'new'

        # for line in order_id.lines:
        #     line.item_kitchen_state = 'new'

        # Response.status = "200"
        result = {  
                     "message": "Order is sent to the kitchen"
                        }
        return result

    @validate_token
    @http.route('/pos_custom/create_customer', type='json', methods=['POST'], auth="none", csrf=False)
    def create_customer(self,**kw):
        """ API to Create New Customer"""
        

        name = kw.get('name',False)
        mobile = kw.get('mobile',False)
        if not name:
            result = {  
                        "message":"Sorry No Customer Name",
                    }
            # Response.status = "401"
            return result
        
        partner_obj = request.env['res.partner'].sudo()
        
        

        data = {'name':name,'customer_rank':1,'is_company':True}
        if mobile:
            partner_check_mobile = partner_obj.search([('mobile','=',mobile)])
        
            if partner_check_mobile:
                result = {  
                            "message":"Sorry Mobile Number Already Found",
                        }
                # Response.status = "401"
                return result


            data.update(mobile=mobile)

        
        customer_id = partner_obj.with_context(
            {'search_default_customer': 1,
            'res_partner_search_mode': 'customer',
             'default_is_company': True,
              'default_customer_rank': 1}).create(data)
        

        # Response.status = "200"
        result = {  
                "message": "Add Customer Successful",
                
                "body": {
                "id": customer_id.id,
                "name": customer_id.name,
                "mobile": customer_id.mobile,
                'wallet_balance': customer_id.wallet_balance,
            }    
        }

                        
        return result


    @validate_token
    @http.route('/pos_custom/create_payment', type='json', methods=['POST'], auth="none", csrf=False)
    def create_payment(self,order_id,payment):
        """ API to Create New Payment for Order"""
        
        if not order_id:
            result = {  
                        "message":"Sorry Order ID Not Provided",
                    }
            # Response.status = "401"
            return result
        
        
        if not payment.get('payment_methods',False):
            result = {  
                        "message":"Sorry Payment Methods Not Provided",
                    }
            # Response.status = "401"
            return result

        if not payment['payment_methods']:
            result = {  
                        "message":"Sorry Payment Details Not Provided",
                    }
            # Response.status = "401"
            return result
        
        pos_order_id = request.env['pos.order'].sudo().search([('id','=',order_id)])

        
        if not pos_order_id:
            result = {  
                        "message":"Sorry Order ID Not Found",
                    }
            # Response.status = "401"
            return result
        
        if  pos_order_id.state in ['paid','invoiced','cancel']:
            result = {  
                        "message":"Sorry You can't pay if Order State in Paid , Invoiced or Cancel",
                    }
            # Response.status = "401"
            return result
        
        for pay in payment['payment_methods']:

            payment_vals = {
                    'name': ('Payment'),
                    'pos_order_id': pos_order_id.id,
                    'amount': pay['payment_amount'],
                    'payment_date': fields.Datetime.now(),
                    'payment_method_id': pay['paymen_method'],
                    'session_id':pos_order_id.session_id.id,
                    
                }
            pos_order_id.add_payment(payment_vals)


        # Response.status = "200"
        result = {  
                "message": "Payment completed successfully",
        }

                        
        return result


    @validate_token
    @http.route('/pos_custom/check_coupon_validity', type='json', methods=['POST'], auth="none", csrf=False)
    def check_coupon_validity(self, **kw):
        """ Check the validity of the coupon."""
        coupon_barcode = kw.get('coupon_barcode',False)
        pos_id = kw.get('pos_id',False)

        if not coupon_barcode:
            result = {  
                        "message":"Sorry Coupon Barcode Not Provided",
                    }
            # Response.status = "401"
            return result
        
        if not pos_id:
            result = {  
                        "message":"Sorry POS ID Not Provided",
                    }
            # Response.status = "401"
            return result


        pos_gift_coupon_obj = request.env['pos.gift.coupon'].sudo()
        pos_gift_coupon_records = pos_gift_coupon_obj.search(
            [('c_barcode', '=', coupon_barcode),
            ('applied_pos_ids','in',[pos_id,])
            
            ],limit=1)
        result = []
        if pos_gift_coupon_records:
            gift_coupon = pos_gift_coupon_records
            remain_count = gift_coupon.coupon_apply_times - len(gift_coupon.order_ids)
            
            valid = True
            
            if (remain_count <= 0):
                valid = False
            
            if (gift_coupon.exp_dat_show and fields.Date.today() > gift_coupon.expiry_date.date() ):
                valid = False
            
            
            # result += [{
            #     'active': gift_coupon.active,
            #     'coupon_allow_times': gift_coupon.coupon_apply_times,
            #     'coupon_applied_times': len(gift_coupon.order_ids),
            #     'expiry_date': gift_coupon.expiry_date.date(),
            #     'valid': valid,
            # }]
            if valid:
                message = "The coupon is Found and valid"
            else:
                message = "The coupon is Found but no valid"
            amount_type = 'amount' if  gift_coupon.amount_type == 'fix' else 'percentage'
            amount = gift_coupon.amount
            result =  {
                    "message": message,
                    "body": {
                        "coupon_id": gift_coupon.id,
                        "customer_id":gift_coupon.partner_id.id,
                        "coupon_name": gift_coupon.name,
                        "valid": valid,
                        "discount": {
                            "type": amount_type,
                            "value": amount,
                            "max_amount":gift_coupon.max_amount,
                        }
                    }
           
                }
            
            # Response.status = "200"
        else:
            # Response.status = "404"
            result = {
                        'message': "Coupon Not Found or not Found in POS" + coupon_barcode,
                    }
        return result











    @validate_token
    @http.route('/pos_custom/get_product_waste_report', type='json', methods=['POST'], auth="none", csrf=False)
    def get_product_waste_report(self,pos_id,start_date,end_date):
        """Get Product Waste Report"""

        
        
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
            
        if not start_date:
            result = {  
                        "message":"Start Date not Provided",
                    }
            # Response.status = "401"
            return result

        domain = [('pos_session_id','=',pos_id),  ('state','=','done')]

        if start_date:
            domain.append(('date_done','>=',start_date))
            # pos_order_domain.append(('session_id.start_at','>=',start_date))
        
        if end_date:
            domain.append(('date_done','<=',end_date))
            # pos_order_domain.append(('session_id.stop_at','<=',end_date))


        order_list = []
        stock_scrap_obj = request.env['stock.scrap'].sudo()
        stock_scraps_categ = stock_scrap_obj.read_group(domain,['pos_categ_id','qty_total:sum(scrap_qty)'],['pos_categ_id'])
        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>stock_scraps_categ ",stock_scraps_categ)

        categories = []
        grand_totals = 0
        for stock_scrap_categ in stock_scraps_categ:
            scrap_categ_domain = domain
            scrap_categ_domain.append(('pos_categ_id','=',stock_scrap_categ['pos_categ_id'][0]))
            stock_scraps = stock_scrap_obj.read_group(scrap_categ_domain,['product_id','list_price','pos_categ_id','qty_total:sum(scrap_qty)'],['product_id',])
            
            items = []
            total = 0
            for stock_scrap in stock_scraps:
                price_total = stock_scrap['list_price'] * stock_scrap['qty_total']
                total = total + price_total
                items.append(  {
                            "product_name": stock_scrap['product_id'][1],
                            "product_price": price_total,
                            "product_qty": stock_scrap['qty_total']
                        })
            grand_totals = grand_totals + total
            categories.append({
                "name": stock_scrap_categ['pos_categ_id'][1],
                    "total": total,
                    "qty": stock_scrap_categ['qty_total'],
                    "items":items
            })


        # Response.status = "200"
        result = {  
                   "message": "Get Product waste Successfully",
                     "body" : {
            "title_ar": "المنتجات الهالكة",
            "title_en": "Product waste",
            "pos_name": check_pos_id.name,

            "start_time": start_date,
            "end_time": end_date,
            
            # "total_orders": 4,
            "total": grand_totals,

            "categories":categories,
                    
                     },
            "printed_by": request.env.user.name,
            "printed_at": str(datetime.now()) 
            
         }
        return result



    @validate_token
    @http.route('/pos_custom/get_product_return_report', type='json', methods=['POST'], auth="none", csrf=False)
    def get_product_return_report(self,pos_id,start_date,end_date):
        """Get Product Return Report"""

        
        
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
            
        if not start_date:
            result = {  
                        "message":"Start Date not Provided",
                    }
            # Response.status = "401"
            return result

        domain = [('order_id.config_id','=',pos_id),('qty','<',0),('pos_categ_id','!=',False)]

        if start_date:
            domain.append(('order_id.date_order','>=',start_date))
            # pos_order_domain.append(('session_id.start_at','>=',start_date))
        
        if end_date:
            domain.append(('order_id.date_order','<=',end_date))
            # pos_order_domain.append(('session_id.stop_at','<=',end_date))


        order_list = []
        pos_order_line_obj = request.env['pos.order.line'].sudo()
        pos_order_lines_categ = pos_order_line_obj.read_group(domain,['pos_categ_id','qty_total:sum(qty)'],['pos_categ_id'])
       
        pos_order_lines_orders = pos_order_line_obj.read_group(domain,['order_id'],['order_id'])
        
        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>pos_order_lines_categ ",pos_order_lines_categ)

        categories = []
        grand_totals = 0
        for pos_order_line_categ in pos_order_lines_categ:
            order_line_categ_domain = domain
            order_line_categ_domain.append(('pos_categ_id','=',pos_order_line_categ['pos_categ_id'][0]))
            pos_order_lines = pos_order_line_obj.read_group(order_line_categ_domain,['product_id','list_price','pos_categ_id','qty_total:sum(qty)'],['product_id',])
            
            items = []
            total = 0
            for pos_order_line in pos_order_lines:
                price_total = pos_order_line['list_price'] * pos_order_line['qty_total']
                total = total + price_total
                items.append(  {
                            "product_name": str(pos_order_line['product_id'][1]),
                            "product_price": price_total,
                            "product_qty": pos_order_line['qty_total']
                        })
            grand_totals = grand_totals + total
            categories.append({
                "name": str(pos_order_line_categ['pos_categ_id'][1]),
                    "total": total,
                    "qty": pos_order_line_categ['qty_total'],
                    "items":items
            })


        # Response.status = "200"
        result = {  
                   "message": "Get Product Return Successfully",
                     "body" : {
            "title_ar": "المنتجات الراجعة",
            "title_en": "Product Return",
            "pos_name": check_pos_id.name,

            "start_time": "2022-06-29T04:58:27.953Z",
            "end_time": "2022-06-29T04:58:27.953Z",
            
            "total_orders": len(pos_order_lines_orders),
            "total": grand_totals,

            "categories":categories,
                    
                     },
            "printed_by": request.env.user.name,
            "printed_at": str(datetime.now()) 
            
        }
        
        return result










    @validate_token
    @http.route('/pos_custom/get_config_stock_report', type='json', methods=['POST'], auth="none", csrf=False)
    def get_config_stock_report(self,pos_id,product_ids):
        """Get POS Config Stock Reports"""

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
            
        location_id = check_pos_id.picking_type_id.default_location_src_id.id
        domain = [('location_id','=',location_id),]
        # picking_type_id.default_location_src_id
        
        if product_ids:
            domain.append(('product_id','in',product_ids))
        


        order_list = []
        stock_quant_obj = request.env['stock.quant'].sudo()
        
        products = stock_quant_obj.read_group(domain,['product_id','product_uom_id','quantity_total:sum(quantity)'],['product_id','product_uom_id'])
        
        products_data = []
        product_obj = request.env['product.product'].sudo()
        for product in products:
            product_id = product_obj.browse(product['product_id'][0])
            products_data.append( {
                    "code": product_id.default_code,
                    "name":product_id.name, # str(product['product_id'][1]),
                    "qty": product['quantity_total'],
                    "unit": product_id.uom_id.name,
            })
           
        # Response.status = "200"
        result = {  
                   "message": "Get Stock report Successfully",
                     "body" : {
            "title_ar": "الأصناف المتواجدة في المخزن",
            "title_en": "POS Stock Report",
            "pos_name": check_pos_id.name,
            "time": str(datetime.now()),

            "products":products_data,
                    
                     },
            "printed_by": request.env.user.name,
            "printed_at": str(datetime.now()) 
            
         }
        
        
        return result



    @validate_token
    @http.route('/pos_custom/get_session_report', type='json', methods=['POST'], auth="none", csrf=False)
    def get_session_report(self,pos_id,pos_session_ids,start_date,end_date):
        """Get sessions report  """
        if not pos_id:
            result = {  
                        "message":"POS Session ID not Provided",
                    }
            # Response.status = "401"
            return result

            

        
        pos_id = request.env['pos.config'].sudo().search([('id','=',pos_id)])
         
        if not pos_id:
            result = {  
                        "message":"POS ID not Found",
                    }
            # Response.status = "401"
            return result



        domain = [('config_id','=',pos_id.id)]

        if start_date:
            domain.append(('start_at','>=',start_date))
            # pos_order_domain.append(('session_id.start_at','>=',start_date))
        
        if end_date:
            domain.append(('stop_at','<=',end_date))
            # pos_order_domain.append(('session_id.stop_at','<=',end_date))

        if pos_session_ids:
            domain.append(('id','in',pos_session_ids))
            # pos_order_domain.append(('session_id.stop_at','<=',end_date))



        
        pos_session_ids = request.env['pos.session'].sudo().search(domain)
         
        

        # Response.status = "200"
        result = {  
                  "message": "Get sessions Successfully",
            "body": {
                "id": pos_id.id,
                "title_ar": "Sessions Reports",
                "title_en": "تقرير الجلسات",
                "pos_name": pos_id.name,
                "start_time": start_date,
                "end_time": end_date,
                "sessions":[
                {
                "id": pos_session_id.id,
                "name_en": pos_session_id.name,
                "start_time": str(pos_session_id.start_at),
                "end_time": str(pos_session_id.stop_at),
                "cash_in": pos_session_id.cash_register_balance_start,
                "cash_out": pos_session_id.cash_register_balance_end_real,
                "status": pos_session_id.state,
           } for pos_session_id in pos_session_ids
           ]
            }

            
        }
        
        return result




    @validate_token
    @http.route('/pos_custom/get_mixed_products_report', type='json', methods=['POST'], auth="none", csrf=False)
    def get_mixed_products_report(self,pos_id,start_date,end_date,):
        """mixed products reports """

        
        
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
            
        if not start_date:
            result = {  
                        "message":"Start Date not Provided",
                    }
            # Response.status = "401"
            return result

        domain = [('order_id.config_id','=',pos_id),('pos_categ_id','!=',False)]

        if start_date:
            domain.append(('order_id.date_order','>=',start_date))
            # pos_order_domain.append(('session_id.start_at','>=',start_date))
        
        if end_date:
            domain.append(('order_id.date_order','<=',end_date))
            # pos_order_domain.append(('session_id.stop_at','<=',end_date))


        order_list = []
        pos_order_line_obj = request.env['pos.order.line'].sudo()
        pos_order_lines_categ = pos_order_line_obj.read_group(domain,['pos_categ_id','qty_total:sum(qty)'],['pos_categ_id'])
       
        pos_order_lines_orders = pos_order_line_obj.read_group(domain,['order_id'],['order_id'])
        
        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>pos_order_lines_categ ",pos_order_lines_categ)

        categories = []
        grand_totals = 0
        for pos_order_line_categ in pos_order_lines_categ:
            order_line_categ_domain = domain
            order_line_categ_domain.append(('pos_categ_id','=',pos_order_line_categ['pos_categ_id'][0]))
            pos_order_lines = pos_order_line_obj.read_group(order_line_categ_domain,['product_id','list_price','pos_categ_id','qty_total:sum(qty)'],['product_id',])
            
            items = []
            total = 0
            for pos_order_line in pos_order_lines:
                price_total = pos_order_line['list_price'] * pos_order_line['qty_total']
                total = total + price_total
                items.append(  {
                            "product_name": str(pos_order_line['product_id'][1]),
                            "product_price": price_total,
                            "product_qty": pos_order_line['qty_total']
                        })
            grand_totals = grand_totals + total
            categories.append({
                "name": str(pos_order_line_categ['pos_categ_id'][1]),
                    "total": total,
                    "qty": pos_order_line_categ['qty_total'],
                    "items":items
            })

        pos_order_lines = pos_order_line_obj.search(domain)
        discount = sum([ ( (pos_order_line.qty * pos_order_line.price_unit) * (pos_order_line.discount / 100) ) if  pos_order_line.discount else 0  for pos_order_line in pos_order_lines])
       
        # Response.status = "200"
        result = {  
                   "message": "Get Mixed Products Successfully",
                     "body" : {
            "title_ar": "المنتجات المختلطة",
            "title_en": "Mixed Products",
            "pos_name": check_pos_id.name,

            "start_time": start_date,
            "end_time": end_date,
            
            "total_orders": len(pos_order_lines_orders),
            "total": grand_totals,
            "discount": discount,
            "net_total": grand_totals - discount,

            "categories":categories,
                    
                     },
            "printed_by": request.env.user.name,
            "printed_at": str(datetime.now()) 
            
        }
        
        return result




    @validate_token
    @http.route('/pos_custom/get_product_category_report', type='json', methods=['POST'], auth="none", csrf=False)
    def get_product_category_report(self,pos_id,start_date,end_date,):
        """get product category report """

        
        
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
            
        if not start_date:
            result = {  
                        "message":"Start Date not Provided",
                    }
            # Response.status = "401"
            return result

        domain = [('order_id.config_id','=',pos_id),('pos_categ_id','!=',False)]

        if start_date:
            domain.append(('order_id.date_order','>=',start_date))
            # pos_order_domain.append(('session_id.start_at','>=',start_date))
        
        if end_date:
            domain.append(('order_id.date_order','<=',end_date))
            # pos_order_domain.append(('session_id.stop_at','<=',end_date))


        order_list = []
        pos_order_line_obj = request.env['pos.order.line'].sudo()
        pos_order_lines_categ = pos_order_line_obj.read_group(domain,['pos_categ_id','qty_total:sum(qty)'],['pos_categ_id'])
       
        pos_order_lines_orders = pos_order_line_obj.read_group(domain,['order_id'],['order_id'])
        
        
        categories = []
        grand_totals = 0
        for pos_order_line_categ in pos_order_lines_categ:
            order_line_categ_domain = domain
            order_line_categ_domain.append(('pos_categ_id','=',pos_order_line_categ['pos_categ_id'][0]))
            pos_order_lines = pos_order_line_obj.read_group(order_line_categ_domain,['product_id','list_price','pos_categ_id','qty_total:sum(qty)'],['product_id',])
            
            items = []
            total = 0
            for pos_order_line in pos_order_lines:
                price_total = pos_order_line['list_price'] * pos_order_line['qty_total']
                total = total + price_total
                items.append(  {
                            "product_name": str(pos_order_line['product_id'][1]),
                            "product_price": price_total,
                            "product_qty": pos_order_line['qty_total']
                        })
            grand_totals = grand_totals + total
            categories.append({
                "name": str(pos_order_line_categ['pos_categ_id'][1]),
                    "total": total,
                    "qty": pos_order_line_categ['qty_total'],
                    # "items":items
            })

        for category in categories:
            category.update(percentage=(str(((total/grand_totals) * 100)) + '%') if grand_totals != 0 else '0%')
        pos_order_lines = pos_order_line_obj.search(domain)
        # discount = sum([ ( (pos_order_line.qty * pos_order_line.price_unit) * (pos_order_line.discount / 100) ) if  pos_order_line.discount else 0  for pos_order_line in pos_order_lines])
        discount = sum([ pos_order_line.price_subtotal_incl if  pos_order_line.product_id.id == pos_order_line.order_id.discount_type_id.discount_program_product_id.id else 0  for pos_order_line in pos_order_lines])
       
        # Response.status = "200"
        result = {  
                   "message": "By Categories Summary",
                     "body" : {
            "title_ar": "ملخص الأقسام",
            "title_en": "By Categories Summary",
            "pos_name": check_pos_id.name,

            "start_time": start_date,
            "end_time": end_date,
            
            "total_orders": len(pos_order_lines_orders),
            "total": grand_totals,
            "discount": discount,
            "net_total": grand_totals - discount,

            "categories":categories,
                    
                     },
            "printed_by": request.env.user.name,
            "printed_at": str(datetime.now()) 
            
        }
        
        return result



    @validate_token
    @http.route('/pos_custom/get_discount_category_report', type='json', methods=['POST'], auth="none", csrf=False)
    def get_discount_category_report(self,pos_id,start_date,end_date,):
        """get discount category report """   
        
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
            
        if not start_date:
            result = {  
                        "message":"Start Date not Provided",
                    }
            # Response.status = "401"
            return result

        domain = [('config_id','=',pos_id),('discount_type_id','!=',False)]

        if start_date:
            domain.append(('date_order','>=',start_date))
            # pos_order_domain.append(('session_id.start_at','>=',start_date))
        
        if end_date:
            domain.append(('date_order','<=',end_date))
            # pos_order_domain.append(('session_id.stop_at','<=',end_date))


        order_list = []
        pos_order_obj = request.env['pos.order'].sudo()
        pos_order_obj.search(domain)._get_discount_program_total()
        pos_order_discounts = pos_order_obj.read_group(domain,['discount_type_id','discount_total:sum(discount_type_total)','discount_qty:sum(discount_type_qty)'],['discount_type_id'])
       
        

        discounts = []
        grand_totals = 0
        for pos_order_discount in pos_order_discounts:
            
            total = pos_order_discount['discount_total']
            
            grand_totals = grand_totals + total
            discounts.append({
                "name": str(pos_order_discount['discount_type_id'][1]),
                "amount": pos_order_discount['discount_total'],
                "quantity": pos_order_discount['discount_qty'],
                # "items":items
            })

        for discount in discounts:
            discount.update(percentage=(str(((discount['amount']/grand_totals) * 100)) + '%') if grand_totals != 0 else '0%')
        
        # Response.status = "200"
        result = {  
                   "message": "Discount Summary",
                     "body" : {
            "id": check_pos_id.id,
            "title_ar": "Discount Summary",
            "title_en": "ملخص الخصومات",
            "pos_name": check_pos_id.name,

            "start_time": start_date,
            "end_time": end_date,
            "total":grand_totals,
            
            

            "items":discounts,
            
                    
                     },
            # "printed_by": request.env.user.name,
            # "printed_at": str(datetime.now()) 
            
        }
        return result
        

    @validate_token
    @http.route('/pos_custom/get_last_pos_session_report', type='json', methods=['POST'], auth="none", csrf=False)
    def get_last_pos_session_report(self,pos_id,):
        """Get Last Pos Session report  """

        if not pos_id:
            result = {  
                        "message":"POS ID not Provided",
                    }
            # Response.status = "401"
            return result

            

        
        pos_id = request.env['pos.config'].sudo().search([('id','=',pos_id)])
         
        if not pos_id:
            result = {  
                        "message":"POS ID not Found",
                    }
            # Response.status = "401"
            return result


        pos_session_id = request.env['pos.session'].sudo().search([('config_id','=',pos_id.id)],order="id desc",limit=1)

        if not pos_session_id:
            result = {  
                        "message":"POS Session not Found",
                        "body":[]
                    }

                    
            # Response.status = "200"
            return result
            
        session_report = []
        payment_type = []
        order_type = []
        order_payment_type = []

        payment_type_total = 0  
        order_type_total = 0    

        total_taxes = 0  
        total_amount_with_taxes = 0  
        total_amount_without_taxes = 0  
        deleted_products_total = 0
        return_total = 0
        total_order_rejected = 0

        total_discount = 0
        order_number = pos_session_id.order_count 
        cash_sale = 0
        for order in pos_session_id.order_ids:
            total_taxes = total_taxes + order.amount_tax
            total_amount_with_taxes = total_amount_with_taxes + order.amount_total
            return_total = return_total + order.total_return
            for delete_order in order.line_delete_ids:
                deleted_products_total = deleted_products_total + (delete_order.price * delete_order.quantity)
            
            for line in order.lines.filtered(lambda x: x.product_id.id == order.discount_type_id.discount_program_product_id.id):
                total_discount = total_discount + line.price_subtotal_incl
            
            
            if order.state == 'cancel':
                total_order_rejected = total_order_rejected + order.amount_total
            
            for payment in order.payment_ids:
                amount = payment.amount
                payment_type_total = payment_type_total + amount

                #better to find proper way to read just cash sales
                if payment.payment_method_id.name == 'Cash':
                    cash_sale = cash_sale + amount
                payment_type.append({
                    'id':payment.payment_method_id.id,
                    'name':payment.payment_method_id.name,
                    "amount": amount,
                    # "count": 1
                })
                if payment.pos_order_id.order_type_id:
                    order_payment_type.append({
                        'id':str(payment.payment_method_id.id)+str(payment.payment_method_id.id),
                        "name": payment.pos_order_id.order_type_id.name,
                        "Payment_method_name": payment.payment_method_id.name,
                        "count": 1,
                        "amount": payment.amount,
                    })

            if order.order_type_id:
                order_type_total = order_type_total + order.amount_total
                order_type.append({
                        'id':order.order_type_id.id,
                        'name':order.order_type_id.name,
                        "amount": order.amount_total,
                        "quantity": order.total_qty,
                        # "count": 1,
                    })
        
        day_summary =  {
                # "canceled_products": "40.0",
                "deleted_products": deleted_products_total,
                "returns": return_total,
                # "order_rejected": total_order_rejected,
                "discount": total_discount
            }

        total_amount_without_taxes = total_amount_with_taxes - total_taxes
        company_obj = request.env['res.company'].sudo()
        payment_grouped_data = company_obj.group_sum("id",payment_type,['name'],True)
        order_type_grouped_data = company_obj.group_sum("id",order_type,['name'],True)
        order_type_payment_grouped_data = company_obj.group_sum("id",order_payment_type,['name','Payment_method_name'],True)
        
        session_report.append( {
                    "title": "payment Summary",
                    "total_value": payment_type_total,
                    "data": payment_grouped_data
                }
            )
        session_report.append( {
                    "title": "Order Type Summary",
                    "total_value": order_type_total,
                    "data": order_type_grouped_data
                }
            )
        
            
        
        
        payment_method = {
                    "summary_pay": payment_type_total,
                    "item": payment_grouped_data
                }
        order_type = order_type_grouped_data
        order_type_payment = order_type_payment_grouped_data

        dict_total= {
                "start_balance": pos_session_id.cash_register_balance_start , #"40.0",
                "closing_balance": pos_session_id.cash_register_balance_end_real,
                "differences": pos_session_id.cash_real_difference,
                "cash_sales": cash_sale,
                "without_tax": total_amount_without_taxes,
                "with_tax": total_amount_with_taxes,
                "tax": total_taxes,
            }
        
        



        # Response.status = "200"
        result = {  
                  "message": "Get POS Last Session Report Successfully",
            "body": [{
                "title_ar": "",
                "title_en": "",
                # "id": pos_session_id.id,
                "pos_name": pos_session_id.config_id.name,
                "session_id": pos_session_id.id,
                "session": pos_session_id.name,
                "start_time": str(pos_session_id.start_at),
                "end_time": str(pos_session_id.stop_at),
                "cash_start": pos_session_id.cash_register_balance_start,
                "cash_end": pos_session_id.cash_register_balance_end_real,
                "cashier": pos_session_id.user_id.name,
                "order_number": order_number,
                "session_status": pos_session_id.state,
                "payment_method": payment_method ,
                "order_type_payment":order_type_payment,
                
                "order_type": order_type ,
                "total":dict_total,
                "day_summary":day_summary,
                # "session_report":session_report,
           
            },]

            
        }
        
        return result

    @validate_token
    @http.route('/pos_custom/get_operation_report', type='json', methods=['POST'], auth="none", csrf=False)
    def get_operation_report(self,pos_id,start_date,end_date):
        """Get Last Pos Session report  """


        if not pos_id:
            result = {  
                        "message":"POS ID not Provided",
                    }
            # Response.status = "401"
            return result

            

        
        pos_id = request.env['pos.config'].sudo().search([('id','=',pos_id)])
         
        if not pos_id:
            result = {  
                        "message":"POS ID not Found",
                    }
            # Response.status = "401"
            return result
        
        domain = [('config_id','=',pos_id.id)]

        if not start_date:
            result = {  
                        "message":"Start Date not Provided",
                    }
            # Response.status = "401"
            return result


        if start_date:
            domain.append(('date_order','>=',start_date))
            # pos_order_domain.append(('session_id.start_at','>=',start_date))
        
        if end_date:
            domain.append(('date_order','<=',end_date))

        # pos_session_ids = request.env['pos.session'].sudo().search(domain)
        pos_order_ids = request.env['pos.order'].sudo().search(domain)

        session_report = []
        payment_type = []
        order_type = []
        order_payment_type = []

        payment_type_total = 0  
        order_type_total = 0    

        total_taxes = 0  
        total_amount_with_taxes = 0  
        total_amount_without_taxes = 0  
        deleted_products_total = 0
        return_total = 0
        total_order_rejected = 0

        total_discount = 0
        # for pos_session_id in pos_session_ids:
        for order in pos_order_ids:
            total_taxes = total_taxes + order.amount_tax
            total_amount_with_taxes = total_amount_with_taxes + order.amount_total
            return_total = return_total + order.total_return
            for delete_order in order.line_delete_ids:
                deleted_products_total = deleted_products_total + (delete_order.price * delete_order.quantity)
            
            for line in order.lines.filtered(lambda x: x.product_id.id == order.discount_type_id.discount_program_product_id.id):
                total_discount = total_discount + line.price_subtotal_incl
            
            
            # if order.state == 'cancel':
            #     total_order_rejected = total_order_rejected + order.amount_total
            
            for payment in order.payment_ids:
                amount = payment.amount
                payment_type_total = payment_type_total + amount
                payment_type.append({
                    'id':payment.payment_method_id.id,
                    'name':payment.payment_method_id.name,
                    "amount": amount,
                    # "count": 1
                })
                if payment.pos_order_id.order_type_id:
                    order_payment_type.append({
                        'id':str(payment.payment_method_id.id)+str(payment.payment_method_id.id),
                        "name": payment.pos_order_id.order_type_id.name,
                        "Payment_method_name": payment.payment_method_id.name,
                        "count": 1,
                        "amount": payment.amount,
                    })

            if order.order_type_id:
                order_type_total = order_type_total + order.amount_total
                order_type.append({
                        'id':order.order_type_id.id,
                        'name':order.order_type_id.name,
                        "amount": order.amount_total,
                        "quantity": order.total_qty,
                        # "count": 1,
                    })
        
        day_summary =  {
                # "canceled_products": "40.0",
                "deleted_products": deleted_products_total,
                "returns": return_total,
                # "order_rejected": total_order_rejected,
                "discount": total_discount
            }

        total_amount_without_taxes = total_amount_with_taxes - total_taxes
        company_obj = request.env['res.company'].sudo()
        payment_grouped_data = company_obj.group_sum("id",payment_type,['name'],True)
        order_type_grouped_data = company_obj.group_sum("id",order_type,['name'],True)
        order_type_payment_grouped_data = company_obj.group_sum("id",order_payment_type,['name','Payment_method_name'],True)
        
        for payment_grouped in payment_grouped_data:
            payment_grouped.update(percentage=(str(((payment_grouped['amount']/payment_type_total) * 100)) + '%') if total_discount != 0 else '0%')
        
        session_report.append( {
                    "title": "payment Summary",
                    "total_value": payment_type_total,
                    "data": payment_grouped_data
                }
            )
        session_report.append( {
                    "title": "Order Type Summary",
                    "total_value": order_type_total,
                    "data": order_type_grouped_data
                }
            )
        
            
        
        
        payment_method = {
                    "summary_pay": payment_type_total,
                    "item": payment_grouped_data
                }
        order_type = order_type_grouped_data
        order_type_payment = order_type_payment_grouped_data

        dict_total= {
                "without_tax": total_amount_without_taxes,
                "with_tax": total_amount_with_taxes,
                "tax": total_taxes,
            }
        
        



        # Response.status = "200"
        result = {  
                   "message": "Get operations report Successfully",
            "body": {
                "title_ar": "",
            "title_en": "",
                "pos_name": pos_id.name,
                "start_time": start_date,
                "end_time": end_date,
                "payment_method": payment_method ,
                "order_type_payment":order_type_payment,
                
                "order_type": order_type ,
                "total":dict_total,
                "day_summary":day_summary,
                # "session_report":session_report,
           
            }

            
        }
        
        return result


    @validate_token
    @http.route('/pos_custom/get_sale_report', type='json', methods=['POST'], auth="none", csrf=False)
    def get_sale_report(self,pos_id,start_date,end_date):
        """Get Sale report  """


        if not pos_id:
            result = {  
                        "message":"POS ID not Provided",
                    }
            # Response.status = "401"
            return result

            

        
        pos_id = request.env['pos.config'].sudo().search([('id','=',pos_id)])
         
        if not pos_id:
            result = {  
                        "message":"POS ID not Found",
                    }
            # Response.status = "401"
            return result
        
        domain = [('config_id','=',pos_id.id)]

        if not start_date:
            result = {  
                        "message":"Start Date not Provided",
                    }
            # Response.status = "401"
            return result


        if start_date:
            domain.append(('date_order','>=',start_date))
            # pos_order_domain.append(('session_id.start_at','>=',start_date))
        
        if end_date:
            domain.append(('date_order','<=',end_date))

        # pos_session_ids = request.env['pos.session'].sudo().search(domain)
        pos_order_ids = request.env['pos.order'].sudo().search(domain)

        session_report = []
        payment_type = []
        order_type = []
        order_payment_type = []
        discounts = []

        payment_type_total = 0  
        order_type_total = 0    

        total_taxes = 0  
        total_amount_with_taxes = 0  
        total_amount_without_taxes = 0  
        deleted_products_total = 0
        return_total = 0
        total_order_rejected = 0

        total_discount = 0
        # for pos_session_id in pos_session_ids:
        for order in pos_order_ids:
            total_taxes = total_taxes + order.amount_tax
            total_amount_with_taxes = total_amount_with_taxes + order.amount_total
            return_total = return_total + order.total_return
            for delete_order in order.line_delete_ids:
                deleted_products_total = deleted_products_total + (delete_order.price * delete_order.quantity)
            
            for line in order.lines.filtered(lambda x: x.product_id.id == order.discount_type_id.discount_program_product_id.id):
                total_discount = total_discount + line.price_subtotal_incl
            
            
            # if order.state == 'cancel':
            #     total_order_rejected = total_order_rejected + order.amount_total
            
            for payment in order.payment_ids:
                amount = payment.amount
                payment_type_total = payment_type_total + amount
                payment_type.append({
                    'id':payment.payment_method_id.id,
                    'name':payment.payment_method_id.name,
                    "amount": amount,
                    "count": 1
                })
                if payment.pos_order_id.order_type_id:
                    order_payment_type.append({
                        'id':str(payment.payment_method_id.id)+str(payment.payment_method_id.id),
                        "name": payment.pos_order_id.order_type_id.name,
                        "Payment_method_name": payment.payment_method_id.name,
                        "count": 1,
                        "amount": payment.amount,
                    })

            if order.order_type_id:
                order_type_total = order_type_total + order.amount_total
                order_type.append({
                        'id':order.order_type_id.id,
                        'name':order.order_type_id.name,
                        "amount": order.amount_total,
                        "quantity": order.total_qty,
                        # "count": 1,
                    })
            if order.discount_type_id:
                order._get_discount_program_total()
                discounts.append(
                    {
                        "id":order.discount_type_id.id,
                        "name": order.discount_type_id.name,
                        # "percentage": "21.0",
                        "total": order.discount_type_total

                    }
                )
        day_summary =  {
                # "canceled_products": "40.0",
                "deleted_products": deleted_products_total,
                "returns": return_total,
                # "order_rejected": total_order_rejected,
                "discount": total_discount
            }

        total_amount_without_taxes = total_amount_with_taxes - total_taxes
        company_obj = request.env['res.company'].sudo()
        payment_grouped_data = company_obj.group_sum("id",payment_type,['name'],True)
        order_type_grouped_data = company_obj.group_sum("id",order_type,['name'],True)
        order_type_payment_grouped_data = company_obj.group_sum("id",order_payment_type,['name','Payment_method_name'],True)
        discounts_grouped_data = company_obj.group_sum("id",discounts,[],True)
        


        for discount_grouped in discounts_grouped_data:
            discount_grouped.update(percentage=(str(((discount_grouped['total']/total_discount) * 100)) + '%') if total_discount != 0 else '0%')
        
        for order_type_grouped in order_type_grouped_data:
            order_type_grouped.update(percentage=(str(((order_type_grouped['amount']/order_type_total) * 100)) + '%') if total_discount != 0 else '0%')
        
        for payment_grouped in payment_grouped_data:
            payment_grouped.update(percentage=(str(((payment_grouped['amount']/payment_type_total) * 100)) + '%') if total_discount != 0 else '0%')
        
        
        
        session_report.append( {
                    "title": "payment Summary",
                    "total_value": payment_type_total,
                    "data": payment_grouped_data
                }
            )
        session_report.append( {
                    "title": "Order Type Summary",
                    "total_value": order_type_total,
                    "data": order_type_grouped_data
                }
            )
        
            
        
        
        payment_method = payment_grouped_data
                
        order_type = order_type_grouped_data
        order_type_payment = order_type_payment_grouped_data
        discount_dict =  {
                    "total": total_discount,
                     "item": discounts_grouped_data
                   
                }



        dict_total= {
                "without_tax": total_amount_without_taxes,
                "with_tax": total_amount_with_taxes,
                "tax": total_taxes,
            }
        
        



        # Response.status = "200"
        result = {  
                   "message": "Get Sales summary Successfully",
            "body": {
                "title_ar": "",
                "title_en": "",
                "pos_name": pos_id.name,
                "start_time": str(start_date),
                "end_time": str(end_date),
                "total":dict_total,
                "day_summary":day_summary,
                "payment_method": payment_method ,
                # "order_type_payment":order_type_payment,
                
                "order_type": order_type ,
                "discount":discount_dict,
                
                
                # "session_report":session_report,
           
            }

            
        }
        
        return result


    @validate_token
    @http.route("/pos_custom/get_cashier_profile", methods=["POST"], type="json", auth="none", csrf=False)
    def get_cashier_profile(self, user_id,):
        """
        GET CAHHIER PROFILE DATA WITH USER ID
        """
        
        if not user_id:
            # Response.status = "403"
            response = {
                        "message": "User ID Not Provided"
                        }                                 
            return response
        user_id = request.env['res.users'].sudo().search([('id','=',user_id)])
        
        if not user_id:
            # Response.status = "403"
            response = {
                        "message": "User ID not Found"
                        }                                 
            return response
        
        
        
                 
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # Response.status = "200"
        
        
        

        pos_log = request.env['res.users.pos.log'].sudo().search([('user_id','=',user_id.id)],order="id desc",limit=1)
        

        result = {
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
                    "login_time":(str(pos_log.login_date) if pos_log.login_date else ""),
                            }
                    }
        # Response.status = "200"
        return result




    @validate_token
    @http.route('/pos_custom/get_all_discount', type='json', methods=['POST'], auth="none", csrf=False)
    def get_all_discount(self,**kw):
        """get All discount available """   
        
        pos_id = kw.get('pos_id',False)
        if not pos_id:
            # Response.status = "403"
            response = {
                        "message": "POS ID Not Provided"
                        }                                 
            return response
        pos_id = request.env['pos.config'].sudo().search([('id','=',pos_id)])
        
        if not pos_id:
            # Response.status = "403"
            response = {
                        "message": "POS ID not Found"
                        }                                 
            return response

        discount_program_obj = request.env['pos.discount_program'].sudo()
        discount_programs = discount_program_obj.search([('pos_applied','in',pos_id.ids)])
        
        if not discount_programs:
            # Response.status = "200"
            response = {
                        "message": "No Disocunt Program Found for POS",
                        "body": [],
                        }                                 
            return response
        
        # Response.status = "200"
        result = {
        "message": "Get all discounts successfully",
        "body": [
                        {
                            "id": discount_program.id,
                            "name": discount_program.name,
                            "type": discount_program.discount_type,
                            "required_customer": discount_program.require_customer,
                            "amount": discount_program.amount,
                            "pos_categories_ids": discount_program.pos_category_ids.ids,
                            # "pos_applied_ids": discount_program.pos_applied.ids,
                            "discount_product_id": discount_program.discount_program_product_id.id,
                        } for discount_program in discount_programs
                    ]
                }
        # Response.status = "200"
        return result
        

    @validate_token
    @http.route('/pos_custom/pos_order_delete_product', type='json', methods=['POST'], auth="none", csrf=False)
    def pos_order_delete_product(self,order_id,product_id):
        """Delete Product From Order"""   

        if not order_id:
            # Response.status = "403"
            response = {
                        "message": "Order ID Not Provided"
                        }                                 
            return response
        order_id = request.env['pos.order'].sudo().search([('id','=',order_id)])
        
        if not order_id:
            # Response.status = "403"
            response = {
                        "message": "Order ID not Found"
                        }                                 
            return response

        if order_id.state in ['paid','done','invoiced']:
            # Response.status = "403"
            response = {
                        "message": "Sorry!! , you can't delete Product when Order in Paid,Posted Or Invoiced State"
                        }                                 
            return response
            
        if not product_id:
            # Response.status = "403"
            response = {
                        "message": "Product ID Not Provided"
                        }                                 
            return response
        product_id = request.env['product.product'].sudo().search([('id','=',product_id)])
        
        if not product_id:
            # Response.status = "403"
            response = {
                        "message": "Product ID not Found"
                        }                                 
            return response
        
        order_product = order_id.lines.filtered(lambda x: x.product_id.id == product_id.id)
        if not order_product:
            # Response.status = "403"
            response = {
                        "message": "Product ID not Found in Order"
                        }                                 
            return response
        order_product.unlink()

        order_id._onchange_amount_all()
        
        # Response.status = "200"
        result = {
          "message": "Product Deleted successfully"
        
        }

        return result
        
        

