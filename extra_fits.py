# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import api, fields, models, _, tools


class InvoiceSaleOrderAnalisisTotal(models.Model):
    _name = "invoice.sale.analysis.total"
    _description = "Analisis de Ventas vs Facturas"
    _auto = False
    _rec_name = 'name'

    id                = fields.Integer(string='Id Orden', size=64, readonly=True)
    name              = fields.Char(string='Referencia Venta', size=64, readonly=True)
    date_order        = fields.Date(string='Fecha Venta', readonly=True)
    so_amount_total   = fields.Float(string='Total Venta', digits=(18,4), readonly=True)     

    customer_name     = fields.Char(string='Cliente', size=64, readonly=True)

    invoice_name      = fields.Char(string='Factura', size=64, readonly=True)
    date_invoice      = fields.Date(string='Fecha Factura', readonly=True)
    inv_amount_total  = fields.Float(string='Total Factura', digits=(18,4), readonly=True)     

    pend_amount_total = fields.Float(string='Pendiente por Facturar', digits=(18,4), readonly=True)     


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)        
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT 
              so.id,
              so.name,
              so.date_order as date_order,
              so.amount_total as so_amount_total,
              rp.name as customer_name,
              inv.name as invoice_name,
              inv.invoice_date as date_invoice,
              inv.amount_total as inv_amount_total,
              so.amount_total - inv.amount_total as pend_amount_total
             -- ->Cruce de Tablas
             FROM sale_order so
             JOIN res_partner rp
               ON rp.id = so.id
             JOIN sale_order_line sol
               ON so.id = sol.order_id
             JOIN sale_order_line_invoice_rel solinv
               ON sol.id = solinv.order_line_id
             JOIN account_move_line aml
               ON aml.id = solinv.invoice_line_id
             JOIN account_move inv
               ON inv.id = aml.move_id
        );""" % (self._table, ))