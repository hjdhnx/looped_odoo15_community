# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

MAP_INVOICE_TYPE_PARTNER_TYPE = {
	'out_invoice': 'customer',
	'out_refund': 'customer',
	'in_invoice': 'supplier',
	'in_refund': 'supplier',
}

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	@api.model
	def default_get(self, fields):
		rec = super(AccountPayment, self).default_get(fields)
		invoice_defaults = self.reconciled_invoice_ids
		if invoice_defaults and len(invoice_defaults) == 1:
			invoice = invoice_defaults[0]
			rec['branch_id'] = invoice.branch_id.id
		return rec

	branch_id = fields.Many2one('res.branch')

