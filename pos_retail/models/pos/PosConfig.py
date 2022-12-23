# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging
from odoo.exceptions import UserError, ValidationError
import re
import requests
import json
import base64

try:
    to_unicode = unicode
except NameError:
    to_unicode = str

_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    # method_type = fields.Selection([ ('cash', 'Cash'), ('bank', 'Bank') ], string='Type')
    type = fields.Selection(selection=[('cash', 'Cash'), ('bank', 'Bank'), ('pay_later', 'Pay Later')], compute="_compute_type")

    create_invoice = fields.Boolean('')
    arbic_name = fields.Char('')
    
class PosConfig(models.Model):
    _inherit = "pos.config"

    pos_loyalty_id = fields.Many2one(
        'pos.loyalty', 'Loyalty',
        domain=[('state', '=', 'running')])
    loyalty_combine_promotion = fields.Boolean(
        'Loyalty Combine Promotion',
        help='If checked: allow each order line, loyalty plus point and promotion apply together \n'
             'If not checked: When promotion add to order lines, points will not plus'
    )
    promotion_manual_select = fields.Boolean(
        'Promotion manual Choice', default=0,
        help='When you check to this checkbox, \n'
             'your cashiers will have one button, \n'
             'when cashiers clicked on it, \n'
             'all promotions active will display for choose')
    promotion_auto_add = fields.Boolean(
        'Promotion Auto Apply',
        help='All Promotion Active with Condition Items in Cart \n'
             'When Cashier click Paid button, all Promotions Active will add to Order')

    promotion_ids = fields.Many2many(
        'pos.promotion',
        'pos_config_promotion_rel',
        'config_id',
        'promotion_id',
        string='Promotions Applied')
    
    wallet_id = fields.Many2one(
        'pos.wallet.rule',
        
        string='Wallets Applied')
    wallet_ids = fields.Many2many(
        'pos.wallet.rule',
        
        string='Wallets Applied')


    
    allow_split_table = fields.Boolean('Allow Split Table')
    # allow_merge_table = fields.Boolean('Merge/Combine Tables')
    allow_transfer_table = fields.Boolean('Transfer Tables')
    allow_lock_table = fields.Boolean(
        'Lock Table',
        default=0,
        help='If Customer Booked Table, you can lock talbe \n'
             'Unlock by Pos Pass In of Managers Validation')
    required_set_guest = fields.Boolean(
        'Auto ask Guests when add new Order')


    whatsapp_api = fields.Char('WhatApp Api')
    whatsapp_token = fields.Char('WhatApp Token')
    whatsapp_send_type = fields.Selection([
        ('automatic', 'Automatic'),
        ('manual', 'Manual')
    ], string='WhatApp send Receipt Type', default='manual')
    whatsapp_message_receipt = fields.Text(
        'WhatsApp Message Receipt',
        default='Thank you for giving us the opportunity to serve you. This is your receipt'
    )
