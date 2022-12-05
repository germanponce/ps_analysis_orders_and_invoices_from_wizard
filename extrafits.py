# -*- coding: utf-8 -*-
# Coded by German Ponce Dominguez 
#     ▬▬▬▬▬.◙.▬▬▬▬▬  
#       ▂▄▄▓▄▄▂  
#    ◢◤█▀▀████▄▄▄▄▄▄ ◢◤  
#    █▄ █ █▄ ███▀▀▀▀▀▀▀ ╬  
#    ◥ █████ ◤  
#     ══╩══╩═  
#       ╬═╬  
#       ╬═╬ Dream big and start with something small!!!  
#       ╬═╬  
#       ╬═╬ You can do it!  
#       ╬═╬   Let's go...
#    ☻/ ╬═╬   
#   /▌  ╬═╬   
#   / \
# Cherman Seingalt - german.ponce@outlook.com

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round
from odoo.tools.float_utils import float_compare
import datetime
import calendar

import tempfile

import xlwt
from io import BytesIO
import base64

from itertools import zip_longest

import logging
_logger = logging.getLogger(__name__)

logger_debug = False

format_date = "%Y-%m-%d"

class PsWizardReportMovesBySupplier(models.TransientModel):
    _name = 'ps.wizard.report.moves.by.supplier'
    _description = 'Asistente Pagos por Proveedor'

    def _get_date(self):
        currentDate = datetime.date.today()
        firstDayOfMonth = datetime.date(currentDate.year, currentDate.month, 1)
        return firstDayOfMonth

    def _get_date_end(self):
        currentDate = datetime.date.today()
        lastDayOfMonth = datetime.date(currentDate.year, currentDate.month, calendar.monthrange(currentDate.year, currentDate.month)[1])
        return lastDayOfMonth

    date       = fields.Date(string='Fecha Inicio', default=_get_date, required=True)
    date_stop  = fields.Date(string='Fecha fin', default=_get_date_end, required=True)

    get_info_by = fields.Selection([
                                     ('product','Producto'),
                                     ('category','Categoria'),
                                     ('user','Agente'),
                                     ('all','Sin filtro (Todo)'),
                                    ], 'Obtener por')


    partner_id = fields.Many2one('res.partner', 'Proveedor')

    output_type = fields.Selection([
                                     ('view','Análisis Odoo'),
                                     ('pdf','PDF')
                                    ], 'Tipo Informe', default="pdf")

    def get_current_report(self):
        self.clear_tables()
        report_id = self.insert_data()
        if self.output_type == 'view':
            data_list_ids = self.get_row_ids()
            return {
                'domain': [('id', 'in', data_list_ids)],
                'name': 'Reporte de Pagos por Proveedor',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'context': {'tree_view_ref': 'ps_analysis_orders_and_invoices_from_wizard.ps_table_report_moves_by_supplier_tree'},
                'res_model': 'ps.table.report.moves.by.supplier',
                'type': 'ir.actions.act_window'
                }
        else:
            return self.env.ref('ps_analysis_orders_and_invoices_from_wizard.report_moves_by_supplier_act').report_action(report_id)
        return True

    def get_row_ids(self):
        cr = self.env.cr
        data_list_ids = []
        cr.execute("""
            select id from ps_table_report_moves_by_supplier where user_id=%s;
            """, (self.env.user.id, ))
        cr_res = cr.fetchall()
        if cr_res and cr_res[0] and cr_res[0][0]:
            data_list_ids = [x[0] for x in cr_res]
        else:
            raise UserError("No existe información.")
        return data_list_ids


    def clear_tables(self):
        cr = self.env.cr

        ##### limpiamos la tabla temporal #####
        cr.execute("""
            delete from ps_table_report_moves_by_supplier_header where user_id=%s;
            """,(self.env.user.id, ))

        ##### limpiamos la tabla temporal #####
        cr.execute("""
            delete from ps_table_report_moves_by_supplier where user_id=%s;
            """,(self.env.user.id, ))

        ##### limpiamos la tabla temporal #####
        cr.execute("""
            delete from moves_by_supplier_account_move_line where user_id=%s;
            """,(self.env.user.id, ))
        return True

    def insert_data(self):
        cr = self.env.cr
        current_user_id = self.env.user.id
        
        invoice_obj = self.env['account.move'].sudo()

        partner_obj = self.env['res.partner'].sudo()

        report_header_obj = self.env['ps.table.report.moves.by.supplier.header']
        
        move_by_partner_obj = self.env['ps.table.report.moves.by.supplier']

        move_by_partner_line_obj = self.env['moves.by.supplier.account.move.line']

        vals = {
                    'report_name': str(self.date) + " || " + str(self.date_stop) + " || " + str(self.env.user.login),
                    'date': self.date,
                    'date_stop': self.date_stop,
                    'user_id': self.env.user.id,
                    'partner_id': self.partner_id.id if self.partner_id else False,
                }
        report_new = report_header_obj.create(vals)
        report_id = report_new.id
        date_start = str(self.date)
        date_stop = str(self.date_stop)

        partner_ids = []
        date_sort_list = []
        move_list_vals = []

        if self.partner_id:
            partner_ids = [self.partner_id.id]

        else:
            
            cr.execute("""
                select partner_id from account_move
                         where move_type='in_invoice' and
                         state not in ('draft', 'cancel') and
                  invoice_date between '%s' and '%s'
                  group by partner_id;
                """ % (date_start, date_stop,))

            cr_res = cr.fetchall()
            if cr_res and cr_res[0] and cr_res[0][0]:
                partner_ids = [x[0] for x in cr_res]

        for partner in partner_ids:
            partner_br = partner_obj.browse(partner)
            line_vals = {
                            'partner_id': partner,
                            'user_id': current_user_id,
                            'report_id': report_id,
                    }
            line_new = move_by_partner_obj.create(line_vals)
            line_id = line_new.id

            ### Sacamos los Datos de Pagos ####
            cr.execute("""
                SELECT
                      move.name,
                      move.date,
                      ARRAY_AGG(DISTINCT invoice.id) AS invoice_ids,
                      payment.amount,
                      move.ref,
                      move.currency_id
                  FROM account_payment payment
                  JOIN account_move move ON move.id = payment.move_id
                  JOIN account_move_line line ON line.move_id = move.id
                  JOIN account_partial_reconcile part ON
                      part.debit_move_id = line.id
                      OR
                      part.credit_move_id = line.id
                  JOIN account_move_line counterpart_line ON
                      part.debit_move_id = counterpart_line.id
                      OR
                      part.credit_move_id = counterpart_line.id
                  JOIN account_move invoice ON invoice.id = counterpart_line.move_id
                  JOIN account_account account ON account.id = line.account_id
                  WHERE account.internal_type IN ('receivable', 'payable')
                      AND line.id != counterpart_line.id
                      AND invoice.move_type  = 'in_invoice'
                      AND move.date  between %s and %s
                      AND invoice.partner_id = %s
                  GROUP BY payment.id, move.date, move.name, move.ref, move.currency_id;
                """, (date_start, date_stop, partner))
            cr_res = cr.fetchall()
            if cr_res and cr_res[0] and cr_res[0][0]:
                supplier_amount_total = 0.0
                for pvals in cr_res:
                    tag_info =  pvals[0]
                    move_vals = {
                                    'date': str(pvals[1]),
                                    'invoice_name': pvals[4],
                                    'concept': 'payment',
                                    'tags': tag_info,
                                    'debit': 0.0,
                                    'credit': abs(pvals[3]) * -1,
                                    'residual': abs(pvals[3]) * -1,
                                    'payment_amount': abs(pvals[3]),
                                    'currency_id': pvals[5],
                                    'user_id': current_user_id,
                                    'line_id': line_id,
                                }
                    supplier_amount_total += abs(pvals[3])

                    date_sort_list.append(str(pvals[2]))
                    move_list_vals.append(move_vals)
                    move_result_id = move_by_partner_line_obj.create(move_vals)
                
                line_new.supplier_amount_total = supplier_amount_total

        if not move_list_vals:
            raise UserError("Error no existe información.")

        return report_id

