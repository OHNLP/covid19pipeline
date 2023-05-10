var fig_heatgeomap_uscntycdt = {
    plot_id: 'fig_heatgeomap_uscntycdt',
    plot_elm: null,
    plot_dict: null,
    plot_type: 'plotly',
    colorbar_title: 'Days',
    cdt_max: 50,
    colorscale: {
        CDT: [
            [0, 'rgba(255, 0, 0, 0.5)'],
            [0.5, 'rgba(255, 255, 0, 0.5)'],
            [1, 'rgba(144, 238, 144, 0.5)']
        ],
    },
    data: null,
    data_file: 'uscounty-data-latest.json',

    FIPS2State: {
        '01': { name: 'Alabama', code: 'AL' },
        '02': { name: 'Alaska', code: 'AK' },
        '04': { name: 'Arizona', code: 'AZ' },
        '05': { name: 'Arkansas', code: 'AR' },
        '06': { name: 'California', code: 'CA' },
        '08': { name: 'Colorado', code: 'CO' },
        '09': { name: 'Connecticut', code: 'CT' },
        '10': { name: 'Delaware', code: 'DE' },
        '11': { name: 'District Of Columbia', code: 'DC' },
        '12': { name: 'Florida', code: 'FL' },
        '13': { name: 'Georgia', code: 'GA' },
        '15': { name: 'Hawaii', code: 'HI' },
        '16': { name: 'Idaho', code: 'ID' },
        '17': { name: 'Illinois', code: 'IL' },
        '18': { name: 'Indiana', code: 'IN' },
        '19': { name: 'Iowa', code: 'IA' },
        '20': { name: 'Kansas', code: 'KS' },
        '21': { name: 'Kentucky', code: 'KY' },
        '22': { name: 'Louisiana', code: 'LA' },
        '23': { name: 'Maine', code: 'ME' },
        '24': { name: 'Maryland', code: 'MD' },
        '25': { name: 'Massachusetts', code: 'MA' },
        '26': { name: 'Michigan', code: 'MI' },
        '27': { name: 'Minnesota', code: 'MN' },
        '28': { name: 'Mississippi', code: 'MS' },
        '29': { name: 'Missouri', code: 'MO' },
        '30': { name: 'Montana', code: 'MT' },
        '31': { name: 'Nebraska', code: 'NE' },
        '32': { name: 'Nevada', code: 'NV' },
        '33': { name: 'New Hampshire', code: 'NH' },
        '34': { name: 'New Jersey', code: 'NJ' },
        '35': { name: 'New Mexico', code: 'NM' },
        '36': { name: 'New York', code: 'NY' },
        '37': { name: 'North Carolina', code: 'NC' },
        '38': { name: 'North Dakota', code: 'ND' },
        '39': { name: 'Ohio', code: 'OH' },
        '40': { name: 'Oklahoma', code: 'OK' },
        '41': { name: 'Oregon', code: 'OR' },
        '42': { name: 'Pennsylvania', code: 'PA' },
        '44': { name: 'Rhode Island', code: 'RI' },
        '45': { name: 'South Carolina', code: 'SC' },
        '46': { name: 'South Dakota', code: 'SD' },
        '47': { name: 'Tennessee', code: 'TN' },
        '48': { name: 'Texas', code: 'TX' },
        '49': { name: 'Utah', code: 'UT' },
        '50': { name: 'Vermont', code: 'VT' },
        '51': { name: 'Virginia', code: 'VA' },
        '53': { name: 'Washington', code: 'WA' },
        '54': { name: 'West Virginia', code: 'WV' },
        '55': { name: 'Wisconsin', code: 'WI' },
        '56': { name: 'Wyoming', code: 'WY' },
        '60': { name: 'American Samoa', code: 'AS' },
        '66': { name: 'Guam', code: 'GU' },
        '69': { name: 'Northern Mariana Islands', code: 'MP' },
        '72': { name: 'Puerto Rico', code: 'PR' },
        '78': { name: 'Virgin Islands', code: 'VI' },
    },

    area: {
        SWMN: [44.02907899472882, -94.3890149890982, 6.504512558724205],
        SWWI: [44.02850002190516, -91.14599583630508, 6.436584781196458],
        NWWI: [45.05152269286285, -91.42584363926721, 6.229056098694206],
        PHX:  [34.544938344671905, -111.95353291577072, 4.506340326068152],
        JAX:  [30.736528159343408, -81.94074851482583, 5.858222918792623],
        RST:  [44.18972577500327, -92.52786083477628, 6.134125167316714],
        default: [38.44642166295486, -96.99774150364671, 1.0530913529267336]
    },

    load: function() {
        $.when(
            $.get('./static/data/us-countymap-5m.json', {}),
            $.get('./covid_data/dsvm/' + this.data_file, {ver: Math.random()})
        ).done(function(data1, data2) {
            fig_heatgeomap_uscntycdt.set_all_counties(data1[0]);
            fig_heatgeomap_uscntycdt.init(data2[0]);
        });
    },

    set_all_counties: function(data) {
        this.data_geo = data;
        this.all_counties = d3.map();
        for (let i = 0; i < data.features.length; i++) {
            const f = data.features[i];
            // create a new county obj
            var county = {
                FIPS: f.id,
                countyName: f.properties.NAME,
                state: this.FIPS2State[f.properties.STATE].name,
                has_case: false,
                data: null
            };
            
            this.all_counties.set(f.id, county);
        }
    },

    convert_data_to_dict: function() {
        this.data_dict = d3.map();
        for (const FIPS in this.data.data) {
            if (this.data.data.hasOwnProperty(FIPS)) {
                const cnty = this.data.data[FIPS];
                this.data_dict.set(FIPS, cnty);
            }
        }
    },

    init: function(data) {
        this.data = data;
        this.create_plot_dict();
        this.convert_data_to_dict();

        Plotly.newPlot(
            this.plot_id, 
            this.plot_dict.data,
            this.plot_dict.layout,
            {responsive: true}
        );

        $('#' + this.plot_id + '_last_update').html(data.date);

        this.bind_click_event();
    },

    bind_click_event: function() {
        // bind click events
        this.plot_elm = document.getElementById(this.plot_id);
        this.plot_elm.on('plotly_click', function(data) {
            console.log(data);
            var FIPS = data.points[0].properties.STATE + data.points[0].properties.COUNTY;
            // hope jarvis has this ablity!
            console.log("* clicked on " + FIPS);
            jarvis.add_county_series(FIPS);
        });

        this.plot_elm.on('plotly_selected', function(data) {
            data.points.forEach(function(p) {
                var FIPS = p.properties.STATE + p.properties.COUNTY;
                jarvis.add_county_series(FIPS);
            });

        });
    },

    _update: function() {
        Plotly.update(this.plot_id, this.plot_dict);
    },

    _relayout: function(update) {
        Plotly.relayout(this.plot_id, update);
    },

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

    create_plot_dict: function(filter) {
        var date = this.data.date;
        var rows = this.data.data;
        var mydata = {
            regions: []
        };
        var mydata_0case = {
            regions: []
        };

        // get all the counties with cases
        for (const FIPS in this.data.data) {
            const r = this.data.data[FIPS];

            if (typeof(filter) != 'undefined') {
                var cdt = r.cdts[r.cdts.length-1];
                if (filter(cdt)) {
                    // keep those comply the filter condition
                } else {
                    continue;
                }
            }
            var ncc = r.nccs[r.nccs.length-1];
            if (ncc == 0) {
                continue;
            }
            r.val = r.cdts[r.cdts.length-1].toFixed(2);

            var cdt = r.cdts[r.cdts.length-1];
            var dth = r.dths[r.dths.length-1];
            var sdr = r.sdrs[r.sdrs.length-1] * 100;
            var cdr = dth / ncc * 100;

            // ok, when we build the txt
            r.txt = r.countyName + ', ' + r.state + ' on ' + date + '<br>' +
                'CDT: <b>' + r.val + '</b> days ' +
                    '(<span class="txt-'+this.get_color(r.d_cdt)+'">'+ this.get_sign(r.d_cdt) + 
                    r.d_cdt.toFixed(1) +'</span>)<br>' +
                'Total Cases:  <b>' + ncc.toFixed(0) + 
                    ' (' + this.get_sign(r.d_ncc) + r.d_ncc.toFixed(0) + ')</b><br>' + 
                'Total Deaths:  <b>' + dth.toFixed(0) + 
                    ' (' + this.get_sign(r.d_dth) + r.d_dth.toFixed(0) + ')</b><br>' +
                'Death Rate:  <b>' + cdr.toFixed(1) + '%</b><br>' +
                'Death Rate(4-day Smoothed):  <b>' + sdr.toFixed(1) + '%</b>';

            mydata.regions.push(r);

            // update the all counties
            var cnty = this.all_counties.get(r.FIPS);
            if (cnty == null) {
                // pass, we don't have data for this area
                console.log('* missing geo data for', r.FIPS, r.countyName + ', ' + r.state)
            } else {
                cnty['has_case'] = true;
                cnty['data'] = r;
            }
        }

        // get those counties without case
        var all_cnty = this.all_counties.values();
        for (let i = 0; i < all_cnty.length; i++) {
            const cnty = all_cnty[i];
            if (cnty.has_case) {
                continue;
            }
            var r = {
                FIPS: cnty.FIPS,
                val: this.cdt_max,
                txt: cnty.countyName + ', ' + cnty.State + ' on ' + date + '<br>' +
                    'No confirmed COVID-19 case'
            }
            if (typeof(filter) != 'undefined') {
                if (filter(r.val)) {
                    // keep those comply the filter condition
                } else {
                    continue;
                }
            }
            mydata_0case.regions.push(r);
        }
        
        var plot_data = [];

        // those counties with case
        plot_data.push({
            name: 'County<br>Data',
            type: 'choropleth',
            locations: this.unpack(mydata.regions, 'FIPS'),
            text: this.unpack(mydata.regions, 'txt'),
            z: this.unpack(mydata.regions, 'val'),
            hovertemplate: '%{text}',
            zmin: 0,
            zmid: this.cdt_max / 2,
            zmax: this.cdt_max,
            geojson: './static/data/us-countymap-5m.json',
            colorscale: this.colorscale.CDT,
            colorbar: {
                title: this.colorbar_title,
                thickness: 15,
                len: .3,
                x: 0.02,
                y: 0.23,
                nticks: 6
            }
        });

        // those counties with 0 case
        plot_data.push({
            name: '0 Case<br>County',
            type: 'choropleth',
            locations: this.unpack(mydata_0case.regions, 'FIPS'),
            text: this.unpack(mydata_0case.regions, 'txt'),
            z: this.unpack(mydata_0case.regions, 'val'),
            hovertemplate: '%{text}',
            zmin: 0,
            zmid: this.cdt_max / 2,
            zmax: this.cdt_max,
            geojson: './static/data/us-countymap-5m.json',
            colorscale: this.colorscale.CDT,
            showscale: false
        });
        
        this.plot_dict = {
            data: plot_data,
            layout: {
                margin: { t: 0 , b: 0, l: 0, r: 0},
                geo: {
                    scope: 'usa',
                    center: {
                        lat: this.area.default[0],
                        lon: this.area.default[1]
                    },
                    projection: {
                        scale: this.area.default[2]
                    }
                }
            }
        };
    },

    set_view_to(name) {
        var update = {
            geo: {
                center: {
                    lat: this.area[name][0],
                    lon: this.area[name][1]
                },
                projection: {
                    scale: this.area[name][2]
                }
            }
        }
        this._relayout(update);
    },

    set_view: function(view) {
        var update = {
            geo: {
                center: {
                    lat: view[0],
                    lon: view[1]
                },
                projection: {
                    scale: view[2]
                }
            }
        }
        this._relayout(update);
    },

    get_view: function() {
        return [
            this.plot_dict.layout.geo.center.lat,
            this.plot_dict.layout.geo.center.lon,
            this.plot_dict.layout.geo.projection.scale
        ];
    },

    filter_by_cdt: function(a, b) {
        if (b > 0) {
            var f = function(v) {
                if (v > a && v <= b) {
                    return true;
                } else {
                    return false;
                }
            };
            this.create_plot_dict(f);
        } else {
            this.create_plot_dict();
        }
        Plotly.purge(this.plot_id);
        Plotly.newPlot(this.plot_id, this.plot_dict);

        this.bind_click_event();
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
    plots[fig_heatgeomap_uscntycdt.plot_id] = fig_heatgeomap_uscntycdt;
}