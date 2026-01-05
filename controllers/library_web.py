from odoo import http
from odoo.http import request

class LibraryWebsiteController(http.Controller):

    @http.route(['/library/books'], type='http', auth='public', website=True)
    def library_books_page(self, **kw):
        books = request.env['library.book'].sudo().search([])
        return request.render('Library_Manager.library_books_page', {'books': books})
