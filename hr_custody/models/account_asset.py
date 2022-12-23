""" Inherit Account Asset to integrate with custody """
from odoo import api, fields, models


# pylint: disable=missing-return,no-member
class AccountAsset(models.Model):
    """
        Inherit Account Asset
         - integrate with custody property
    """
    _inherit = 'account.asset'

    custody_item_id = fields.Many2one('custody.item')
    custody_property_id = fields.Many2one('custody.property')
    custody_item_ids = fields.Many2many(
        'custody.item', compute='_compute_items', store=True
    )

    @api.depends('account_asset_id', 'account_asset_id.custody_item_ids')
    def _compute_items(self):
        """ Compute items value """
        for line in self:
            line.custody_item_ids = line.account_asset_id.custody_item_ids.ids

    def validate(self):
        """
            Override validate:
             - add new custody property when create new asset
        """
        self.create_custody_property()
        super().validate()

    def create_custody_property(self):
        """ Create custody property and link with asset """
        for asset in self:
            if asset.custody_item_id:
                property_id = self.env['custody.property'].create({
                    'name': asset.name,
                    'property_type': 'asset',
                    'asset_id': asset.id,
                    'item_id': asset.custody_item_id.id,
                })
                asset.custody_property_id = property_id.id
