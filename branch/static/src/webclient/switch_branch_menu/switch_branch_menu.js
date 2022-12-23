/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";
import { symmetricalDifference } from "@web/core/utils/arrays";
var ajax = require('web.ajax');
const { Component, hooks } = owl;
const { useState } = hooks;

export class SwitchBranchMenu extends Component {
    setup() {
        this.branchService = useService("branch");
        this.currentBranch = this.branchService.currentBranch;
        this.state = useState({ branchesToToggle: [] });
    }

    toggleBranch(branchId,isBranchSelected) {
        
        this.state.branchesToToggle = symmetricalDifference(this.state.branchesToToggle, [
            branchId,
        ]);

        var data = symmetricalDifference(
            this.branchService.allowedBranchIds,
            this.state.branchesToToggle
        );
        console.log(data); //IN CASE FALSE THEN MUST BE IN ALLOWED , ELSE VICE VERSA
        
        browser.clearTimeout(this.toggleTimer);
        this.toggleTimer = browser.setTimeout(() => {
            this.branchService.setBranches("toggle", ...this.state.branchesToToggle);
        }, this.constructor.toggleDelay);

        var branch_select = isBranchSelected;
        if (branch_select == true){
            branch_select = false;
        }
        else{
            branch_select = true;
        }

        ajax.jsonRpc('/set_active_branch', 'call', {
            'BranchIDs': data,
            'isBranchSelected': true,
        })

        // ajax.jsonRpc('/set_active_branch_toggle', 'call', {
        //     'BranchID': branchId,
        //     'isBranchSelected': branch_select,
        // })

    }

    logIntoBranch(branchId) {
        console.log(">>>>>>>>>>>>>>>>>>>>1");
        console.log(branchId);
        var allowedBranchIds = this.branchService.allowedBranchIds;
        console.log(allowedBranchIds);
        if (allowedBranchIds.length === 1) {
            // 1 enabled branch: stay in single branch mode
            // nextBranchIds = [branchId];
            console.log(">>>>>>>>>>>>SINGLE BRANCH MODE");
            ajax.jsonRpc('/set_active_branch', 'call', {
                'BranchIDs': [branchId,],
                'isBranchSelected': true,
            })
        } else {
            console.log(">>>>>>>>>>>>MULTI BRANCH MODE");
            ajax.jsonRpc('/set_branch', 'call', {
                'BranchID':  branchId,
        });
        }

        browser.clearTimeout(this.toggleTimer);
        console.log(">>>>>>>>>>>>>>>>>>>>2");
        this.branchService.setBranches("loginto", branchId);
        console.log(">>>>>>>>>>>>>>>>>>>>3");
        

        ajax.jsonRpc('/set_branch', 'call', {
            'BranchID':  branchId,
    });
    console.log(">>>>>>>>>>>>>>>>>>>>4");
    }

    get selectedBranches() {
        return symmetricalDifference(
            this.branchService.allowedBranchIds,
            this.state.branchesToToggle
        );
    }
}
SwitchBranchMenu.template = "SwitchBranchMenu";
SwitchBranchMenu.toggleDelay = 1000;

export const systraybItem = {
    Component: SwitchBranchMenu,
    isDisplayed(env) {
        const { availableBranches } = env.services.branch;
        return Object.keys(availableBranches).length > 1;
    },
};

registry.category("systray").add("SwitchBranchMenu", systraybItem, { sequence: 1 });
