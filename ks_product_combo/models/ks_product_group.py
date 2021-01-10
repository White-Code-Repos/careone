from collections import defaultdict
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.exceptions import ValidationError,UserError


class KsProductGroup(models.Model):
    _name = 'ks.product.group'
    _description = 'Grouped Products'

    ks_product_id = fields.Many2one('product.template', string="Products", domain=[('ks_is_combo', '=', False)],
                                    required=True)
    ks_sell_price = fields.Float('Selling Price', related='ks_product_id.list_price', readonly=1, store=True)
    ks_cost_price = fields.Float('Cost Price', compute='_ks_compute_cost', readonly=1, store=True)
    ks_item_quantity = fields.Integer('Quantity', default=1)
    ks_total_amount = fields.Float('Total Amount', compute='_ks_compute_total_amount', store=True)

    @api.depends('ks_sell_price', 'ks_item_quantity', 'ks_product_id')
    def _ks_compute_total_amount(self):
        """"
            Compute the total amount = item quantity * sales price
        """
        for child_product in self:
            child_product.ks_total_amount = child_product.ks_sell_price * child_product.ks_item_quantity

    @api.depends('ks_product_id')
    def _ks_compute_cost(self):
        """"
            Compute the total amount = item quantity * sales price
        """
        for child_product in self:
            child_product.ks_cost_price = child_product.ks_product_id.product_variant_id.standard_price


