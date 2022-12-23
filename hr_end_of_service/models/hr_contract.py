from odoo import models, fields, api, _
from odoo.exceptions import UserError

class hrContract(models.Model):
    _inherit = 'hr.contract'

    is_active_penalty = fields.Boolean("Active Penalty Condition")
    penalty_value = fields.Float()