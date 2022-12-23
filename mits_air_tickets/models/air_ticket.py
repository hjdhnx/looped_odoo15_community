# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime, time, timedelta
from odoo.fields import Date, Datetime
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp

class airTicketRequest(models.Model):
    _inherit = 'air.ticket.request'

    late_request_id = fields.Many2one('late.request')

    @api.onchange('late_request_id')
    def onchange_late_Request_set_ticket_type(self):
        for rec in self:
            if rec.late_request_id and rec.late_request_id.late_request_id.air_ticket_type_id:
                rec.air_ticket_type = rec.late_request_id.late_request_id.air_ticket_type_id


class airTicketType(models.Model):
    _inherit = 'air.ticket.type'

    # @api.constrains('relatives_tickets')
    # def onchange_