class PsTableReportMovesBySupplierHeader(models.Model):
    _name = 'ps.table.report.moves.by.supplier.header'
    _description = 'Tabla Temporal - Pagos por Proveedor'

    def _get_current_user(self):
        return self.env.user.id


    def _get_current_company(self):
        return self.env.company.id

    def _get_current_date(self):
        return fields.Date.context_today(self)

    company_id = fields.Many2one('res.company', 'Compañia', default=_get_current_company)
    report_name = fields.Char('Nombre Reporte')

    date       = fields.Date(string='Fecha Inicio' )
    date_stop  = fields.Date(string='Fecha fin' )
    line_ids = fields.One2many('ps.table.report.moves.by.supplier', 'report_id', 'Lineas Informe')

    user_id = fields.Many2one('res.users', 'Creado Por')

    partner_id = fields.Many2one('res.partner', 'Cliente')

    current_date  = fields.Date(string='Fecha Inicio', default=_get_current_date)


class PsTableReportMovesBySupplier(models.Model):
    _name = 'ps.table.report.moves.by.supplier'
    _description = 'Tabla Temporal - Pagos por Proveedor'
    _rec_name = "partner_id"


    def _get_current_company(self):
        return self.env.company.id

    company_id = fields.Many2one('res.company', 'Compañia', default=_get_current_company)

    partner_id = fields.Many2one('res.partner', 'Cliente')

    line_ids = fields.One2many('moves.by.supplier.account.move.line', 'line_id', 'Lineas Informe')

    user_id = fields.Many2one('res.users', 'Creado Por')
    report_id = fields.Many2one('ps.table.report.moves.by.supplier.header', 'Header Reporte')


    supplier_amount_total = fields.Monetary('Total Proveedor')

    currency_id = fields.Many2one('res.currency', 'Moneda', related="company_id.currency_id")

    def get_lines_sort(self):
        cr = self.env.cr
        
        line_id = self.id

        move_by_partner_line_obj = self.env['moves.by.supplier.account.move.line']

        cr.execute("""
            select id from moves_by_supplier_account_move_line
                     where line_id=%s order by date, id;
            """,(line_id, ))
        cr_res = cr.fetchall()
        res_ids = [x[0] for x in cr_res]
        move_by_partner_line_ids = move_by_partner_line_obj.browse(res_ids)
        return move_by_partner_line_ids

class MovesBySupplierAccountMoveLine(models.Model):
    _name = 'moves.by.supplier.account.move.line'
    _description = 'Tabla Temporal - Pagos por Proveedor Lineas'
    _rec_name = "invoice_name"
    _order = "date"

    date = fields.Date('Fecha')

    invoice_name = fields.Char('Factura')


    concept = fields.Selection([
                                     ('invoice','Factura'),
                                     ('payment','Pago'),
                                     ('other','Otro'),
                                    ], 'Concepto')

    debit = fields.Monetary('Debe')
    credit = fields.Monetary('Haber')

    residual = fields.Monetary('Saldo')

    payment_amount = fields.Monetary('Pago')

    currency_id = fields.Many2one('res.currency', 'Moneda')

    tags = fields.Char('# Cheque')

    user_id = fields.Many2one('res.users', 'Creado Por')
    line_id = fields.Many2one('ps.table.report.moves.by.supplier', 'Linea Informe')