""" Inherit Account Move to integrate with custody """
from odoo import models


# pylint: disable=no-member
class AccountMove(models.Model):
    """
        Inherit Account Move:
         - auto add custody item to the created asset
         - auto create custody property to the asset
    """
    _inherit = 'account.move'

    def _auto_create_asset(self):
        """
            Override _auto_create_asset:
             - link asset with custody item and property
        """
        assets = super()._auto_create_asset()
        for asset in assets:
            line_items = asset.original_move_line_ids.mapped('custody_item_id')
            for item in line_items:
                asset.custody_item_id = item.id
            if asset.state == 'open':
                asset.create_custody_property()
        return assets
