var fig_crrw_usmap = {
    plot_id: 'fig_crrw_usmap',
    vpp: null,
    vpp_id: '#fig_crrw_usmap_vpp',

    data: null,
    data_file: 'US-latest.json',
    colorscale: {
        cdts: {
            name: 'Case Doubling Time',
            abbr: 'cdts',
            min: 0,
            mid: 50,
            max: 100,
            schema: [
                [0, 'rgba(255, 0, 0, 1)'],
                [0.5, 'rgba(255, 255, 0, 1)'],
                [1, 'rgba(144, 238, 144, 1)']
            ]
        },
        crcs: {
            name: 'CrRW Status',
            abbr: 'crcs',
            min: 0,
            mid: 1,
            max: 2,
            schema: [
                [0,   'green'],
                [0.5, 'gold'],
                [1,   'red']
            ]
        },
        tcps: {
            name: 'Total Cases / Population',
            abbr: 'tcps',
            min: 0,
            mid: 0.1,
            max: 0.2,
            schema: [
                [0,   'rgba(254, 240, 206, 1)'],
                [0.5, 'rgba(253, 164, 93, 1)'],
                [1,   'rgba(255, 30, 2, 1)']
            ]
        },
        pvis: {
            name: 'Pandemic Vulnerability Index',
            abbr: 'pvis',
            min: 0.3,
            mid: 0.5,
            max: 0.7,
            schema: [
                [0,   'rgba(253, 231, 228, 1)'],
                [0.5, 'rgba(240, 90, 158, 1)'],
                [1,   'rgba(71, 1, 103, 1)']
            ]
        },
        vaps: {
            name: 'Vaccination Administered %',
            abbr: 'vaps',
            min: 0,
            mid: 0.6,
            max: 1.2,
            schema: [
                [0,   'rgba(255, 255, 255, 1)'],
                [0.5, 'rgba(117, 218, 157, 1)'],
                [1,   'rgba(1, 117, 31, 1)']
            ]
        },
        fvps: {
            name: 'Fully Vaccinated Percentage',
            abbr: 'fvps',
            min: 0,
            mid: 0.4,
            max: 0.8,
            schema: [
                [0,   'rgba(255, 255, 255, 1)'],
                [0.5, 'rgba(141, 199, 252, 1)'],
                [1,   'rgba(0, 76, 145, 1)']
            ]
        }
    },
    fmt_comma: d3.format(","),

    current: {
        date: null,
        attr: 'crcs'
    },

    plot_config: {
        responsive: true,
        // displayModeBar: false,
        scrollZoom: false,
    },

    load: function() {
        $.get(
            './covid_data/v2/' + this.data_file,
            {ver: Math.random()},
            function(data) {
                fig_crrw_usmap.init(data);
            }, 'json'
        );
    },

    init: function() {
        // init the vpp part
        this.vpp = new Vue({
            el: this.vpp_id,
            data: {
                attr_colorscales: this.colorscale,
                current: this.current,
                date: null,
                dates: [],
                state: {
                    state: null,
                    data: {}
                }
            },
            methods: {
                get_attr_colorscale_legend: function(cs) {
                    var style = '';
                    if (cs.abbr == 'crcs') {
                        style = "background: linear-gradient( to right, ";
                        style += cs.schema[0][1] + ", ";
                        style += cs.schema[0][1] + " 33%, ";
                        style += cs.schema[1][1] + " 33%, ";
                        style += cs.schema[1][1] + " 66%, ";
                        style += cs.schema[2][1] + " 66%  ";
                        style += ")";

                    } else {
                        style = "background: linear-gradient(90deg";
                        for (var i = 0; i < cs.schema.length; i++) {
                            var schema_item = cs.schema[i];
                            style += ', ' + schema_item[1] + ' ' + (schema_item[0] * 100) + '%'
                        } 
                        style += ');'
                    }
                    return style;
                },

                get_attr_colorscale_value_legend: function(cs) {
                    if (['tcps', 'fvps', 'vaps'].indexOf(cs.abbr)>=0) {
                        return '('+ 
                            this.get_attr_colorscale_min_value_legend(cs) +
                            ' - ' + 
                            this.get_attr_colorscale_max_value_legend(cs) +
                        ')';

                    } else if (['crcs'].indexOf(cs.abbr)>=0) {
                        return '(Green, Yellow, Red)';

                    } else {
                        return '('+cs.min+' - '+cs.max+')';
                    }
                },

                get_attr_colorscale_min_value_legend: function(cs) {
                    if (['tcps', 'fvps', 'vaps'].indexOf(cs.abbr)>=0) {
                        return (cs.min*100).toFixed(1) +'%';
                    } else if (['crcs'].indexOf(cs.abbr)>=0) {
                        return 'Green';
                    } else {
                        return cs.min;
                    }
                },

                get_attr_colorscale_max_value_legend: function(cs) {
                    if (['tcps', 'fvps', 'vaps'].indexOf(cs.abbr)>=0) {
                        return (cs.max*100).toFixed(1) +'%';
                    } else if (['crcs'].indexOf(cs.abbr)>=0) {
                        return 'Red';
                    } else {
                        return cs.max;
                    }
                },

                update_color: function(attr) {
                    this.current.attr = attr;
                    fig_crrw_usmap.update(fig_crrw_usmap.data);
                },

                get_detail: function() {
                    var date_idx = this.dates.indexOf(this.date);
                    return {
                        state: this.state.data.state,
                        name: this.state.data.name,
                        state: this.state.data,
                        pop: this.state.data.pop,
                        cdt: this.state.data.cdts[date_idx],
                        crp: this.state.data.crps[date_idx],
                        crt: this.state.data.crts[date_idx],
                        ncc: this.state.data.nccs[date_idx],
                        dnc: this.state.data.dncs[date_idx],

                        tpr: this.state.data.tprs[date_idx],
                        ttr: this.state.data.ttrs[date_idx],
                        tpt: this.state.data.tpts[date_idx],
                        t7r: this.state.data.t7rs[date_idx],
                        
                        dth: this.state.data.dths[date_idx],
                        dtr: this.state.data.dtrs[date_idx],
                        crc: this.state.data.crcs[date_idx],
                        pvi: this.state.data.pvis[date_idx],
                        tcp: this.state.data.nccs[date_idx] / this.state.data.pop,
                        fvc: this.state.data.fvcs[date_idx],
                        fvp: this.state.data.fvps[date_idx],
                        vac: this.state.data.vacs[date_idx],
                        vap: this.state.data.vaps[date_idx],
                    }
                },

                fmt_comma: function(v) {
                    return jarvis.fmt_comma(v);
                },

                fmt_ind_val: function(ind, val) {
                    return jarvis.ind2txt(ind).fmt(val);
                },

                fmt_val: function(ind, val) {
                    return jarvis.val2txt(ind, val);
                }
            }
        });
    },

    _create_plot_layout: function() {
        this.plot_layout = {
            margin: { t: 0 , b: 0, l: 0, r: 0},
            geo: {
                scope: 'usa',
                showlakes: true,
                lakecolor: 'rgb(255,255,255)'
            },

            width: this.get_width(),
            height: this.get_height()
        };
        // if (jarvis.is_mobile()) {
        //     this.plot_layout['dragmode'] = false;
        // }
    },

    update: function(data) {
        this.data = data;
        this.current.date = data.date;

        // update the vpp
        this.vpp.date = data.date;
        this.vpp.dates = data.dates;

        this._create_plot_data();
        this._create_plot_layout();

        Plotly.purge(this.plot_id);
        Plotly.newPlot(
            this.plot_id, 
            this.plot_data,
            this.plot_layout,
            this.plot_config
        );

        // re-bind click event
        this._bind_click_event();

        // re-bind hover event
        this._bind_hover_event();

        // update the last update
        $('#' + this.plot_id + '_last_update').html(data.date);
    },

    update_by_date: function(date) {
        this.current.date = date;

        // update hte vpp
        this.vpp.date = date;
        
        // create the data on this date
        var mydata = this._create_mydata();
        var update_plot_data = [{
            locations: this.unpack(mydata, 'state'),
            text: this.unpack(mydata, 'txt'),
            z: this.unpack(mydata, 'val'),
        }];
        
        // update the figure
        Plotly.animate(
            this.plot_id,
            {
                data: update_plot_data,
                traces: [0],
                layout: {},
            },
            {
                transition: {
                    duration: 100,
                    easing: "cubic-in-out",
                },
                frame: {
                    duration: 100,
                },
            }
        );

        // update hte last update time
        $('#' + this.plot_id + '_last_update').html(this.current.date);
    },

    _bind_click_event: function() {
        // bind click events
        this.plot_elm = document.getElementById(this.plot_id);
        this.plot_elm.on('plotly_click', function(data) {
            var state = data.points[0].location;
            jarvis.show_state(state);
            fig_crrw_usmap.show_detail(state)
        });
    },

    _bind_hover_event: function() {
        // bind hover events
        this.plot_elm = document.getElementById(this.plot_id);
        this.plot_elm.on('plotly_hover', function(data) {
            var state = data.points[0].location;
            // jarvis.show_state(state);
        });
    },


    show_detail: function(state) {
        // console.log('* show detail: ' + county_fips);
        this.vpp.state.state = state;
        this.vpp.state.data = this.data.state_data[state];
        // this.vpp.$forceUpdate();
    },

    _create_mydata: function() {
        var date = this.current.date;
        var date_idx = this.data.dates.indexOf(date);
        var rows = this.data.state_data;
        var mydata = [];

        for (var state in rows) {
            if (rows.hasOwnProperty(state)) {
                var obj = rows[state];
                var cdt = obj.cdts[date_idx];
                var ncc = obj.nccs[date_idx];
                var dnc = obj.dncs[date_idx];
                var crp = obj.crps[date_idx];
                var crt = obj.crts[date_idx];
                var dth = obj.dths[date_idx];
                var dtr = obj.dtrs[date_idx];
                var pvi = obj.pvis[date_idx];
                var crc = obj.crcs[date_idx];
                var crc_v = {R:2, Y:1, G:0}[crc];
                var tcp = ncc / obj.pop;

                // decide show which value as default
                var val = null;
                var val_for_plotly = null;
                if (this.current.attr == 'crcs') {
                    val_for_plotly = crc_v;
                    val = crc_v;
                } else if (this.current.attr == 'tcps') {
                    val_for_plotly = tcp;
                    val = tcp;
                } else {
                    val_for_plotly = obj[this.current.attr][date_idx];
                    val = obj[this.current.attr][date_idx];
                }

                // decide the text
                var txt = date + ', ' + 
                    obj.name + '<br>' +
                    jarvis.ind2txt(this.current.attr).name + ': ' + 
                    jarvis.ind2txt(this.current.attr).fmt(val);

                // var txt = obj.name + '<br>' +
                // ' (Population: ' + this.fmt_comma(obj.pop) + ') <br>'+
                // 'For ' + date + ' <br>' +
                // 'Cr7d100k: <b>' + crp.toFixed(1) + ' cases per 100k </b><br>' +
                // 'RW_Cr7d100k: <b>' + crt.toFixed(2) + ' </b><br>' +
                // 'CDT: <b>' + cdt.toFixed(1) + ' days </b><br>' +
                // 'New Cases: <b>' + this.fmt_comma(dnc) + '</b><br>' +
                // 'Total Cases: <b>' + this.fmt_comma(ncc) + ' </b><br>' + 
                // 'Total Cases/Population: <b>' + (tcp*100).toFixed(4) + '% </b><br>' + 
                // 'Total Death: <b>' + this.fmt_comma(dth) + ' </b><br>' + 
                // 'Death Rate: <b>' + (dtr*100).toFixed(2) + '%</b><br>' +
                // '';

                var r = {
                    state: state,
                    val: val_for_plotly,
                    txt: txt
                };
                mydata.push(r);
            }
        }

        return mydata;
    },
    
    _create_plot_data: function() {
        
        var mydata = this._create_mydata();
        this.plot_data = [];
        this.plot_data.push({
            name: '',
            type: 'choropleth',
            locationmode: 'USA-states',

            locations: this.unpack(mydata, 'state'),
            text: this.unpack(mydata, 'txt'),
            z: this.unpack(mydata, 'val'),

            showlegend: false,
            showscale: false,

            hovertemplate: '%{text}',
            zmin: this.colorscale[this.current.attr].min,
            zmax: this.colorscale[this.current.attr].max,

            colorscale: this.colorscale[this.current.attr].schema,

            hoverlabel: {
                font: {
                    size: 12
                },
                align: 'left'
            }
        });
    },

    unpack: function(rows, key) {
        return rows.map(function(row) {
            return row[key];
        });
    },


    get_width: function() {
        // var w = $('#' + this.plot_id).css('width');
        // w = parseFloat(w.substring(0, w.length-2));
        var w = $('#' + this.plot_id).width();
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
        // var h = $('#' + this.plot_id).css('height');
        // h = parseFloat(h.substring(0, h.length-2));
        var h = $('#' + this.plot_id).height();
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
    plots[fig_crrw_usmap.plot_id] = fig_crrw_usmap;
}