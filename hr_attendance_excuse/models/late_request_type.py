# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime, time, timedelta
from odoo.fields import Date, Datetime
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp

class LateRequest(models.Model):
    _name = 'late.request.type'

    name = fields.Char()

    period_type = fields.Selection([('hours','Hour'),('days','Days')],default='hours',required=1)
    days_limit  = fields.Integer()
    hours_limit = fields.Float()
    TYPE = [('late', 'Late IN'),
            ('ab', 'Absence'),
            ('diff', 'Early Out'),
            ('other', 'Others'),]
    penality_type = fields.Selection(string="Type", selection=TYPE, required=True,default='' )
