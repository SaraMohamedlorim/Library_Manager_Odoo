odoo.define('library_manager.chart_manager', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var rpc = require('web.rpc');

var LibraryChartManager = AbstractAction.extend({
    template: 'LibraryChartTemplate',

    init: function(parent, context) {
        this._super(parent, context);
        this.books_data = {};
    },

    willStart: function() {
        var self = this;
        return this._super().then(function() {
            return self._loadChartData();
        });
    },

    _loadChartData: function() {
        var self = this;
        return rpc.query({
            model: 'library.book',
            method: 'search_read',
            domain: [],
            fields: ['status']
        }).then(function(result) {
            self.books_data = result;
            self._renderChart();
        });
    },

    _renderChart: function() {
        // Implement chart rendering using Chart.js or other library
        var available = this.books_data.filter(function(book) {
            return book.status === 'available';
        }).length;
        var borrowed = this.books_data.filter(function(book) {
            return book.status === 'checked_out';
        }).length;

        // Chart rendering code here
        console.log('Available:', available, 'Borrowed:', borrowed);
    }
});

core.action_registry.add('library_chart_action', LibraryChartManager);

return {
    LibraryChartManager: LibraryChartManager
};

});