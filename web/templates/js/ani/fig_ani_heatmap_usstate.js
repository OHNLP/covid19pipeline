var fig_ani_heatmap_usstate = {
    plot_id: 'fig_ani_heatmap_usstate',
    cal_id: 'fig_ani_heatmap_usstate_cal',
    plot_elm: null,
    plot_dict: null,
    plot_type: 'd3',
    geojson_file: 'us-states.json',
    geojson_file_county: 'us-10m.v2.json',
    data_file: 'US-history.json',
    data_file_sm: 'US-latest.json',

    // for d3.js
    num_max: 100,
    color_range: [
        'rgba(255, 0, 0, 0.6)',
        'rgba(255, 255, 0, 0.6)',
        'rgba(144, 238, 144, 0.6)'
    ],
    draw: {
        attr: 'cdts',
        states: []
    },
    proc_play: null,
    date_idx: 0,
    frame_duration: 300,
    mdy_str2date: d3.timeParse('%m/%d/%y'),
    date2Ymd_str: d3.timeFormat('%Y-%m-%d'),

    load: function() {
        $.when(
            $.get("./static/data/map/" + this.geojson_file),
            $.get("./covid_data/v2/" + this.data_file, {ver: Math.random() }),
        ).done(function(data0, data1) {
            fig_ani_heatmap_usstate.init(data0[0], data1[0]);
        })
    },

    init: function(usmap, data, attr) {
        // bind data
        this.data = data;
        this.draw.states = usmap.features;
        this.draw.attr = attr;
        // this.draw.states = topojson.feature(usmap, usmap.objects.states).features;

        // bind state data to map
        for (let i = 0; i < this.draw.states.length; i++) {
            var geo_state = this.draw.states[i];
            var state = geo_state.id;

            geo_state.state = state;
            geo_state.name = geo_state.properties.STATE_NAME;
            geo_state.date = this.data.date;
            geo_state.dates = this.data.dates;
            // bind all data of this states
            geo_state.data = this.data.state_data[state];
            // set the latest item as default
            geo_state.val = geo_state.data[this.draw.attr][ 
                geo_state.data[this.draw.attr].length - 1];
        }

        // init the svg
        this.svg = d3.select("svg#" + this.plot_id);
        this.width = +this.svg.attr("width");
        this.height = +this.svg.attr("height");

        // for map display
        this.geo_projection = d3.geoAlbersUsa();
        // this.geo_projection = d3.geoAlbersUsaTerritories();
        this.geo_path = d3.geoPath(this.geo_projection);

        // color scale
        this.color_scale = d3.scaleLinear()
            .domain([0, this.num_max/2, this.num_max])
            .range(this.color_range);
        this.color_scale2 = d3.scaleSequential(d3.interpolatePuRd)
            .domain([0, this.num_max]);
        
        // the tip tool
        this.tip = d3.tip().attr('class', 'd3-tip').direction('e').offset([0,5])
            .html(function(d) {
                var dt = d.date;
                var dt_idx = d.dates.indexOf(dt);
                var dt_idx_ystdy = dt_idx==0? 0:dt_idx-1;

                var cdt = d.val;
                var ncc = d.data.nccs[dt_idx];
                var dth = d.data.dths[dt_idx];

                var cdr = ncc == 0? 0:dth / ncc * 100;
                var sdr = d.data.sdrs[dt_idx] * 100;
                var fmt_comma = d3.format(',');

                var d_cdt = cdt - d.data.cdts[dt_idx_ystdy];
                var d_ncc = ncc - d.data.nccs[dt_idx_ystdy];
                var d_dth = dth - d.data.dths[dt_idx_ystdy];

                var content = "<span style='margin-left: 2.5px;'><b>" + d.name + "</b> on " + dt + "</span><br>";
                content +=`
                    <table style="margin-top: 2.5px;">
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
                fig_ani_heatmap_usstate.svg.selectAll('path')
                    .attr('transform', d3.event.transform);
                // zoom text
                fig_ani_heatmap_usstate.g_state_labels.selectAll('text')
                    .attr('transform', d3.event.transform);
            });
        
        this.svg.call(this.zoom);

        // draw the basic map
        this.g_states = this.svg.append("g")
            .attr("class", "states");
        
        // draw each state
        this.g_states.selectAll("path")
            .data(this.draw.states)
            .enter().append("path")
            .attr("class", "state")
            .attr("fill", function(d) { 
                return fig_ani_heatmap_usstate.color_scale(d.val); 
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
                return fig_ani_heatmap_usstate.geo_path.centroid(d)[0];
            })
            .attr("y", function(d) {
                return fig_ani_heatmap_usstate.geo_path.centroid(d)[1];
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
                        return fig_ani_heatmap_usstate.geo_path.centroid(d)[0];
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
            var dt = fig_ani_heatmap_usstate.mdy_str2date(d);
            var val = fig_ani_heatmap_usstate.data.usa_data[fig_ani_heatmap_usstate.draw.attr][i];
            return [
                fig_ani_heatmap_usstate.date2Ymd_str(dt),
                val
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
                        'US: ' + params.value[1] + '';
                }
            },
            visualMap: {
                min: 0,
                max: this.num_max,
                right: 0,
                top: 0,
                itemHeight: 80,
                text: [this.num_max + ' days', '0'],
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
            fig_ani_heatmap_usstate.update_by_date(date_mdy);
        });
    },

    update_by_date: function(date) {
        var idx = this.data.dates.indexOf(date);
        this.date_idx = idx;
        // update the val
        for (let i = 0; i < this.draw.states.length; i++) {
            const geo_state = this.draw.states[i];
            geo_state.date = date;
            geo_state.val = geo_state.data.cdts[idx];
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
                return fig_ani_heatmap_usstate.color_scale(d.val); 
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
            "U.S. Case Doubling Time Map on " + 
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
            this.proc_play = setInterval('fig_ani_heatmap_usstate.autoplay();', this.frame_duration);
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
    plots[fig_ani_heatmap_usstate.plot_id] = fig_ani_heatmap_usstate;
}