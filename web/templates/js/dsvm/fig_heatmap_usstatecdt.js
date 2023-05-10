var fig_heatmap_usstatecdt = {
    plot_id: 'fig_heatmap_usstatecdt',
    plot_elm: null,
    plot_dict: null,
    plot_type: 'plotly',
    data: null,
    data_file: 'usstate-data-latest.json',
    mapbox: {
        accesstoken: 'pk.eyJ1IjoiaGVodWFuMjExMiIsImEiOiJjazhudzg2ODgweWJ1M2Zremxub2VoY3MxIn0.JEycE3z3q8b7JX8f2XCw3Q',
        style: 'light'
    },
    colorbar_title: 'Days',
    cdt_max: 50,
    colorscale: {
        CDT: [
            [0, 'rgba(255, 0, 0, 0.7)'],
            [0.5, 'rgba(255, 255, 0, 0.7)'],
            [1, 'rgba(144, 238, 144, 0.7)']
        ],
    },
    fmt_comma: d3.format(","),

    area: {
        default: {
            center: [38, -96],
            zoom: 3.4
        }
    },

    load: function() {
        $.get(
            './covid_data/dsvm/' + this.data_file,
            {ver: Math.random()},
            function(data) {
                fig_heatmap_usstatecdt.init(data);
            }, 'json'
        );
    },

    init: function(data) {
        this.data = data;
        var mydata = this.create_plot_data();

        var plot_data = [];

        plot_data.push({
            name: 'State<br>Data',
            type: 'choropleth',
            locationmode: 'USA-states',
            locations: this.unpack(mydata.regions, 'state'),
            text: this.unpack(mydata.regions, 'txt'),
            z: this.unpack(mydata.regions, 'val'),
            hovertemplate: '%{text}',
            zmin: 0,
            zmid: this.cdt_max/2,
            zmax: this.cdt_max,
            colorscale: this.colorscale.CDT,
            colorbar: {
                title: this.colorbar_title,
                thickness: 15,
                len: .3,
                x: 0.9,
                y: 0.83,
                nticks: 6
            }
        });

        this.plot_dict = {
            data: plot_data,
            layout: {
                height: this.get_height(),
                margin: { t: 10 , b: 10, l: 12, r: 12},
                geo: {
                    scope: 'usa',
                    showlakes: true,
                    lakecolor: 'rgb(255,255,255)'
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
            var state = data.points[0].location;
            jarvis.add_state_series(state);
        });
    },
    
    create_plot_data: function() {
        var date = this.data.date;
        var dates = this.data.dates;
        var rows = this.data.data;
        var mydata = {
            regions: []
        };

        for (const state in rows) {
            if (rows.hasOwnProperty(state)) {
                const obj = rows[state];
                var cdt = obj.cdts[obj.cdts.length - 1];
                var ncc = obj.nccs[obj.nccs.length - 1];
                var dth = obj.dths[obj.dths.length - 1];
                var sdr = obj.sdrs[obj.dths.length - 1] * 100;
                var cdr = dth / ncc * 100;
                var r = {
                    state: state,
                    val: cdt,
                    txt: state + ' on ' + date + ' <br>' +
                        'CDT: ' + cdt.toFixed(1) + ' days (' + obj.d_cdt.toFixed(1) +')<br>' +
                        'Total Cases: ' + this.fmt_comma(ncc) + ' (' + obj.d_ncc.toFixed(0) + ')<br>' + 
                        'Total Death: ' + this.fmt_comma(dth) + ' (' + obj.d_dth.toFixed(0) + ')<br>' + 
                        'Death Rate: ' + cdr.toFixed(1) + '%<br>' + 
                        'Death Rate(4-day Smoothed): ' + sdr.toFixed(1) + '%<br>'
                };
                mydata.regions.push(r);
            }
        }

        return mydata;
    },

    unpack: function(rows, key) {
        return rows.map(function(row) {
            return row[key];
        });
    },


    get_width: function() {
        var w = $('#' + this.plot_id).css('width');
        w = parseFloat(w.substring(0, w.length-2));
        console.log('* ' + this.plot_id + ' width: ' + w);
        
        var widths = [];
        if (w < 100) {
            // ask help !!!
            // 40 is the padding of the container
            w = jarvis.guess_width(this.plot_id) - 40;
            if (w == 0) {
                w = this.default_width;
            }
        }

        return w;
    },

    get_height: function() {
        var h = $('#' + this.plot_id).css('height');
        h = parseFloat(h.substring(0, h.length-2));
        console.log('* ' + this.plot_id + ' height: ' + h);

        if (h < 200) {
            var width = this.get_width();
            return width * 0.6;
        } else {
            return h;
        }

    },

};
// bind this to the global plots object
if (typeof(plots) == 'undefined') {

} else {
    plots[fig_heatmap_usstatecdt.plot_id] = fig_heatmap_usstatecdt;
}