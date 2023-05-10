var fig_ani_heatmap_uscnty = {
    plot_id: 'fig_ani_heatmap_uscnty',
    cal_id: 'fig_ani_heatmap_uscnty_cal',
    plot_elm: null,
    plot_dict: null,
    plot_type: 'd3',
    geojson_file: 'us-10m.v2.json',
    // data_file: 'uscounty-data-latest.json',
    data_file: 'uscounty-data-history.json',

    // for d3.js
    num_max: 100,
    color_range: [
        'rgba(255, 0, 0, 0.6)',
        'rgba(255, 255, 0, 0.6)',
        'rgba(144, 238, 144, 0.6)'
    ],
    draw: {
        counties: [],
        states: []
    },
    proc_play: null,
    date_idx: 0,
    frame_duration: 300,
    mdy_str2date: d3.timeParse('%m/%d/%y'),
    date2Ymd_str: d3.timeFormat('%Y-%m-%d'),

    load: function() {
        $.when(
            $.get("./static/data/" + this.geojson_file),
            $.get("./covid_data/" + this.data_file, {ver: Math.random() }),
        ).done(function(data0, data1) {
            fig_ani_heatmap_uscnty.init(data0[0], data1[0]);
        })
    },

    init: function(usmap, data) {
        // bind data
        this.usmap = usmap;
        this.data = data;

        // init the us map data
        this.draw.counties = topojson.feature(usmap, usmap.objects.counties).features;
        // bind county data to map
        for (let i = 0; i < this.draw.counties.length; i++) {
            const geo_county = this.draw.counties[i];
            var fips = geo_county.id;
            if (this.data.data.hasOwnProperty(fips)) {
                geo_county.data = this.data.data[fips];
                geo_county.data.date = this.data.date;
                geo_county.data.dates = this.data.dates;
                
                // set current date
                geo_county.has_data = true;
                geo_county.date = this.data.date;
                geo_county.val = geo_county.data.cdts[geo_county.data.cdts.length - 1];
            } else {
                geo_county.has_data = false;
                geo_county.date = this.data.date;
                geo_county.val = this.num_max;
            }
        }

        // init the svg
        this.svg = d3.select("svg#" + this.plot_id);
        this.width = +this.svg.attr("width");
        this.height = +this.svg.attr("height");

        this.geo_path = d3.geoPath();
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
                var dt_idx = d.data.dates.indexOf(dt);
                var dt_idx_ystdy = dt_idx==0? 0:dt_idx-1;

                var cdt = d.val;
                var sdr = d.data.sdrs[dt_idx] * 100;
                var ncc = d.data.nccs[dt_idx];
                var dth = d.data.dths[dt_idx];
                
                var cdr = ncc == 0? 0:dth / ncc * 100;
                var sdr = d.data.sdrs[dt_idx] * 100;
                var fmt_comma = d3.format(',');

                var d_cdt = cdt - d.data.cdts[dt_idx_ystdy];
                var d_ncc = ncc - d.data.nccs[dt_idx_ystdy];
                var d_dth = dth - d.data.dths[dt_idx_ystdy];

                var content = "<span style='margin-left: 2.5px;'><b>" + d.data.countyName + ", " + d.data.state + " (" + d.id + ")</b> on " + dt + "</span><br>";
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
                fig_ani_heatmap_uscnty.svg.selectAll('path')
                .attr('transform', d3.event.transform);
            });
        
        this.svg.call(this.zoom);

        // draw the basic map
        this.g_counties = this.svg.append("g")
            .attr("class", "counties");
        this.g_counties.selectAll("path")
            .data(this.draw.counties)
            .enter().append("path")
            .attr("class", "county")
            .attr("fill", function(d) { 
                return fig_ani_heatmap_uscnty.color_scale(d.val); 
            })
            .attr("d", this.geo_path)
            // .on('click', this.county_on_click)
            .on('mouseover', this.tip.show)
            .on('mouseout', this.tip.hide);

        // draw the state boundary
        this.svg.append("path")
            .datum(topojson.mesh(this.usmap, this.usmap.objects.states, function(a, b) { return a !== b; }))
            .attr("class", "states")
            .attr("d", this.geo_path);
        
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
            var dt = fig_ani_heatmap_uscnty.mdy_str2date(d);
            var cdt = fig_ani_heatmap_uscnty.data.data['99999'].cdts[i];
            return [
                fig_ani_heatmap_uscnty.date2Ymd_str(dt),
                cdt
            ];
        })
        this.us_cal_data_label = [{
            value: JSON.parse(JSON.stringify(this.us_cal_data[this.us_cal_data.length - 1])),
            visualMap: false
        }];

        // create the option for echarts
        this.cal_option = {
            tooltip: {
                formatter: function(params) {
                    // console.log(params);
                    return params.value[0] + "<br>" +
                        'US CDT: ' + params.value[1].toFixed(2) + ' days';
                }
            },
            visualMap: {
                min: 0,
                max: this.num_max,
                right: 0,
                top: 0,
                itemHeight: 80,
                text: [ this.num_max + ' days', '0'],
                inRange: {
                    color: this.color_range
                },
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
            fig_ani_heatmap_uscnty.update_by_date(date_mdy);
        });
    },

    update_by_date: function(date) {
        var idx = this.data.dates.indexOf(date);
        this.date_idx = idx;
        // update the val
        for (let i = 0; i < this.draw.counties.length; i++) {
            const geo_county = this.draw.counties[i];
            if (geo_county.has_data) {
                // update the value
                geo_county.date = date;
                geo_county.val = geo_county.data.cdts[idx];
            } else {
                // do nothing here
            }
        }

        // update the date indicator
        this.us_cal_data_label = [{
            value: JSON.parse(JSON.stringify(this.us_cal_data[idx])),
            visualMap: false
        }];
        this.cal_option.series[1].data = this.us_cal_data_label;
        this.cal_chart.setOption(this.cal_option, true);

        // update the graph
        this.g_counties.selectAll("path")
            .data(this.draw.counties)
            .transition()
            .attr("fill", function(d) {
                return fig_ani_heatmap_uscnty.color_scale(d.val); 
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
            this.proc_play = setInterval('fig_ani_heatmap_uscnty.autoplay();', this.frame_duration);
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
    plots[fig_ani_heatmap_uscnty.plot_id] = fig_ani_heatmap_uscnty;
}