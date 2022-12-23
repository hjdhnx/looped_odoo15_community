odoo.define('bi_inventory_valuation_reports.ListControllerExtender', function (require) {
"use strict";

	var ListController = require('web.ListController');

	ListController.include({

		_onSelectDomain: function (ev) {	
			this._super.apply(this, arguments);
			const state = this.model.get(this.handle, {raw: true});
			var flag = state.context.tree_view_ref
			var id = state.id.split("_")[1]
			if (flag == "bi_inventory_valuation_reports.custom_tree_view"){
				this._rpc({
	                model: 'product.product',
	                method: 'set_flag_to_get_all_records',
	                args: [parseInt(id)],
	            })
			}
			
	    },
	});
});