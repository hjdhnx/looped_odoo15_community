# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, fields, http, models, _
from odoo import models, fields, api, exceptions, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

class HrEmployee(models.Model):

	_inherit = "hr.attendance"

	checkin_message = fields.Char(string="Check-In Message")
	checkout_message = fields.Char(string="Check-Out Message")
	login_latitude = fields.Char(string="Latitude")
	login_longitude = fields.Char(string="Longitude")
	logout_latitude = fields.Char(string="Latitude")
	logout_longitude = fields.Char(string="Longitude")
	checkin_link = fields.Char(string="Check-In Location")
	checkout_link = fields.Char(string="Check-Out Location")

class HrEmployee(models.Model):

	_inherit = "hr.employee"


	def attendance_manual(self, next_action, checkin_message, checkout_message, map_link, longitude, latitude, entered_pin=None):
		self.ensure_one()
		can_check_without_pin = not self.env.user.has_group('hr_attendance.group_hr_attendance_use_pin') or (self.user_id == self.env.user and entered_pin is None)
		if can_check_without_pin or entered_pin is not None and entered_pin == self.sudo().pin:
			return self.attendance_action(next_action, checkin_message, checkout_message, map_link, longitude, latitude)
		return {'warning': _('Wrong PIN')}



	def attendance_action(self, next_action, checkin_message, checkout_message, map_link, longitude, latitude):
		""" Changes the attendance of the employee.
			Returns an action to the check in/out message,
			next_action defines which menu the check in/out message should return to. ("My Attendances" or "Kiosk Mode")
		"""
		self.ensure_one()
		employee = self.sudo()
		action_message = self.env["ir.actions.actions"]._for_xml_id("hr_attendance.hr_attendance_action_greeting_message")
		action_message['previous_attendance_change_date'] = employee.last_attendance_id and (employee.last_attendance_id.check_out or employee.last_attendance_id.check_in) or False
		action_message['employee_name'] = employee.name
		action_message['barcode'] = employee.barcode
		action_message['next_action'] = next_action
		action_message['hours_today'] = employee.hours_today
		action_message['checkin_message'] = checkin_message
		action_message['checkout_message'] = checkout_message

		if employee.user_id:
			modified_attendance = employee.with_user(employee.user_id).attendance_action_change(checkin_message, checkout_message, map_link, longitude, latitude)
		else:
			modified_attendance = employee.attendance_action_change(checkin_message, checkout_message, map_link, longitude, latitude)
		action_message['attendance'] = modified_attendance.read()[0]
		action_message['total_overtime'] = employee.total_overtime
		return {'action': action_message}


	def attendance_action_change(self, checkin_message, checkout_message, map_link, longitude, latitude):
		""" Check In/Check Out action
			Check In: create a new attendance record
			Check Out: modify check_out field of appropriate attendance record
		"""
		self.ensure_one()		
		action_date = fields.Datetime.now()

		if self.attendance_state != 'checked_in':
			if checkin_message:
				vals = {
					'employee_id': self.id,
					'check_in': action_date,
					'checkin_message':checkin_message,
					'checkin_link': map_link,
					'login_latitude': latitude,
					'login_longitude':longitude,
				}
			elif checkout_message:
				vals = {
					'employee_id': self.id,
					'check_in': action_date,
					'checkout_message':checkout_message,
					'checkout_link': map_link,
					'logout_latitude':latitude,
					'logout_longitude': longitude,
				}
			else:
				vals = {
					'employee_id': self.id,
					'check_in': action_date,
				}
			return self.env['hr.attendance'].create(vals)

		attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
		if attendance:
			if checkin_message:
				attendance.check_out = action_date
				attendance.checkin_message = checkin_message
				attendance.checkin_link = map_link
				attendance.login_latitude = latitude
				attendance.login_longitude = longitude
			elif checkout_message:
				attendance.check_out = action_date
				attendance.checkout_message = checkout_message
				attendance.checkout_link = map_link
				attendance.logout_latitude = latitude
				attendance.logout_longitude = longitude
			else:
				attendance.check_out = action_date
		else:
			raise exceptions.UserError(_('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
				'Your attendances have probably been modified manually by human resources.') % {'empl_name': self.sudo().name, })
		return attendance
