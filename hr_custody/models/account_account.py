""" Inherit Account Account to integrate with custody """
from odoo import fields, models


class AccountAccount(models.Model):
    """
        Inherit Account Account
         - integrate with custody items
    """
    _inherit = 'account.account'

    custody_item_ids = fields.Many2many('custody.item', check_company=True)
