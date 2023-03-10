# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare




class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def default_get(self, default_fields):
        res = super(AccountMove, self).default_get(default_fields)
        branch_id = False

        if self._context.get('branch_id'):
            branch_id = self._context.get('branch_id')
        elif self.env.user.branch_id:
            branch_id = self.env.user.branch_id.id
        res.update({
            'branch_id' : branch_id
        })
        return res

    branch_id = fields.Many2one('res.branch', string="Branch")

    # branch_id = fields.Many2one(comodel_name='res.branch', string='Branch',
    #                              store=True, readonly=False,
    #                              compute='_compute_branch_id')

    
    def _compute_branch_id(self):
        for move in self:
            move.company_id = self.env.branch

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def default_get(self, default_fields):
        res = super(AccountMoveLine, self).default_get(default_fields)
        branch_id = False

        if self._context.get('branch_id'):
            branch_id = self._context.get('branch_id')
        elif self.env.user.branch_id:
            branch_id = self.env.user.branch_id.id

        if self.move_id.branch_id :
            branch_id = self.move_id.branch_id.id
        res.update({'branch_id' : branch_id})
        return res

    branch_id = fields.Many2one('res.branch', string="Branch",related="move_id.branch_id",store=True)
