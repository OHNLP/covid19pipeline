var fig_ani_heatmap_world = {
    plot_id: 'fig_ani_heatmap_world',
    cal_id: 'fig_ani_heatmap_world_cal',
    plot_elm: null,
    plot_dict: null,
    plot_type: 'd3',
    geojson_file: 'countries-50m.json',
    data_file: 'world-data-history.json',

    // for d3.js
    num_max: 100,
    color_range: [
        'rgba(255, 0, 0, 0.6)',
        'rgba(255, 255, 0, 0.6)',
        'rgba(144, 238, 144, 0.6)'
    ],
    draw: {
        countries: []
    },
    zoom_s: 1,
    proc_play: null,
    date_idx: 0,
    frame_duration: 300,
    mdy_str2date: d3.timeParse('%m/%d/%y'),
    date2Ymd_str: d3.timeFormat('%Y-%m-%d'),
    fmt_comma: d3.format(","),
    width: 500,
    height: 400,
    geoname2dataname: function(name) {
        var g2d = {
            'W. Sahara': 'Western Sahara',
            'United States of America': 'US',
            'Dem. Rep. Congo': 'Congo (Brazzaville)',
            'Dominican Rep.': 'Dominican Republic',
            'Central African Rep.': 'Central African Republic',
            'Congo': 'Congo (Kinshasa)',
            'Eq. Guinea': 'Equatorial Guinea',
            'South Korea': 'Korea, South',
            'Taiwan': 'Taiwan*',
            'N. Cyprus': 'Cyprus',
            'Bosnia and Herz.': 'Bosnia and Herzegovina',
            'Macedonia': 'North Macedonia',
            'S. Sudan': 'South Sudan',
            // missing in data
            'Fr. S. Antarctic Lands': '',
            'Puerto Rico': '',
            "Côte d'Ivoire": '',
            'Falkland Is.': '',
            'Greenland': '',
            'Somaliland': '',
            'Antarctica': '',
            'eSwatini': '',
            'Palestine': '',
            'Vanuatu': '',
            'Myanmar': '',
            'North Korea': '',
            'Turkmenistan': '',
            'New Caledonia': '',
            'Solomon Is.': '',
        }
        if (g2d.hasOwnProperty(name)) {
            return g2d[name];
        } else {
            return name;
        }
    },

    load: function() {
        $.when(
            $.get("./static/data/" + this.geojson_file),
            $.get("./covid_data/" + this.data_file, {ver: Math.random() }),
        ).done(function(data0, data1) {
            fig_ani_heatmap_world.init(data0[0], data1[0]);
        })
    },

    on_zoom: function() {
        console.log('! on zoom')
        console.log('d3.event.transform: ', d3.event.transform);
        var t = [ d3.event.transform.x, d3.event.transform.y ];
        var h = 0;
        var width = fig_ani_heatmap_world.width;
        var height = fig_ani_heatmap_world.height;

        fig_ani_heatmap_world.zoom_s = d3.event.transform.k;
      
        t[0] = Math.min(
          (width/height)  * (fig_ani_heatmap_world.zoom_s - 1), 
          Math.max( width * (1 - fig_ani_heatmap_world.zoom_s), t[0] )
        );
      
        t[1] = Math.min(
          h * (fig_ani_heatmap_world.zoom_s - 1) + h * fig_ani_heatmap_world.zoom_s, 
          Math.max(height  * (1 - fig_ani_heatmap_world.zoom_s) - h * fig_ani_heatmap_world.zoom_s, t[1])
        );
      
        fig_ani_heatmap_world.g_countries.attr("transform", "translate(" + t + ")scale(" + fig_ani_heatmap_world.zoom_s + ")");
      
        //adjust the stroke width based on zoom level
        d3.selectAll(".country").style("stroke-width", 1 / fig_ani_heatmap_world.zoom_s);
      
        // mouse = d3.mouse(this); 
        
        // if(s === 1 && mouseClicked) {
        //   //rotateMap(d3.mouse(this)[0]);
        //   rotateMap(mouse[0]);
        //   return;
        // }
    },

    on_zoom_end: function() {
        if(this.zoom_s !== 1) return;
    },

    init: function(wdmap, data) {
        // bind data
        this.wdmap = wdmap;
        this.data = data;
        this.draw.countries = topojson.feature(wdmap, wdmap.objects.countries).features;

        // bind state data to map
        for (let i = 0; i < this.draw.countries.length; i++) {
            var geo = this.draw.countries[i];
            var country_id = geo.id;
            var name = geo.properties.name;
            data_name = this.geoname2dataname(name);
            geo.name = data_name;
            geo.date = this.data.date;
            geo.dates = this.data.dates;
            if (this.data.data.hasOwnProperty(data_name)) {
                geo.val = this.data.data[data_name].cdts[ this.data.data[data_name].cdts.length - 1];
                geo.data = this.data.data[data_name];
            } else {
                geo.val = this.num_max;
                geo.data = null;
                console.log('* name not found: ', name);
            }
        }

        // init the svg
        this.svg = d3.select("svg#" + this.plot_id);
        this.width = +$('#' + this.plot_id).css('width').replace('px', '')
        this.height = +$('#' + this.plot_id).css('height').replace('px', '')
        console.log('* svg.width:', this.width);
        console.log('* svg.height:', this.height);

        // for map display
        this.geo_path = d3.geoPath().projection(d3.geoEquirectangular());

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
                if (d.data == null) {
                    return "<span style='margin-left: 2.5px;'><b>" + d.properties.name + "</b> on " + dt + "<br> &nbsp;No Data</span>";
                }
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
            .scaleExtent([1, 12])
            .on('zoom', function() {
                // console.log(d3.event.transform);
                fig_ani_heatmap_world.svg.selectAll('path')
                    .attr('transform', d3.event.transform);
                d3.selectAll(".country").style("stroke-width", .5 / d3.event.transform.k);
            });
        this.svg.call(this.zoom);

        // the semantic zoom
        // this.zoom = d3.zoom()
        //     .scaleExtent([1, 10])
        //     .on("zoom", this.on_zoom)
        //     .on("end", this.on_zoom_end);
        // this.svg.call(this.zoom);

        // draw the basic map
        this.g_countries = this.svg.append("g")
            .attr("class", "countries");

        this.g_countries.selectAll("path")
            .data(this.draw.countries)
            .enter().append("path")
            .attr("class", "country")
            .attr("fill", function(d) { 
                return fig_ani_heatmap_world.color_scale(d.val); 
            })
            .attr("d", this.geo_path)
            .attr("stroke-width", .5)
            // .on('click', this.county_on_click)
            .on('mouseover', this.tip.show)
            .on('mouseout', this.tip.hide);
                
        // draw the date
        this.g_info = this.svg.append("text")
            .attr('id', 'g-info')
            .attr("transform", "translate(0, 40)")
            .attr('x', 520)
            .attr('y', 360)
            .attr('fill', 'black')
            .attr("font-size", "16")
            .attr("font-weight", "bold")
            .text("");
        this.show_date_on_map(this.data.date);

        // init the calendar
        this.wd_cal_data = this.data.dates.map(function(d, i) {
            var dt = fig_ani_heatmap_world.mdy_str2date(d);
            var cdt = fig_ani_heatmap_world.data.data['WORLD'].cdts[i];
            return [
                fig_ani_heatmap_world.date2Ymd_str(dt),
                cdt
            ];
        });
        this.wd_cal_data_label = [{
            value: JSON.parse(JSON.stringify(this.wd_cal_data[this.wd_cal_data.length - 1])),
            visualMap: false
        }];

        // create the option for echarts
        this.cal_option = {
            tooltip: {
                formatter: function(params) {
                    // console.log(params);
                    // if params
                    return params.value[0] + "<br>" +
                        'WORLD CDT: ' + params.value[1].toFixed(2) + ' days';
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
                data: this.wd_cal_data
            }, 
            {
                type: 'scatter',
                coordinateSystem: 'calendar',
                data: this.wd_cal_data_label,
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
            fig_ani_heatmap_world.update_by_date(date_mdy);
        });
    },

    update_by_date: function(date) {
        var idx = this.data.dates.indexOf(date);
        this.date_idx = idx;
        // update the val
        for (let i = 0; i < this.draw.countries.length; i++) {
            const geo = this.draw.countries[i];
            geo.date = date;
            if (geo.data == null) {
                geo.val = this.num_max;
            } else {
                geo.val = geo.data.cdts[idx];
            }
        }

        // update the date indicator
        this.wd_cal_data_label = [{
            value: JSON.parse(JSON.stringify(this.wd_cal_data[idx])),
            visualMap: false
        }];
        this.cal_option.series[1].data = this.wd_cal_data_label;
        this.cal_chart.setOption(this.cal_option, true);

        // update the graph
        this.g_countries.selectAll("path")
            .data(this.draw.countries)
            .transition()
            .attr("fill", function(d) {
                return fig_ani_heatmap_world.color_scale(d.val); 
            });
        
        // update the info
        this.show_date_on_map(date);
    },

    show_date_on_map: function(date) {
        $('#g-info').html(
            "Globe-level Case Doubling Time Map on " + 
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
            this.proc_play = setInterval('fig_ani_heatmap_world.autoplay();', this.frame_duration);
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
    plots[fig_ani_heatmap_world.plot_id] = fig_ani_heatmap_world;
}