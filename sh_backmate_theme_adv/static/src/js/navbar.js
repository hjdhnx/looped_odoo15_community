/** @odoo-module **/
import { MenuDropdown, MenuItem, NavBar } from '@web/webclient/navbar/navbar';
import { patch } from 'web.utils';
// import { ProfileSection } from "@sh_backmate_theme/js/profilesection";
import { ErrorHandler, NotUpdatable } from "@web/core/utils/components";

const components = { NavBar };
var rpc = require("web.rpc");

var theme_style = 'default';

var config = require("web.config");
var session = require('web.session');
var rpc = require('web.rpc')
var icon_style = 'standard';


rpc.query({
    model: 'sh.back.theme.config.settings',
    method: 'search_read',
    args: [[], ['icon_style']],
}, { async: false }).then(function (output) {
    if (output) {
        var i;
        for (i = 0; i < output.length; i++) {
            if (output[i]['icon_style'] == '2d') {
                icon_style = '2d';
            }

        }
    }
});


// console.log(" NavBar.components", NavBar.components)

// NavBar.components = { MenuDropdown, MenuItem, NotUpdatable, ErrorHandler, ProfileSection };
// console.log(" NavBar.components", NavBar.components)
patch(components.NavBar.prototype, 'sh_backmate_theme_adv/static/src/js/navbar.js', {

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */

    // mobileNavbarTabs(...args) {
    //     return [...this._super(...args), {
    //         icon: 'fa fa-comments',
    //         id: 'livechat',
    //         label: this.env._t("Livechat"),
    //     }];
    // }



    onNavBarDropdownItemSelection(ev) {
        const { payload: menu } = ev.detail;
        if (menu) {
            this.menuService.selectMenu(menu);
            // $("body").removeClass("sh_sidebar_background_enterprise");
            // $(".sh_search_container").css("display", "none");
            // $(".sh_backmate_theme_appmenu_div").removeClass("show")
            // $(".o_action_manager").removeClass("d-none");
            // $(".o_menu_brand").css("display", "block");
            // $(".full").removeClass("sidebar_arrow");
            // $(".o_menu_sections").css("display", "flex");


        }
    },
    get_current_company(){
        let current_company_id;
        if (session.user_context.allowed_company_ids) {
            current_company_id = session.user_context.allowed_company_ids[0];
        } else {
            current_company_id = session.user_companies ?
                session.user_companies.current_company :
                false;
        }

        return current_company_id;
    },
    getIconStyle() {


        return icon_style;

    },
    getXmlID(app_id) {
        return this.menuService.getMenuAsTree(app_id).xmlid;
    },
    currentMenuAppSections(app_id) {

        return (
            (this.menuService.getMenuAsTree(app_id).childrenTree) ||
            []
        );
    },



    getThemeStyle(ev) {

        return theme_style;
    },
    isMobile(ev) {
        return config.device.isMobile;
    },
    click_secondary_submenu(ev) {
        if (config.device.isMobile) {
            $(".sh_sub_menu_div").addClass("o_hidden");
        }

        $(".o_menu_sections").removeClass("show")
    },
    click_close_submenu(ev) {
        $(".sh_sub_menu_div").addClass("o_hidden");
        $(".o_menu_sections").removeClass("show")
    },
    click_mobile_toggle(ev) {
        $(".sh_sub_menu_div").removeClass("o_hidden");

    },
    // click_app_toggle(ev) {
    //     console.log(">>>>>>>>>>>>h_backmate_theme_appmenu_div", $(".sh_backmate_theme_appmenu_div"))
    //     if ($(".sh_backmate_theme_appmenu_div").hasClass("show")) {
    //         $("body").removeClass("sh_sidebar_background_enterprise");
    //         $(".sh_search_container").css("display", "none");

    //         $(".sh_backmate_theme_appmenu_div").removeClass("show")
    //         $(".o_action_manager").removeClass("d-none");
    //         $(".o_menu_brand").css("display", "block");
    //         $(".full").removeClass("sidebar_arrow");
    //         $(".o_menu_sections").css("display", "flex");
    //     } else {
    //         $(".sh_backmate_theme_appmenu_div").addClass("show")
    //         $("body").addClass("sh_sidebar_background_enterprise");
    //         $(".sh_backmate_theme_appmenu_div").css("opacity", "1");
    //         //$(".sh_search_container").css("display","block");
    //         $(".o_action_manager").addClass("d-none");
    //         $(".full").addClass("sidebar_arrow");
    //         $(".o_menu_brand").css("display", "none");
    //         $(".o_menu_sections").css("display", "none");
    //     }


    // },


});


