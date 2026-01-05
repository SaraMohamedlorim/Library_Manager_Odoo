from odoo import models, fields, api

class LibraryReport(models.AbstractModel):
    _name = 'report.library_manager.book_report'
    _description = 'Library Book Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['library.book'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'library.book',
            'docs': docs,
            'data': data,
        }