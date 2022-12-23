from . import models
from odoo.exceptions import UserError
from odoo import _

def pre_init_check(cr):
	query = """ select id,name from ir_module_module where name='combo_server' and state='installed' """
	cr.execute(query)
	res = cr.fetchall()
	if len(res)>0:
		raise UserError(_("You can\'t install cobmo client module and combo server module on the same database"))
