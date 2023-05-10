var figmker_cdtgeomap_mayo6 = {
    colorbar_title: 'Days',
    data_file: 'uscounty-data-latest.json',
    data: null,
    valuescale: {
        TPT: [0, 1000],
        CDT: [0, 50],
    },
    colorscale: {
        TPT: [
            [0, 'rgba(255, 255, 255, 0.7)'],
            [1, 'rgba(240, 0, 0, 0.7']
        ],
        CDT: [
            [0, 'rgba(255, 0, 0, 0.5)'],
            [0.5, 'rgba(255, 255, 0, 0.5)'],
            [1, 'rgba(144, 238, 144, 0.5)']
        ],
    },
    fips_lists: {
        RST: [27037, 27043, 27131, 27169, 19189, 
              19195, 27139, 27109, 27045, 27047,
              27147, 27161, 27099, 27039, 27157,
              27049, 55011, 55093, 55091],
        JAX: [12031, 12109, 13191, 13127, 13037, 13065, 13049, 13069, 13003, 13025, 13005, 13229],
        PHX: ['04005', '04017', '04013', '04007', '04009', '04011', '04027', '04012'],
        SWWI: [27055, 55063, 55081, 55123, 55121],
        SWMN: [27012, 27103, 27015, 27063, 27091, 27079, 27161, 27165],
        NWWI: [55035, 55033, 55019, 55017, 55093, 55005]
    },
    area: {
        SWMN: [44.0391440919202, -94.38313071522299, 22.706392363939266],
        SWWI: [44.010476802332036, -91.08307387229706, 22.558226273473466],
        NWWI: [45.05396124702516, -91.49929146927299, 19.37713073804065],
        PHX:  [34.544938344671905, -111.95353291577072, 5.006340326068152],
        JAX:  [30.74383719861222, -82.03935200290773, 12.6725360575254],
        RST:  [44.114646568145986, -92.8008257375003, 14.451571672490006],
        default: [32.84906395662327, -100.32481276712122, 3.787872300973526]
    },

    init: function(data) {
        this.data = data;
    },

    make_fig: function(region, plot_id, data) {
        var fig = {
            plot_id: plot_id,
            get_view: this.get_view
        };
        var plot_dict = this.create_plot_data(region, data);
        fig.plot_dict = plot_dict;
        Plotly.newPlot(
            fig.plot_id, 
            fig.plot_dict.data,
            fig.plot_dict.layout,
            {responsive: true, 
                displayModeBar: false,
                scrollZoom: false,}
        );
        // update the last update
        $('#' + plot_id + '_last_update').html(data.date);
        return fig;
    },

    create_plot_data: function(region, data) {
        var date = data.date;
        var rows = data.data;

        var mydata = {
            regions: []
        };

        for (let i = 0; i < region.fips_list.length; i++) {
            const fips = region.fips_list[i];
            if (rows.hasOwnProperty(fips)) {
                var d = rows[fips];
                var cdt = d.cdts[d.cdts.length - 1];
                var ncc = d.nccs[d.nccs.length - 1];
                var dth = d.dths[d.dths.length - 1];
                var d_dth = dth - d.dths[d.dths.length - 2];
                var sdr = d.sdrs[d.sdrs.length - 1];
                var new_cc = d.news[d.news.length - 1];
                var cdr = dth / ncc;
                var r = {
                    FIPS: fips,
                    val: cdt,
                    txt: d.countyName + ', ' + d.state + ' on ' + date + '<br>' +
                        'CDT: <b>' + cdt.toFixed(1) + '</b> days<br>' +
                        'Total Cases:  <b>' + ncc.toFixed(0) + 
                            ' (' + new_cc.toFixed(0) + ')</b><br>' + 
                        'Total Deaths:  <b>' + dth.toFixed(0) + 
                            ' (' + d_dth.toFixed(0) + ')</b><br>' + 
                        'Death Rate:  <b>' + (cdr*100).toFixed(1) + '%</b><br>' + 
                        'Death Rate(4-day Smoothed): <b>' + (sdr*100).toFixed(1) + '%</b>'
                }
                mydata.regions.push(r);
            }
        }

        var plot_data = [];
        plot_data.push({
            name: 'County<br>Detail',
            type: 'choropleth',
            locations: this.unpack(mydata.regions, 'FIPS'),
            text: this.unpack(mydata.regions, 'txt'),
            z: this.unpack(mydata.regions, 'val'),

            zmin: this.valuescale.CDT[0],
            zmax: this.valuescale.CDT[1],

            hovertemplate: '%{text}',
            geojson: './static/data/us-countymap-5m.json',
            colorscale: this.colorscale.CDT,
            showlegend: false,
            colorbar: {
                title: this.colorbar_title,
                thickness: 15,
                len: .7,
                x: 0.02,
                y: 0.45,
                nticks: 6
            },
            marker: {
                line:{
                    color: '#6f6f6f',
                    width: 1
                }
            },
        });

        var plot_layout = {
            margin: { t: 0 , b: 0, l: 0, r: 0},
            geo: {
                scope: 'usa',
                countrycolor: 'rgb(255, 255, 255)',
                showland: true,
                landcolor: 'rgb(217, 217, 217)',
                lakecolor: 'rgb(255, 255, 255)',
                subunitcolor: 'rgb(255, 255, 255)',
                showlakes: false,
                showframe: false,
                showcoastlines: false,

                center: {
                    lat: region.view[0],
                    lon: region.view[1]
                },
                projection: {
                    scale: region.view[2]
                },
            }
        };

        return {
            data: plot_data, 
            layout: plot_layout
        };
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

    get_view: function() {
        return [
            this.plot_dict.layout.geo.center.lat,
            this.plot_dict.layout.geo.center.lon,
            this.plot_dict.layout.geo.projection.scale
        ];
    },

    unpack: function(rows, key) {
        return rows.map(function(row) {
            return row[key];
        });
    },
};