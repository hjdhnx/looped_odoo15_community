/** @odoo-module **/
import { Dropdown } from '@web/core/dropdown/dropdown';

import { patch } from 'web.utils';
const { Component, core, hooks, useState, QWeb } = owl;
const components = { Dropdown };
const { onWillStart, useExternalListener, useRef, useSubEnv } = hooks;
import { useBus, useEffect, useService } from "@web/core/utils/hooks";
import { usePosition } from "@web/core/position/position_hook";
import { useDropdownNavigation } from "@web/core/dropdown/dropdown_navigation_hook";
import { localization } from "@web/core/l10n/localization";

var rpc = require("web.rpc");
var config = require("web.config");
var theme_style = 'style4';
const DIRECTION_CARET_CLASS = {
    bottom: "dropdown",
    top: "dropup",
    left: "dropleft",
    right: "dropright",
};




patch(components.Dropdown.prototype, 'sh_backmate_theme/static/src/js/dropdown.js', {

    setup() {
        console.log("this.el.parentElement", this, this.props.title)

        if (this.props.title == 'Home Menu' && theme_style == 'style4') {
            this.state = useState({
                open: true,
                groupIsOpen: this.props.startOpen,
            });
        } else {
            this.state = useState({
                open: this.props.startOpen,
                groupIsOpen: this.props.startOpen,
            });
        }


        // Set up beforeOpen ---------------------------------------------------
        onWillStart(() => {
            if (this.state.open && this.props.beforeOpen) {
                return this.props.beforeOpen();
            }
        });

        // Set up dynamic open/close behaviours --------------------------------
        if (!this.props.manualOnly) {
            // Close on outside click listener
            useExternalListener(window, "click", this.onWindowClicked);
            // Listen to all dropdowns state changes
            useBus(Dropdown.bus, "state-changed", this.onDropdownStateChanged);
        }

        // Set up UI active element related behavior ---------------------------
        this.ui = useService("ui");
        useEffect(
            () => {
                Promise.resolve().then(() => {
                    this.myActiveEl = this.ui.activeElement;
                });
            },
            () => []
        );

        // Set up nested dropdowns ---------------------------------------------
        this.hasParentDropdown = this.env.inDropdown;
        useSubEnv({ inDropdown: true });

        // Set up key navigation -----------------------------------------------
        useDropdownNavigation();

        // Set up toggler and positioning --------------------------------------
        this.togglerRef = useRef("togglerRef");
        if (this.props.toggler === "parent") {
            // Add parent click listener to handle toggling
            useEffect(
                () => {
                    const onClick = (ev) => {
                        if (this.el.contains(ev.target)) {
                            // ignore clicks inside the dropdown
                            return;
                        }
                        this.toggle();
                    };
                    this.el.parentElement.addEventListener("click", onClick);
                    return () => {
                        this.el.parentElement.removeEventListener("click", onClick);
                    };
                },
                () => []
            );
        }

        // Setup positioning only when in desktop
        if (!this.env.isSmall) {
            /** @type {string} **/
            let position =
                this.props.position || (this.hasParentDropdown ? "right-start" : "bottom-start");
            let [direction, variant = "middle"] = position.split("-");
            if (localization.direction === "rtl") {
                if (["bottom", "top"].includes(direction)) {
                    variant = variant === "start" ? "end" : "start";
                } else {
                    direction = direction === "left" ? "right" : "left";
                }
                position = [direction, variant].join("-");
            }
            this.directionCaretClass = DIRECTION_CARET_CLASS[direction];

            const positioningOptions = {
                popper: "menuRef",
                position,
                directionFlipOrder: { right: "rl", bottom: "bt", top: "tb", left: "lr" },
            };

            // Position menu relatively to parent element
            if (this.props.toggler === "parent") {
                usePosition(() => this.el.parentElement, positioningOptions);
            } else {
                // Position menu relatively to inner toggler
                usePosition(() => this.togglerRef.el, positioningOptions);
            }
        }
    },
    /**
     * Toggles the dropdown open state.
     *
     * @returns {Promise<void>}
     */
    toggle() {

        if (this.props.title == 'Home Menu' && theme_style == 'style4') {
            return this.changeStateAndNotify({ open: true, groupIsOpen: true });
        } else {
            const toggled = !this.state.open;
            return this.changeStateAndNotify({ open: toggled, groupIsOpen: toggled });
        }


    },
    onDropdownStateChanged(args) {
        // NProgress.configure({ showSpinner: false });
        // NProgress.start();
        if (this.props.title == 'Home Menu' && theme_style == 'style4') {
            this.state.open = true;
        }

        if (this.el.contains(args.emitter.el)) {
            // Do not listen to events emitted by self or children
            return;
        }

        // Emitted by direct siblings ?
        if (args.emitter.el.parentElement === this.el.parentElement) {
            // Sync the group status
            this.state.groupIsOpen = args.newState.groupIsOpen;

            // Another dropdown is now open ? Close myself without notifying siblings.
            if (this.state.open && args.newState.open) {
                this.state.open = false;
            }
        } else {
            // Another dropdown is now open ? Close myself and notify the world (i.e. siblings).
            if (this.state.open && args.newState.open) {
                this.close();
            }
        }
        // NProgress.done();
    }

});