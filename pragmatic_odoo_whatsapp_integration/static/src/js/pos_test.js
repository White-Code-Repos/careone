odoo.define('pragmatic_odoo_whatsapp_integration.pos', function (require) {
'use strict';

var models = require('point_of_sale.models');
var core = require('web.core');
var screens = require('point_of_sale.screens');
var Widget = require('web.Widget');

var ajax = require('web.ajax');

var qweb = core.qweb;
screens.ReceiptScreenWidget.include({

    renderElement: function() {
        var self = this;
        this._super();
        this.$('.js_custom_print').click(function(){
            self.click_custom_print();


        });
    },
    click_custom_print: function(){
        var order = this.pos.get_order();
        var order_list = this.pos.get_order_list();

        // Render receipt screen and can print function
        var value = {
            'order': order.name,
            'formatted_validation_date': order.formatted_validation_date,
            'company_name': this.pos.company.name,
            'company_phone': this.pos.company.phone,
            'user_name': this.pos.user.name,
//            'order_lines': order_list[0].orderlines.models

            }
             $.ajax({
            url : '/whatsapp/send/message',
            data : value,
            type: "POST",

            success: function (data) {
            alert("Whatsapp Message Send Sucessfully");
            }


 });

    }
});

});