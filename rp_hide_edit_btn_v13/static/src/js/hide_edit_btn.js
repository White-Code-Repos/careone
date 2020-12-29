odoo.define('rp_hide_edit_btn_v13.hide_edit_btn', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var core = require('web.core');
    var _t = core._t;

    FormController.include({

        /**
         * @private
         */
        _updateButtons: function () {
            var self = this;
            this._super.apply(this, arguments);
            if (this.$buttons && this.mode === 'readonly') {
                var attrs = this.renderer.arch.attrs;
                var action_edit = ['edit', 'create'];
                _.each(action_edit, function (action) {
                    var expr = attrs['rp_' + action];
                    var res = expr ? self._evalExpression(expr) : self.activeActions[action];
                    self.$buttons.find('.o_form_button_' + action).toggleClass('o_hidden', !res);
                });
            }
        },

        _evalExpression: function (expr) {
            //https://openerp-web-v7.readthedocs.io/en/stable/#convert-js
            var tokens = py.tokenize(expr);
            var tree = py.parse(tokens);
            var evalcontext = this.renderer.state.evalContext
            var expr_eval = py.evaluate(tree, evalcontext);
            return py.PY_isTrue(expr_eval);
        }
    });
});