class KsproductTemplate(models.Model):
    _inherit = ['product.template']

    ks_is_combo = fields.Boolean('Combo Product', default=False, store=True)
    type = fields.Selection(selection_add=[('product', 'Storable Product'),
                                           ('combo', 'Combo Product')
                                           ], )
    ks_product_child_ids = fields.Many2many('ks.product.group', string="Associated Products", required=1)

    @api.onchange('ks_is_combo', 'type')
    def _check_ks_is_combo(self):
        """
        Manage product type: if product is combo, then product type must also be combo product
        """
        if self.ks_is_combo:
            self.type = 'combo'
            self.purchase_ok = False
            if not self.invoice_policy:
                self.invoice_policy = 'order'
            self.service_type = 'manual'
        if (not self.ks_is_combo) and self.type == 'combo':
            self.type = 'product'

        return

    @api.constrains('type', 'ks_is_combo', 'purchase_ok')
    def _check_product_type(self):
        # Check Product Type: Combo Product or not

        if self.ks_is_combo and self.purchase_ok:
            raise ValidationError('Cannot Purchase a combo product')
        if self.type == 'combo' and (not self.ks_is_combo):
            raise ValidationError('Please tick the combo product or select another product type')
        if (not self.type == 'combo') and self.ks_is_combo:
            self.type = 'combo'

        if self.ks_is_combo and not self.ks_product_child_ids:
            raise ValidationError('Please add some combo items in the combo product')
        return

    @api.onchange('ks_product_child_ids')
    def check_valid_ks_product(self):

        #Check valid combo items and their quantity in combo product

        if self.ks_is_combo:
            for child_product in self.ks_product_child_ids:
                if child_product.ks_product_id.type in ['product']:
                    if (child_product.ks_product_id.qty_available < child_product.ks_item_quantity):
                        raise ValidationError('Quantity of %s exceeds their available quantity'
                                         % (child_product.ks_product_id.name))
                    if not child_product.ks_item_quantity:
                        raise ValidationError('Please enter the valid quantity for %s '
                                              % (child_product.ks_product_id.name))
                if child_product.ks_product_id.ks_product_child_ids:
                    raise ValidationError("Sorry! You are not allowed to add a combo product"
                                          " inside another combo product")

    @api.constrains('ks_product_child_ids')
    def _ks_check_sell_price(self):
        """"
            Validate Sales Price and the items in combo for Combo Product
        """
        if self.ks_is_combo and (self.list_price <= 1.00):
            self.list_price = sum(self.ks_product_child_ids.mapped('ks_total_amount'))

    standard_price = fields.Float(
        'Cost', compute='_compute_standard_price',
        inverse='_set_standard_price', search='_search_standard_price',
        digits='Product Price', groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
            In FIFO: value of the last unit that left the stock (automatically computed).
            Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
            Used to compute margins on sale orders.""")

    @api.depends('product_variant_ids', 'product_variant_ids.standard_price', 'ks_product_child_ids')
    def _compute_standard_price(self):
        # Do not Update cost price of Combo Products
        for product in self:
            if product.ks_is_combo:
                cost_price = 0.00
                for child_product in product.ks_product_child_ids:
                    cost_price = cost_price + child_product.ks_cost_price * child_product.ks_item_quantity
                product.standard_price = cost_price
                for variants in product.product_variant_ids:
                    variants.standard_price = cost_price
            else:
                unique_variants = product.filtered(lambda template: len(template.product_variant_ids) == 1)
                for template in unique_variants:
                    template.standard_price = template.product_variant_ids.standard_price
                for template in (product - unique_variants):
                    template.standard_price = 0.0


class KsStockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_pull(self, procurements):

        ks_check_combo = False

        moves_values_by_company = defaultdict(list)
        mtso_products_by_locations = defaultdict(list)
        """
        Create the movelines for all the combo items if the product is combo product :
        """
        for procurement, rule in procurements:
            if not rule.location_src_id:
                msg = _('No source location defined on stock rule: %s!') % (rule.name,)
                raise UserError(msg)

            if rule.procure_method == 'mts_else_mto':
                mtso_products_by_locations[rule.location_src_id].append(procurement.product_id.id)

        # Get the forecasted quantity for the `mts_else_mto` procurement.
        forecasted_qties_by_loc = {}
        for location, product_ids in mtso_products_by_locations.items():
            products = self.env['product.product'].browse(product_ids).with_context(location=location.id)
            forecasted_qties_by_loc[location] = {product.id: product.virtual_available for product in products}

        # Prepare the move values, adapt the `procure_method` if needed.
        for procurement, rule in procurements:
            procure_method = rule.procure_method
            if rule.procure_method == 'mts_else_mto':
                qty_needed = procurement.product_uom._compute_quantity(procurement.product_qty,
                                                                       procurement.product_id.uom_id)
                qty_available = forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id]
                if float_compare(qty_needed, qty_available,
                                 precision_rounding=procurement.product_id.uom_id.rounding) <= 0:
                    procure_method = 'make_to_stock'
                    forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id] -= qty_needed
                else:
                    procure_method = 'make_to_order'

            move_values = rule._get_stock_move_values(*procurement)
            move_values['procure_method'] = procure_method

            #Create move lines for the combo items of the combo products

            if procurement.product_id.ks_is_combo:
                for child in procurement.product_id.ks_product_child_ids.filtered\
                            (lambda x: x.ks_product_id.product_variant_id.type not in ['service', 'combo']):
                    ks_move_values = move_values.copy()
                    ks_move_values['name'] = child.ks_product_id.product_variant_id.name
                    ks_move_values['product_id'] = child.ks_product_id.product_variant_id.id
                    ks_move_values['product_uom_qty'] = child.ks_item_quantity * move_values['product_uom_qty']
                    ks_move_values['product_type'] = child.ks_product_id.product_variant_id.type
                    moves_values_by_company[procurement.company_id.id].append(ks_move_values)

            else:
                moves_values_by_company[procurement.company_id.id].append(move_values)

        for company_id, moves_values in moves_values_by_company.items():
            moves = self.env['stock.move'].sudo().with_context(force_company=company_id).create(moves_values)
            moves._action_confirm()

        return True


class KsSaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ks_previous_product_qty = fields.Float(string='Previous Order Quantity', default=0.0)

    def write(self, values):
        #store previous qunatity of combo product
        if 'product_uom_qty' in values:
            self.ks_previous_product_qty = self.product_uom_qty
        res = super(KsSaleOrderLine, self).write(values)
        return res

    @api.constrains('product_id')
    def ks_check_combo_item(self):
        for ks_product in self:
            if ks_product.product_id.ks_is_combo and not ks_product.product_id.ks_product_child_ids:
                raise ValueError('%s do not have any combo items' % ks_product.product_id.name)

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        # When modifying a one2many, _origin doesn't guarantee that its values will be the ones
        # in database. Hence, we need to explicitly read them from there.
        if self._origin:
            product_uom_qty_origin = self._origin.read(["product_uom_qty"])[0]["product_uom_qty"]
        else:
            product_uom_qty_origin = 0
        #check product type as combo to update its quantity
        if self.state == 'sale' and self.product_id.type in ['product', 'consu', 'combo'] \
                and self.product_uom_qty < product_uom_qty_origin:
            if self.product_uom_qty < self.qty_delivered:
                return {}
            warning_mess = {
                'title': ('Ordered quantity decreased!'),
                'message': ('You are decreasing the ordered quantity!'
                            ' Do not forget to manually update the delivery order if needed.'),
            }
            return {'warning': warning_mess}
        return {}

    @api.depends('product_id')
    def _compute_qty_delivered_method(self):
        """ Compute delivered quantity for combo products
        """
        super(KsSaleOrderLine, self)._compute_qty_delivered_method()

        for line in self:
            if not line.is_expense and line.product_id.type in ['consu', 'combo', 'product']:
                line.qty_delivered_method = 'stock_move'

    def ks_action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in self:
            if line.state != 'sale' or not line.product_id.type in ('consu', 'product', 'combo'):
                continue
            if line.product_id.ks_is_combo:
                qty = line.ks_previous_product_qty
            else:
                qty = line._get_qty_procurement()
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            procurements.append(self.env['procurement.group'].Procurement(
                line.product_id, product_qty, procurement_uom,
                line.order_id.partner_shipping_id.property_stock_customer,
                line.name, line.order_id.name, line.order_id.company_id, values))
        if procurements:
            self.env['procurement.group'].run(procurements)
        return True

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        If the product is a combo product then execute ks_action_launch_stock_rule function
                    else call the parent function
        """
        ks_check_combo = False
        for ks_prod in self:
            if ks_prod.product_id.ks_is_combo:
                ks_check_combo = True

        if ks_check_combo:
            res = self.ks_action_launch_stock_rule(previous_product_uom_qty=previous_product_uom_qty)
            orders = list(set(x.order_id for x in self))
            for order in orders:
                reassign = order.picking_ids.filtered(
                    lambda x: x.state == 'confirmed' or (x.state in ['waiting', 'assigned'] and not x.printed))
                if reassign:
                    reassign.action_assign()
        else:
            res = super(KsSaleOrderLine, self)._action_launch_stock_rule()
        return res

    def _update_line_quantity(self, values):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        line_products = self.filtered(lambda l: l.product_id.type == 'combo')
        if line_products.mapped('qty_delivered') and float_compare(values['product_uom_qty'],
                                                                   max(line_products.mapped('qty_delivered')),
                                                                   precision_digits=precision) == -1:
            raise UserError(_('You cannot decrease the ordered quantity below the delivered quantity.\n'
                              'Create a return first.'))
        super(KsSaleOrderLine, self)._update_line_quantity(values)

    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_delivered(self):
        super(KsSaleOrderLine, self)._compute_qty_delivered()

        #Compute delivered quantity for the combo products

        for line in self:
            if line.qty_delivered_method == 'stock_move':
                qty = 0.0
                if line.product_id.ks_is_combo and line.product_id.ks_product_child_ids:
                    ks_total_child_qty = 0.0
                    for ks_product_child in line.product_id.ks_product_child_ids:
                        if ks_product_child.ks_product_id.product_variant_id.type in ['product', 'consu']:
                            ks_total_child_qty += ks_product_child.ks_item_quantity

                    for move in line.move_ids.filtered(
                            lambda r: r.state == 'done' and not r.scrapped):
                        if move.location_dest_id.usage == "customer":
                            if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                                qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        elif move.location_dest_id.usage != "customer" and move.to_refund:
                            qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                    ks_combo_child_qty = ks_total_child_qty if ks_total_child_qty else 1.0
                    qty = qty // ks_combo_child_qty
                else:
                    for move in line.move_ids.filtered(
                            lambda r: r.state == 'done' and not r.scrapped and line.product_id == r.product_id):
                        if move.location_dest_id.usage == "customer":
                            if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                                qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        elif move.location_dest_id.usage != "customer" and move.to_refund:
                            qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                line.qty_delivered = qty
