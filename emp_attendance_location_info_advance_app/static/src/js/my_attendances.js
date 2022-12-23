odoo.define('emp_attendance_google_map_app.my_attendances_restriction', function (require) {
"use strict";

	var AbstractAction = require('web.AbstractAction');
	var core = require('web.core');
	var ajax = require('web.ajax');
	var MyAttendances = require('hr_attendance.my_attendances');
	var GreetingMessage = require('hr_attendance.greeting_message')
	var QWeb = core.qweb;
	var _t = core._t;
	var rpc = require('web.rpc');
	var KioskConfirm = require('hr_attendance.kiosk_confirm')

	KioskConfirm.include({
		events: {
	        "click .o_hr_attendance_back_button": function () { this.do_action(this.next_action, {clear_breadcrumbs: true}); },
	        "click .o_hr_attendance_sign_in_out_icon": _.debounce(function () {
	            var self = this;
	            var checkin_message = $('.oe_kiosk_checkin_message').val();
        		var checkout_message = $('.oe_kiosk_checkout_message').val();
	            navigator.geolocation.getCurrentPosition(function(position){
					self.lat = position.coords.latitude;
					self.long = position.coords.longitude;
		            var map_link = "https://maps.google.com/?q=" + self.lat + "," + self.long;
		            self._rpc({
		                    model: 'hr.employee',
		                    method: 'attendance_manual',
		                    args: [[self.employee_id], self.next_action, checkin_message, checkout_message, map_link, self.lat, self.long],
		                })
		                .then(function(result) {
		                    if (result.action) {
		                        self.do_action(result.action);
		                    } else if (result.warning) {
		                        self.do_warn(result.warning);
		                    }
		                });
		            });
	        }, 200, true),
	        'click .o_hr_attendance_pin_pad_button_0': function() { this.$('.o_hr_attendance_PINbox').val(this.$('.o_hr_attendance_PINbox').val() + 0); },
	        'click .o_hr_attendance_pin_pad_button_1': function() { this.$('.o_hr_attendance_PINbox').val(this.$('.o_hr_attendance_PINbox').val() + 1); },
	        'click .o_hr_attendance_pin_pad_button_2': function() { this.$('.o_hr_attendance_PINbox').val(this.$('.o_hr_attendance_PINbox').val() + 2); },
	        'click .o_hr_attendance_pin_pad_button_3': function() { this.$('.o_hr_attendance_PINbox').val(this.$('.o_hr_attendance_PINbox').val() + 3); },
	        'click .o_hr_attendance_pin_pad_button_4': function() { this.$('.o_hr_attendance_PINbox').val(this.$('.o_hr_attendance_PINbox').val() + 4); },
	        'click .o_hr_attendance_pin_pad_button_5': function() { this.$('.o_hr_attendance_PINbox').val(this.$('.o_hr_attendance_PINbox').val() + 5); },
	        'click .o_hr_attendance_pin_pad_button_6': function() { this.$('.o_hr_attendance_PINbox').val(this.$('.o_hr_attendance_PINbox').val() + 6); },
	        'click .o_hr_attendance_pin_pad_button_7': function() { this.$('.o_hr_attendance_PINbox').val(this.$('.o_hr_attendance_PINbox').val() + 7); },
	        'click .o_hr_attendance_pin_pad_button_8': function() { this.$('.o_hr_attendance_PINbox').val(this.$('.o_hr_attendance_PINbox').val() + 8); },
	        'click .o_hr_attendance_pin_pad_button_9': function() { this.$('.o_hr_attendance_PINbox').val(this.$('.o_hr_attendance_PINbox').val() + 9); },
	        'click .o_hr_attendance_pin_pad_button_C': function() { this.$('.o_hr_attendance_PINbox').val(''); },
	        'click .o_hr_attendance_pin_pad_button_ok': _.debounce(function() {
	            var self = this;
	            this.$('.o_hr_attendance_pin_pad_button_ok').attr("disabled", "disabled");
	            var checkin_message = $('.oe_kiosk_checkin_message').val();
        		var checkout_message = $('.oe_kiosk_checkout_message').val();
	            navigator.geolocation.getCurrentPosition(function(position){
					self.lat = position.coords.latitude;
					self.long = position.coords.longitude;
		            var map_link = "https://maps.google.com/?q=" + self.lat + "," + self.long;
		            self._rpc({
		                    model: 'hr.employee',
		                    method: 'attendance_manual',
		                    args: [[self.employee_id], self.next_action, checkin_message, checkout_message, map_link, self.lat, self.long, self.$('.o_hr_attendance_PINbox').val()],
		                })
		                .then(function(result) {
		                    if (result.action) {
		                        self.do_action(result.action);
		                    } else if (result.warning) {
		                        self.do_warn(result.warning);
		                        self.$('.o_hr_attendance_PINbox').val('');
		                        setTimeout( function() { self.$('.o_hr_attendance_pin_pad_button_ok').removeAttr("disabled"); }, 500);
		                    }
		                });
		            });
	        }, 200, true),
	    },
	});

	MyAttendances.include({
		start: function () {
			this._super.apply(this, arguments)
		},

		update_attendance: function () {
        var self = this;
        var checkin_message = $('.oe_checkin_message').val();
        var checkout_message = $('.oe_checkout_message').val();
        var co_o = [];
        navigator.geolocation.getCurrentPosition(function(position){
			self.lat = position.coords.latitude;
			self.long = position.coords.longitude;
	        var map_link = "https://maps.google.com/?q=" + self.lat + "," + self.long;
	        rpc.query({
	                model: 'hr.employee',
	                method: 'attendance_manual',
	                args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances', checkin_message, checkout_message, map_link, self.lat, self.long],
	            })
	            .then(function(result) {
	                if (result.action) {
	                    self.do_action(result.action);
	                } else if (result.warning) {
	                    self.do_warn(result.warning);
	                }
	            });
            });	
    	},
	});
});