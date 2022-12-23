

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    it_manager = fields.Many2one('hr.employee', string="Computer Manager")
    stock_manager = fields.Many2one('hr.employee', string="Stock Manager")


class HREmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    it_manager = fields.Many2one('hr.employee', string="Computer Manager")
    stock_manager = fields.Many2one('hr.employee', string="Stock Manager")



