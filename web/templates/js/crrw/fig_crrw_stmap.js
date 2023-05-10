var fig_crrw_stmap = {
    plot_id: 'fig_crrw_stmap',
    data_file: 'US-latest.json',
    vpp: null,
    vpp_id: '#fig_crrw_stmap_vpp',

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
    geojson_url_base: "./static/data/map/",

    get_geojson_url: function(state) {
        if (state == 'US') {
            // return this.geojson_url_base + "us-states.json?ver=" + Math.random();
            return this.geojson_url_base + "us-states.json";
        } else {
            // return this.geojson_url_base + "us-"+state+".json?ver=" + Math.random();
            return this.geojson_url_base + "us-"+state+".json";
        }
    },

    center_zoom: {
        AL: [32.83094098386724, -86.72798630623657, 5.555648752272612, 6.505648752272609],
        AK: [63.44693850362876, -152.35437607298434, 2.7821258120506602, 3.582125812050661],
        AZ: [34.22032129272864, -111.79519254393165, 5.151412188068152, 6.151412188068149],
        AR: [34.74154293076825, -92.27158518339274, 5.3909149325614415, 6.890914932561438],
        CA: [37.45075663829661, -119.15385736551389, 4.203726247727388, 5.503726247727385],
        CO: [39.031159219718006, -105.50860962020852, 4.851412188068152, 6.551412188068148],
        CT: [41.55715657621522, -72.7299787240895, 6.636700474857865, 8.299999999999999],
        DE: [39.15099498387974, -75.36087912973886, 7.063404857504172, 7.96340485750417],
        DC: [38.896758078722826, -77.02494504184142, 9.863382259558914, 10.699999999999996],
        FL: [27.887125200731163, -83.79563908145951, 4.788425024767943, 6.08842502476794],
        GA: [32.80136845685382, -83.17089284876477, 5.194073777040557, 6.494073777040554],
        HI: [20.60743963352357, -157.54104533361146, 5.280893574706169, 6.6808935747061655],
        ID: [45.61980167243152, -114.16598280970521, 4.736549065241494, 5.636549065241491],
        IL: [39.81074645701159, -88.99580463570834, 5.24346021698839, 6.1434602169883865],
        IN: [39.799696826456255, -86.22002516386937, 5.397696781192849, 6.5976967811928455],
        IA: [42.10491391119382, -93.41377777792462, 5.211168201429747, 6.8111682014297426],
        KS: [38.440684985214176, -98.28074220678246, 4.808343825293441, 6.408343825293437],
        KY: [37.564568416051415, -85.6694500400194, 5.259756013361598, 6.559756013361594],
        LA: [30.99086613113124, -91.43518683060825, 5.380138585345384, 6.6801385853453805],
        ME: [45.289657532234486, -68.9674969445648, 5.229988796751516, 6.329988796751513],
        MD: [38.81535418520116, -77.12180346403989, 6.003973887409244, 7.203973887409241],
        MA: [42.08303690793116, -71.71280982798328, 6.0390902791042025, 7.439090279104199],
        MI: [44.5801516216078, -86.36481608559717, 4.799287957423174, 5.899287957423171],
        MN: [46.38085826405498, -93.6717735092464, 4.8000000000000005, 5.799999999999998],
        MS: [32.67036218623886, -89.64788757469944, 5.536594679723923, 6.43659467972392],
        MO: [38.38745607075799, -92.45400615072117, 5.202740687503251, 6.302740687503248],
        MT: [46.69748337383348, -109.89449604217452, 4.194267559094335, 5.694267559094331],
        NE: [41.35954643228564, -99.749047264115, 4.882358115519469, 6.182358115519465],
        NV: [38.61884501147105, -116.78201005530627, 4.896457889700124, 5.696457889700121],
        NH: [44.01014312907287, -71.52454991154269, 6.222515228018716, 7.0225152280187135],
        NJ: [40.14494695293476, -74.56351899912465, 6.266427775437659, 7.366427775437656],
        NM: [34.200386344213044, -106.07109251748108, 5.10199102508721, 6.101991025087207],
        NY: [42.93475020043314, -75.85682602572393, 4.851412188068152, 6.151412188068149],
        NC: [35.212586257912264, -79.89760235349581, 4.878911947457379, 6.178911947457375],
        ND: [47.45124418753352, -100.37322141588692, 4.833557666103269, 6.333557666103265],
        OH: [40.244096346922646, -82.58889854466332, 5.37060940340765, 6.657060940340762],
        OK: [35.36240917258573, -98.67768864171694, 4.4393485316272955, 6.239348531627291],
        OR: [44.14153619035105, -120.49700768838579, 4.640168187669632, 6.240168187669628],
        PA: [40.93561623669444, -77.63858939515887, 5.003288622967021, 6.9032886229670165],
        RI: [41.644399559477705, -71.49968794595952, 8.093127369668101, 8.993127369668098],
        SC: [33.57961112709421, -80.89443809845852, 5.878145529643364, 6.97814552964336],
        SD: [44.21476029518314, -100.23875902228633, 5.184352210170486, 6.384352210170482],
        TN: [35.83840909453255, -85.97782123718252, 5.064853245762301, 6.464853245762296],
        TX: [31.38153766444762, -100.08651780956296, 4.440010149181202, 5.340010149181198],
        UT: [39.57383395300832, -111.44344606283937, 5.402824376136306, 6.202824376136303],
        VT: [43.88191442670171, -72.52570703386135, 6.430489799445501, 7.330489799445497],
        VA: [37.48779928349346, -79.42283700816557, 5.092093635377879, 6.492093635377874],
        WA: [47.39956277899745, -120.79115434451177, 5.500000000000008, 6.300000000000005],
        WV: [38.9752685512272, -80.17909479124876, 5.880624334739462, 6.780624334739459],
        WI: [44.75598451280965, -89.84999463098484, 5.402824376136305, 6.302824376136302],
        WY: [43.00465749846177, -107.54231152504644, 5.001412188068152, 6.251412188068149],

        // for the USA map
        US: [41.341570863844055, -112.28385033630519, 1.33, 3.0333333333333408],

        // for the territories
        "AS": [-14.287319715841264, -170.6875293445853, 8.900000000000004, 9.900000000000004],
        "GU": [13.4352408224931, 144.79330364803013, 8.999999999999982, 9.999999999999982],
        "MP": [15.101249677795451, 145.7078289288088, 8.799999999999983, 9.799999999999983],
        "PR": [18.19379353240403, -66.41591225952243, 6.69999999999989, 7.89999999999999],
        "VI": [18.03447726727822, -64.79825504504345, 8.099999999999985, 9.099999999999985]
    },

    current: {
        date: null,
        state: null,
        attr: 'crcs'
    },

    plot_config: {
        responsive: true,
        // displayModeBar: false,
        scrollZoom: true,
    },

    init: function() {
        this.vpp = new Vue({
            el: this.vpp_id,
            data: {
                attr_colorscales: this.colorscale,
                current: this.current,
                date: null,
                dates: [],
                county: {
                    fips: null,
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
                    fig_crrw_stmap.update(fig_crrw_stmap.data);
                },

                get_detail: function() {
                    var date_idx = this.dates.indexOf(this.date);
                    return {
                        FIPS: this.county.data.FIPS,
                        name: this.county.data.name,
                        state: this.county.data,
                        pop: this.county.data.pop,
                        cdt: this.county.data.cdts[date_idx],
                        crp: this.county.data.crps[date_idx],
                        crt: this.county.data.crts[date_idx],
                        ncc: this.county.data.nccs[date_idx],
                        dnc: this.county.data.dncs[date_idx],
                        dth: this.county.data.dths[date_idx],
                        dtr: this.county.data.dtrs[date_idx],
                        crc: this.county.data.crcs[date_idx],
                        pvi: this.county.data.pvis[date_idx],
                        tcp: this.county.data.nccs[date_idx] / this.county.data.pop,
                        fvc: this.county.data.fvcs[date_idx],
                        fvp: this.county.data.fvps[date_idx],
                        vac: this.county.data.vacs[date_idx],
                        vap: this.county.data.vaps[date_idx],
                    }
                },

                get_detail_by_date: function(date) {
                    this.date = date;
                    return this.get_detail();
                },

                fmt_comma: function(v) {
                    return fig_crrw_stmap.fmt_comma(v);
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

    update: function(data) {
        this.data = data;
        this.current.state = data.state;
        this.current.date = data.date;
    
        // update the vpp
        this.vpp.date = data.date;
        this.vpp.dates = data.dates;

        // create the data on this date
        this._create_plot_data();

        // update the layout
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
        $('#' + this.plot_id + '_state_name').html(data.state);
    },

    update_by_date: function(date) {
        this.current.date = date;

        // update hte vpp
        this.vpp.date = date;
        
        // create the layout
        // this._create_plot_layout();
        
        // create the data on this date
        var mydata = this._create_mydata();
        this.mydata = mydata;

        var update_plot_data = [{
            locations: this.unpack(mydata, 'fips'),
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
            var county_fips = data.points[0].location;
            fig_crrw_stmap.show_detail(county_fips)
            jarvis.show_county(county_fips);
        });
    },

    _bind_hover_event: function() {
        // bind hover events
        this.plot_elm = document.getElementById(this.plot_id);
        this.plot_elm.on('plotly_hover', function(data) {
            var county_fips = data.points[0].location;
            // jarvis.show_county(state);
            // fig_crrw_stmap.show_detail(county_fips)
        });
    },

    show_detail: function(county_fips) {
        // console.log('* show detail: ' + county_fips);
        this.vpp.county.fips = county_fips;
        this.vpp.county.data = this.data.county_data[county_fips];
        // this.vpp.$forceUpdate();
    },

    _create_mydata: function() {
        var date = this.current.date;
        var date_idx = this.data.dates.indexOf(date);
        var rows = this.data.county_data;
        var mydata = [];

        for (var fips in rows) {
            if (rows.hasOwnProperty(fips)) {
                var obj = rows[fips];
                var cdt = obj.cdts[date_idx];
                var crp = obj.crps[date_idx];
                var crt = obj.crts[date_idx];
                var ncc = obj.nccs[date_idx];
                var dnc = obj.dncs[date_idx];
                var dth = obj.dths[date_idx];
                var dtr = obj.dtrs[date_idx];
                var pvi = obj.pvis[date_idx];
                var crc = obj.crcs[date_idx];
                var crc_v = {R:2, Y:1, G:0}[crc];
                var tcp = ncc / obj.pop;

                // decide show which value as default
                var val = null;
                if (this.current.attr == 'crcs') {
                    val = crc_v;
                } else if (this.current.attr == 'tcps') {
                    val = tcp;
                } else {
                    val = obj[this.current.attr][date_idx];
                }

                // decide the text
                var txt = date + ', ' + 
                    obj.name + '<br>' +
                    jarvis.ind2txt(this.current.attr).name + ': ' + 
                    jarvis.ind2txt(this.current.attr).fmt(val);

                var r = {
                    fips: fips,
                    val: val,
                    txt: txt
                };
                mydata.push(r);
            }
        }

        return mydata;
    },
    
    _create_plot_data: function() {
        // create the data list
        var mydata = this._create_mydata();

        // generate the plot_data for plotly
        this.plot_data = [];

        this.plot_data.push({
            name: '',
            type: 'choropleth',
            locationmode: 'USA-states',
            locations: this.unpack(mydata, 'fips'),

            locationmode: "geojson-id",
            geojson: this.get_geojson_url(this.current.state),

            text: this.unpack(mydata, 'txt'),
            z: this.unpack(mydata, 'val'),

            hovertemplate: '%{text}',

            zmin: this.colorscale[this.current.attr].min,
            zmax: this.colorscale[this.current.attr].max,

            colorscale: this.colorscale[this.current.attr].schema,

            hoverlabel: {
                bgcolor: '#000000',
                font: {
                    size: 12,
                    color: '#ffffff'
                },
                align: 'left'
            },

            showlegend: false,
            showscale: false,

            marker: {
                line: {
                    color: "#333333",
                    width: 1,
                },
            },
        });

    },

    _create_plot_layout: function() {
        var state_loc = this.center_zoom[this.current.state];
        var lat = state_loc[0];
        var lon = state_loc[1];
        var zoom = state_loc[3];

        this.plot_layout = {
            margin: { t: 0 , b: 0, l: 0, r: 0},
            geo: {
                scope: 'world',
                projection: {
                    type: 'mercator'
                },
                center: {
                    lat: lat,
                    lon: lon,
                },
                fitbounds: 'locations',
                zoom: zoom,
                showframe: false,
                showlakes: false
            },

            width: this.get_width(),
            height: this.get_height()
        };

        // if (jarvis.is_mobile()) {
        //     this.plot_layout['dragmode'] = false;
        // }
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
    plots[fig_crrw_stmap.plot_id] = fig_crrw_stmap;
}