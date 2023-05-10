var fig_ani_rtmap_usstate = {
    plot_id: 'fig_ani_rtmap_usstate',
    cal_id: 'fig_ani_rtmap_usstate_cal',
    plot_elm: null,
    plot_dict: null,
    plot_type: 'd3',
    geojson_file: 'us-10m.v2.json',
    data_file: 'usstate-data-history.json',

    // for d3.js
    num_max: 50,
    rt_max: 2,
    rt_min: 0,
    color_range: [
        'rgba(144, 238, 144, 0.6)',
        'rgba(255, 255, 0, 0.6)',
        'rgba(255, 0, 0, 0.6)'
    ],
    draw: {
        states: []
    },
    proc_play: null,
    date_idx: 0,
    frame_duration: 300,
    mdy_str2date: d3.timeParse('%m/%d/%y'),
    date2Ymd_str: d3.timeFormat('%Y-%m-%d'),
    fips2state: {
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

    load: function() {
        $.when(
            $.get("./static/data/" + this.geojson_file),
            $.get("./covid_data/" + this.data_file, {ver: Math.random() }),
        ).done(function(data0, data1) {
            fig_ani_rtmap_usstate.init(data0[0], data1[0]);
        })
    },

    init: function(usmap, data) {
        // bind data
        this.usmap = usmap;
        this.data = data;
        this.draw.states = topojson.feature(usmap, usmap.objects.states).features;

        // bind state data to map
        for (let i = 0; i < this.draw.states.length; i++) {
            var geo_state = this.draw.states[i];
            var fips = geo_state.id;
            var code = this.fips2state[fips].code;
            geo_state.code = code;
            geo_state.data = this.data.data[code];
            geo_state.date = this.data.date;
            geo_state.dates = this.data.dates;
            geo_state.name = geo_state.properties.name;
            geo_state.val = this.data.data[code].rt_ml[ this.data.data[code].rt_ml.length - 1];
        }

        // init the svg
        this.svg = d3.select("svg#" + this.plot_id);
        this.width = +this.svg.attr("width");
        this.height = +this.svg.attr("height");

        // for map display
        this.geo_path = d3.geoPath();

        // color scale
        this.color_scale = d3.scaleLinear()
            .domain([this.rt_min, this.rt_max/2, this.rt_max])
            .range(this.color_range);
        
        // the tip tool
        this.tip = d3.tip().attr('class', 'd3-tip').direction('e').offset([0,5])
            .html(function(d) {
                var dt = d.date;
                var dt_idx = d.dates.indexOf(dt);
                var dt_idx_ystdy = dt_idx==0? 0:dt_idx-1;

                var rt_ml = d.data.rt_ml[dt_idx];
                var cdt = d.data.cdts[dt_idx];
                var ncc = d.data.nccs[dt_idx];
                var dth = d.data.dths[dt_idx];

                var cdr = ncc == 0? 0:dth / ncc * 100;
                var sdr = d.data.sdrs[dt_idx] * 100;
                var fmt_comma = d3.format(',');
                
                var d_rt  = rt_ml - d.data.rt_ml[dt_idx_ystdy];
                var d_cdt = cdt - d.data.cdts[dt_idx_ystdy];
                var d_ncc = ncc - d.data.nccs[dt_idx_ystdy];
                var d_dth = dth - d.data.dths[dt_idx_ystdy];

                var content = "<span style='margin-left: 2.5px;'><b>" + d.name + "</b> on " + dt + "</span><br>";
                content +=`
                    <table style="margin-top: 2.5px;">
                        <tr><td>Case R<sub>t</sub>: </td><td style="text-align: right">${rt_ml.toFixed(2)} days (${d_rt.toFixed(2)})</td></tr>
                        <tr><td>Case Doubling Time: </td><td style="text-align: right">${cdt.toFixed(2)} days (${d_cdt.toFixed(2)})</td></tr>
                        <tr><td>Total Cases: </td><td style="text-align: right">${fmt_comma(ncc.toFixed(0))} (${fmt_comma(d_ncc)})</td></tr>
                        <tr><td>Total Deaths: </td><td style="text-align: right">${fmt_comma(dth.toFixed(0))} (${fmt_comma(d_dth)})</td></tr>
                        <tr><td>Death Rate: </td><td style="text-align: right">${cdr.toFixed(1)} %</td></tr>
                        <tr><td>Death Rate(4-day Smoothed): </td><td style="text-align: right">${sdr.toFixed(1)}%</td></tr>
                    </table>
                    `;
                return content;
            });
        this.svg.call(this.tip);

        // the zooming
        this.zoom = d3.zoom()
            .scaleExtent([1, 8])
            .on('zoom', function() {
                // zoom shapes
                fig_ani_rtmap_usstate.svg.selectAll('path')
                    .attr('transform', d3.event.transform);
                // zoom text
                fig_ani_rtmap_usstate.g_state_labels.selectAll('text')
                    .attr('transform', d3.event.transform);
            });
        
        this.svg.call(this.zoom);

        // draw the basic map
        this.g_states = this.svg.append("g")
            .attr("class", "states");
        this.g_states.selectAll("path")
            .data(this.draw.states)
            .enter().append("path")
            .attr("class", "state")
            .attr("fill", function(d) { 
                return fig_ani_rtmap_usstate.color_scale(d.val); 
            })
            .attr("d", this.geo_path)
            // .on('click', this.county_on_click)
            .on('mouseover', this.tip.show)
            .on('mouseout', this.tip.hide);
        // draw the state label
        this.g_state_labels = this.svg.append("g")
            .attr("class", "state-labels");
        this.g_state_labels.selectAll("text")
            .data(this.draw.states)
            .enter().append("text")
            .attr("class", "state-label")
            .attr("x", function(d) {
                return fig_ani_rtmap_usstate.geo_path.centroid(d)[0];
            })
            .attr("y", function(d) {
                return fig_ani_rtmap_usstate.geo_path.centroid(d)[1];
            })
            .attr("text-anchor", "middle")
            .attr('fill', 'black')
            .each(function(d) {
                d3.select(this).append('tspan')
                    .text(function(d) {
                        return d.code;
                    });
                d3.select(this).append('tspan')
                    .attr("class", "state-label-value")
                    .attr("x", function(d) {
                        return fig_ani_rtmap_usstate.geo_path.centroid(d)[0];
                    })
                    .attr('dy', function(d) {
                        return 10;
                    })
                    .text(function(d) {
                        return d.val.toFixed(1);
                    });
            })
            
                
        // draw the date
        this.g_info = this.svg.append("text")
            .attr('id', 'g-info')
            .attr("transform", "translate(0, 40)")
            .attr('x', 520)
            .attr('y', -5)
            .attr('fill', 'black')
            .attr("font-size", "16")
            .attr("font-weight", "bold")
            .text("");
        this.show_date_on_map(this.data.date);

        // init the calendar
        this.us_cal_data = this.data.dates.map(function(d, i) {
            var dt = fig_ani_rtmap_usstate.mdy_str2date(d);
            var rt_ml = fig_ani_rtmap_usstate.data.data['US'].rt_ml[i];
            return [
                fig_ani_rtmap_usstate.date2Ymd_str(dt),
                rt_ml
            ];
        });
        this.us_cal_data_label = [{
            value: JSON.parse(JSON.stringify(this.us_cal_data[this.us_cal_data.length - 1])),
            visualMap: false
        }];

        // create the option for echarts
        this.cal_option = {
            tooltip: {
                formatter: function(params) {
                    // console.log(params);
                    // if params
                    return params.value[0] + "<br>" +
                        'US R<sub>t</sub>: ' + params.value[1].toFixed(2) + '';
                }
            },
            visualMap: {
                min: 0,
                max: this.rt_max,
                right: 0,
                top: 0,
                itemHeight: 80,
                text: [this.rt_max + '', '0'],
                inRange: {
                    color: this.color_range
                }
            },
            calendar: {
                top: 20,
                left: 50,
                cellSize: 15,
                range: '2020',
                itemStyle: {
                    borderWidth: 1
                }
            },
            series: [
            {
                type: 'heatmap',
                coordinateSystem: 'calendar',
                data: this.us_cal_data
            }, 
            {
                type: 'scatter',
                coordinateSystem: 'calendar',
                data: this.us_cal_data_label,
                symbolSize: 9,
                itemStyle: {
                    color: 'black'
                }
            }]
        };
        this.cal_chart = echarts.init(document.getElementById(this.cal_id));
        this.cal_chart.setOption(this.cal_option);

        // bind click event
        this.cal_chart.on('click', function(params) {
            // console.log(params);
            var date_Ymd = params.data[0];
            var date_mdy = d3.timeFormat('%-m/%-d/%y')(d3.timeParse('%Y-%m-%d')(date_Ymd));
            fig_ani_rtmap_usstate.update_by_date(date_mdy);
        });
    },

    update_by_date: function(date) {
        var idx = this.data.dates.indexOf(date);
        this.date_idx = idx;
        // update the val
        for (let i = 0; i < this.draw.states.length; i++) {
            const geo_state = this.draw.states[i];
            geo_state.date = date;
            geo_state.val = geo_state.data.rt_ml[idx];
        }

        // update the date indicator
        this.us_cal_data_label = [{
            value: JSON.parse(JSON.stringify(this.us_cal_data[idx])),
            visualMap: false
        }];
        this.cal_option.series[1].data = this.us_cal_data_label;
        this.cal_chart.setOption(this.cal_option, true);

        // update the graph
        this.g_states.selectAll("path")
            .data(this.draw.states)
            .transition()
            .attr("fill", function(d) {
                return fig_ani_rtmap_usstate.color_scale(d.val); 
            });
        // update the text
        this.g_state_labels.selectAll("tspan.state-label-value")
            .data(this.draw.states)
            .transition()
            .text(function(d) {
                return d.val.toFixed(1);
            });
        
        // update the info
        this.show_date_on_map(date);
    },

    show_date_on_map: function(date) {
        $('#g-info').html(
            "U.S. Case Rt Map on " + 
            this.date2Ymd_str(this.mdy_str2date(date))
        );
    },

    stop: function() {
        if (this.proc_play == null) {
    
        } else {
            clearInterval(this.proc_play);
            this.proc_play = null;
        }
    },

    play: function() {
        if (this.proc_play == null) {
            this.proc_play = setInterval('fig_ani_rtmap_usstate.autoplay();', this.frame_duration);
        } else {
    
        } 
    },

    autoplay: function() {
        if (this.date_idx >= this.data.dates.length - 1) {
            this.date_idx = 0;
            this.stop();
        } else {
            this.date_idx += 1;
            var next_date = this.data.dates[this.date_idx];
            this.update_by_date(next_date);
        }
    }
};


// bind this to the global plots object
if (typeof(plots) == 'undefined') {

} else {
    plots[fig_ani_rtmap_usstate.plot_id] = fig_ani_rtmap_usstate;
}