var fig_heatmap_worldcdt = {
    plot_id: 'fig_heatmap_worldcdt',
    plot_dict: null,
    plot_type: 'plotly',
    
    colorbar_title: 'Days',
    cdt_max: 50,
    colorscale: {
        CDT: [
            [0, 'rgba(255, 0, 0, 0.6)'],
            [0.5, 'rgba(255, 255, 0, 0.6)'],
            [1, 'rgba(144, 238, 144, 0.6)']
        ],
    },
    data: null,
    fmt_comma: d3.format(","),
    data_file: 'world-data-latest.json',

    get_color: function(v) {
        if (v>=0) { return 'green'; }
        else { return 'red'; }
    },

    get_sign: function(v) {
        if (v>0) {
            return '+';
        } else {
            return '';
        }
    },
    

    load: function() {
        $.get(
            './covid_data/dsvm/' + this.data_file, 
            {ver: Math.random()},
            function(data) {
                fig_heatmap_worldcdt.init(data);
            },
            'json'
        );
    },

    init: function(data) {
        this.data = data;
        var date = data.date;
        var rows = data.data;
        var mydata = [];
        for (const country in rows) {
            if (rows.hasOwnProperty(country)) {
                const obj = rows[country];
                // console.log('* country: ' + country);
                
                var cdt = obj.cdts[obj.cdts.length - 1];
                var ncc = obj.nccs[obj.nccs.length - 1];
                var dth = obj.dths[obj.dths.length - 1];
                var d_ncc = obj.news[obj.news.length - 1];
                var d_dth = dth - obj.dths[obj.dths.length - 2];
                var sdr = obj.sdrs[obj.sdrs.length - 1] * 100;
                var cdr = '--';
                if (ncc > 0) {
                    cdr = dth / ncc * 100;
                    cdr = cdr.toFixed(1) + '%';
                }
                if (cdt == null) { cdt = this.cdt_max; }
                var r = {
                    country: country,
                    cdt: obj.cdts[obj.cdts.length - 1],
                    txt: "<b>" + country + '</b> on ' + date + '<br>' + 
                        'CDT: <b>' + cdt.toFixed(1) + '</b> days <br>' +
                        'Total Cases:  <b>' + this.fmt_comma(ncc) + 
                            ' (' + this.get_sign(d_ncc) + this.fmt_comma(d_ncc) + ')</b><br>' + 
                        'Total Deaths:  <b>' + this.fmt_comma(dth) + 
                            ' (' + this.get_sign(d_dth) + this.fmt_comma(d_dth) + ')</b><br>' + 
                        'Death Rate:  <b>' + cdr + '</b><br>' + 
                        'Death Rate(4-day Smoothed): <b>'+ sdr.toFixed(1) + '%</b>'
                }
                mydata.push(r);
            }
        }
        
        var plot_data = [{
            name: 'Country<br>Data',
            type: 'choropleth',
            locationmode: 'country names',
            locations: this.unpack(mydata, 'country'),
            z: this.unpack(mydata, 'cdt'),
            text: this.unpack(mydata, 'txt'),
            hovertemplate: '%{text}',
            
            zmin: 0,
            zmid: this.cdt_max / 2,
            zmax: this.cdt_max,
            colorscale: this.colorscale.CDT,
            colorbar: {
                title: this.colorbar_title,
                thickness: 15,
                len: .4,
                x: 0.05,
                y: 0.35,
                nticks: 6
            }
        }];
        
        this.plot_dict = {
            data: plot_data,
            layout: {
                height: this.get_height(),
                margin: { t: 10 , b: 10, l: 12, r: 12},
                geo: {
                    resolution: 50,
                    projection: {
                        type: 'equirectangular'
                    }
                }
            }
        };

        Plotly.newPlot(
            this.plot_id, 
            this.plot_dict.data,
            this.plot_dict.layout,
            {responsive: true}
        );
        // update the last update
        $('#' + this.plot_id + '_last_update').html(data.date);

        this.bind_click_event();
    },
    

    bind_click_event: function() {
        // bind click events
        this.plot_elm = document.getElementById(this.plot_id);
        this.plot_elm.on('plotly_click', function(data) {
            var nation = data.points[0].location;
            jarvis.add_nation_series(nation);
        });
    },

    get_width: function() {
        var w = $('#' + this.plot_id).css('width');
        return parseFloat(w.substring(0, w.length-2));
    },

    get_height: function() {
        var h = $('#' + this.plot_id).css('height');
        h = parseFloat(h.substring(0, h.length-2));

        if (h >= 300) {
            return h;
        } else {
            var width = this.get_width();
            if (width > 500) {
                return width * 0.5;
            } else {
                return 300;
            }
        }
    },
    

    unpack: function(rows, key) {
        return rows.map(function(row) {
            return row[key];
        });
    }

};
// bind this to the global plots object
if (typeof(plots) == 'undefined') {

} else {
    plots[fig_heatmap_worldcdt.plot_id] = fig_heatmap_worldcdt;
}