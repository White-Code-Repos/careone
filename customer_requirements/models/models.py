# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CustomerQuestions(models.Model):
    _name = 'customer.questions'
    _rec_name = 'question'
    sequence = fields.Char('', size=32, required=True, readonly=True, default=lambda self: _('New'),
                           track_visibility='onchange')

    @api.model
    def create(self, waltz):
        if waltz:
            waltz['sequence'] = self.env['ir.sequence'].next_by_code('question')
        return super(CustomerQuestions, self).create(waltz)

    question = fields.Text(string="Question", required=False, )
    answer_type = fields.Selection(string="Answer Type", selection=[('multi', 'Multi Selection'), ('bol', 'Yes or No'),
                                                                    ('text', 'Free Text')], required=True, )
    answer_ids = fields.One2many(comodel_name="multi.answer", inverse_name="question_id", string="", required=False, )


class SalesQuestion(models.Model):
    _name = 'sale.question'

    # @api.model
    # def service_id_domain(self):
    #     my_orders = self.env['sale.order.line'].search([('order_id', '=', self.sale_id.id)])
    #     print(self.sale_id)
    #     print(my_orders)
    #     my_products = []
    #     for order in my_orders:
    #         my_products.append(order.product_id.id)
    #     return [('id', 'in', my_products)]

    @api.onchange('service_id')
    def service_id_domain_x(self):
        return {'domain': {'service_id': [('id', 'in', self.sale_id.order_products_ids.ids)]}}

    question_id = fields.Many2one(comodel_name="customer.questions", string="Question", required=False, )
    answer_type = fields.Selection(string="Answer Type", selection=[('multi', 'Multi Selection'), ('bol', 'Yes or No'),
                                                                    ('text', 'Free Text')],
                                   related='question_id.answer_type')
    # question = fields.Text(string="Question", required=False, related='question_id.question')
    multi_answer_id = fields.Many2one(comodel_name="multi.answer", string="Multi Selection", required=False,
                                      domain="[('question_id','=',question_id)]")
    boolean_answer = fields.Selection(string="Yes or No", selection=[('y', 'Yes'), ('n', 'No'), ], required=False, )
    text_answer = fields.Text(string="Free Text", required=False, )
    sale_id = fields.Many2one(comodel_name="sale.order", string="", required=False, )
    service_id = fields.Many2one(comodel_name="product.product", string="Service", required=False, )
    mrp_id = fields.Many2one(comodel_name="mrp.production", string="", required=False, )


class SalesOrderInherit(models.Model):
    _inherit = 'sale.order'
    questions_ids = fields.One2many(comodel_name="sale.question", inverse_name="sale_id", string="", required=False, )
    order_products_ids = fields.Many2many(comodel_name="product.product", compute="get_order_products_ids", store=True)

    @api.depends('order_line')
    def get_order_products_ids(self):
        products = []
        for rec in self.order_line:
            products.append(rec.product_id.id)
        self.order_products_ids = products


class MrpProductionInherit(models.Model):
    _inherit = 'mrp.production'
    questions_ids = fields.One2many(comodel_name="sale.question", inverse_name="mrp_id", string="", required=False,
                                    compute='get_value_from_sale_questions_ids', store=False, index=False)

    @api.depends('origin')
    def get_value_from_sale_questions_ids(self):
        for rec in self:
            sale_order = self.env['sale.order'].search([('name', '=', rec.origin)], order='id desc', limit=1)
            if sale_order:
                rec.questions_ids = sale_order.questions_ids
            else:
                rec.questions_ids = False


class MultiSelectionAnswer(models.Model):
    _name = 'multi.answer'
    _rec_name = 'answer'
    answer = fields.Char(string='Answer')
    question_id = fields.Many2one(comodel_name="customer.questions", string="", required=False, )
