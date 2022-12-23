# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


import logging
from hashlib import sha256
from lxml import etree
from lxml.builder import E
from odoo import api, fields, models, tools, SUPERUSER_ID, _

_logger = logging.getLogger(__name__)


#
# Functions for manipulating boolean and selection pseudo-fields
#
def name_boolean_group(id):
	return 'in_group_' + str(id)

def name_selection_groups(ids):
	return 'sel_groups_' + '_'.join(str(it) for it in ids)


class GroupsView(models.Model):
	_inherit = 'res.groups'


	# @api.model
	# def _update_user_groups_view(self):
	# 	super(GroupsView,self)._update_user_groups_view()
	# 	""" Modify the view with xmlid ``base.user_groups_view``, which inherits
	# 		the user form view, and introduces the reified group fields.
	# 	"""

	# 	# remove the language to avoid translations, it will be handled at the view level
	# 	self = self.with_context(lang=None)

	# 	# We have to try-catch this, because at first init the view does not
	# 	# exist but we are already creating some basic groups.
	# 	view = self.env.ref('base.user_groups_view', raise_if_not_found=False)
	# 	if view and view.exists() and view._name == 'ir.ui.view':
	# 		group_no_one = view.env.ref('base.group_no_one')
	# 		group_employee = view.env.ref('base.group_user')
	# 		non_user_group = view.env.ref('pos_branch.group_no_branch_user')
	# 		xml1, xml2, xml3 = [], [], []
	# 		xml_by_category = {}
	# 		xml1.append(E.separator(string='User Type', colspan="2", groups='base.group_no_one'))

	# 		user_type_field_name = ''
	# 		user_type_readonly = str({})
	# 		sorted_tuples = sorted(self.get_groups_by_application(),
	# 							   key=lambda t: t[0].xml_id != 'base.module_category_user_type')
	# 		for app, kind, gs, category_name in sorted_tuples:  # we process the user type first
	# 			attrs = {}
	# 			# hide groups in categories 'Hidden' and 'Extra' (except for group_no_one)
	# 			if app.xml_id in self._get_hidden_extra_categories():
	# 				attrs['groups'] = 'base.group_no_one'

	# 			# User type (employee, portal or public) is a separated group. This is the only 'selection'
	# 			# group of res.groups without implied groups (with each other).
	# 			if app.xml_id == 'base.module_category_user_type':
	# 				# application name with a selection field
	# 				field_name = name_selection_groups(gs.ids)
	# 				user_type_field_name = field_name
	# 				user_type_readonly = str({'readonly': [(user_type_field_name, '!=', group_employee.id)]})
	# 				attrs['widget'] = 'radio'
	# 				attrs['groups'] = 'base.group_no_one'
	# 				xml1.append(E.field(name=field_name, **attrs))
	# 				xml1.append(E.newline())

	# 			elif kind == 'selection':
	# 				# application name with a selection field
	# 				field_name = name_selection_groups(gs.ids)
	# 				attrs['attrs'] = user_type_readonly
	# 				if category_name not in xml_by_category:
	# 					xml_by_category[category_name] = []
	# 					xml_by_category[category_name].append(E.newline())
	# 				xml_by_category[category_name].append(E.field(name=field_name, **attrs))
	# 				xml_by_category[category_name].append(E.newline())

	# 			else:
	# 				# application separator with boolean fields
	# 				app_name = app.name or 'Other'
	# 				xml3.append(E.separator(string=app_name, colspan="4", **attrs))
	# 				attrs['attrs'] = user_type_readonly
	# 				for g in gs:
	# 					field_name = name_boolean_group(g.id)
	# 					if g == group_no_one or g == non_user_group:
	# 						# make the group_no_one invisible in the form view
	# 						xml3.append(E.field(name=field_name, invisible="1", **attrs))
	# 					else:
	# 						xml3.append(E.field(name=field_name, **attrs))

	# 		xml3.append({'class': "o_label_nowrap"})
	# 		if user_type_field_name:
	# 			user_type_attrs = {'invisible': [(user_type_field_name, '!=', group_employee.id)]}
	# 		else:
	# 			user_type_attrs = {}

	# 		for xml_cat in sorted(xml_by_category.keys(), key=lambda it: it[0]):
	# 			xml_cat_name = xml_cat[1]
	# 			master_category_name = (_(xml_cat_name))
	# 			xml2.append(E.group(*(xml_by_category[xml_cat]), col="2", string=master_category_name))

	# 		xml = E.field(
	# 			E.group(*(xml1), col="2"),
	# 			E.group(*(xml2), col="2", attrs=str(user_type_attrs)),
	# 			E.group(*(xml3), col="4", attrs=str(user_type_attrs)), name="groups_id", position="replace")
	# 		xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))
	# 		xml_content = etree.tostring(xml, pretty_print=True, encoding="unicode")

	# 		new_context = dict(view._context)
	# 		new_context.pop('install_filename', None)  # don't set arch_fs for this computed view
	# 		new_context['lang'] = None
	# 		view.with_context(new_context).write({'arch': xml_content})

