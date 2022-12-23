""" Inherit Account Move Line to integrate with custody """
from odoo import api, fields, models


# pylint: disable=no-member
class AccountMoveLine(models.Model):
    """
        Inherit Account Move Line:
         - add custody item to be sent to asset when created from bills
    """
    _inherit = 'account.move.line'

    custody_item_id = fields.Many2one('custody.item')
    custody_item_ids = fields.Many2many(
        'custody.item', compute='_compute_items', store=True
    )

    @api.depends('account_id', 'account_id.custody_item_ids')
    def _compute_items(self):
        """ Compute items that linked with the account """
        for line in self:
            line.custody_item_ids = line.account_id.custody_item_ids.ids
