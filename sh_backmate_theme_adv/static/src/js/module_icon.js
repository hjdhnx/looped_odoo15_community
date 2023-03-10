odoo.define('backmate_adv.settings', function (require) {
	"use strict";
		var BaseSetting = require('base.settings');
		var core = require('web.core');
		var FormController = require('web.FormController');
		var FormRenderer = require('web.FormRenderer');
		var view_registry = require('web.view_registry');
		var QWeb = core.qweb;
		var _t = core._t;
		BaseSetting.Renderer.include({
			// change settings icons
			 _getAppIconUrl: function (module) {
				 console.log(">>>>>>>>>>>>>>>",module)
			        //  return module === "general_settings" ? "/sh_backmate_theme_adv/static/src/icons/2d/settings.svg" : "/"+module+"/static/description/icon.png";
					return "/sh_backmate_theme_adv/static/src/icons/2d/setting_icons/"+module+".svg";
			   }
		});
	});

		