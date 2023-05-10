var figmker_crrw_cntymap = {

    data: null,
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
            mid: 0.4,
            max: 0.8,
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
            mid: 0.25,
            max: 0.5,
            schema: [
                [0,   'rgba(255, 255, 255, 1)'],
                [0.5, 'rgba(141, 199, 252, 1)'],
                [1,   'rgba(0, 76, 145, 1)']
            ]
        }
    },

    regions: {
        RST: {
            fips_list: [27037, 27043, 27131, 27169, 19189, 
                        19195, 27139, 27109, 27045, 27047,
                        27147, 27161, 27099, 27039, 27157,
                        27049, 55011, 55093, 55091],
            view: [44.114646568145986, -92.8008257375003, 14.451571672490006]
        },

        JAX: {
            fips_list: [12031, 12109, 13191, 13127, 13037, 
                        13065, 13049, 13069, 13003, 13025, 
                        13005, 13229],
            view: [30.74383719861222, -82.03935200290773, 12.6725360575254]
        },

        PHX: {
            fips_list: ['04005', '04017', '04013', '04007', '04009', 
                        '04011', '04027', '04012'],
            view: [34.544938344671905, -111.95353291577072, 5.006340326068152]
        },

        SWWI: {
            fips_list: [27055, 55063, 55081, 55123, 55121],
            view: [44.010476802332036, -91.08307387229706, 22.558226273473466]
        },

        SWMN: {
            fips_list: [27012, 27103, 27015, 27063, 27091, 
                        27079, 27161, 27165],
            view: [44.0391440919202, -94.38313071522299, 22.706392363939266]
        },

        NWWI: {
            fips_list: [55035, 55033, 55019, 55017, 55093, 55005],
            view: [45.05396124702516, -91.49929146927299, 19.37713073804065]
        },
    },

    make_fig: function(region, plot_id, data) {
        return {
            plot_id: plot_id,
            get_view: this.get_view,

            current: {
                attr: 'crcs',
                date: data.date,
                region: region
            },

            data: data,

            _create_mydata: function() {
                var date = this.current.date;
                var date_idx = this.data.dates.indexOf(date);
                var rows = this.data.county_data;
    
                var mydata = [];
    
                for (let i = 0; i < this.current.region.fips_list.length; i++) {
                    const fips = this.current.region.fips_list[i];
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
    
                        // get the text
                        var txt = date + ', ' + obj.name + '<br>' + 
                            jarvis.ind2txt(this.current.attr).name + ': ' + 
                            jarvis.ind2txt(this.current.attr).fmt(val);
    
                        var r = {
                            fips: fips,
                            val: val,
                            txt: txt
                        }
                        mydata.push(r);
                    }
                }

                return mydata;
            },

            create_plot_data: function() {
                var mydata = this._create_mydata();
    
                var plot_data = [];
                plot_data.push({
                    name: '',
                    type: 'choropleth',
    
                    locations: this.unpack(mydata, 'fips'),
                    text: this.unpack(mydata, 'txt'),
                    z: this.unpack(mydata, 'val'),
    
                    hovertemplate: '%{text}',
                    geojson: './static/data/us-countymap-5m.json',
    
                    zmin: figmker_crrw_cntymap.colorscale[this.current.attr].min,
                    zmax: figmker_crrw_cntymap.colorscale[this.current.attr].max,
    
                    colorscale: figmker_crrw_cntymap.colorscale[this.current.attr].schema,
    
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
                        line:{
                            color: '#333333',
                            width: 1
                        }
                    },
                });
    
                return plot_data;
            },

            create_plot_layout: function() {

                var plot_layout = {
                    margin: { t: 0 , b: 0, l: 0, r: 0},
                    geo: {
                        scope: 'usa',

                        countrycolor: 'rgb(255, 255, 255)',
                        landcolor: 'rgb(255, 255, 255)',
                        lakecolor: 'rgb(255, 255, 255)',
                        subunitcolor: 'rgb(222, 222, 222)',

                        // showland: true,
                        showlakes: false,
                        showframe: false,
                        showcoastlines: false,
    
                        center: {
                            lat: this.current.region.view[0],
                            lon: this.current.region.view[1]
                        },
                        projection: {
                            scale: this.current.region.view[2]
                        },
                    }
                };
    
                return plot_layout;
            },
            
            update: function(data) {
                this.data = data;
                this.draw();
            },

            draw: function() {
                this.plot_data = this.create_plot_data();
                this.plot_layout = this.create_plot_layout();
                this.plot_config = {
                    responsive: true, 
                    displayModeBar: false,
                    scrollZoom: false
                };
    
                Plotly.purge(this.plot_id);
                Plotly.newPlot(
                    this.plot_id, 
                    this.plot_data,
                    this.plot_layout,
                    this.plot_config
                );
            },

            update_by_date: function(date) {
                this.current.date = date;
                        
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
                    this.plot_layout.geo.center.lat,
                    this.plot_layout.geo.center.lon,
                    this.plot_layout.geo.projection.scale
                ];
            },

            unpack: function(rows, key) {
                return rows.map(function(row) {
                    return row[key];
                });
            },
        };

        // // update the last update
        // $('#' + plot_id + '_last_update').html(data.date);
        // return fig;
    },

};