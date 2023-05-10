var figmker_crrw_calendar = {
    dom_id: '#fig_crrw_calendars',
    colorscale: [
        'green',
        'gold',
        'red'
    ],

    plot_id: null,
    data: null,
    country: null,
    state: null,
    fips: null,
    is_display_label: false,

    clear_and_make_fig: function(plot_id, data, country, state, fips, is_display_label) {
        this.plot_id = plot_id;
        this.data = data;
        this.country = country;
        this.state = state;
        this.fips = fips;
        this.is_display_label = is_display_label;

        $(this.dom_id).html('');
        $(this.dom_id + '_region').html(country);
        return this.make_fig(plot_id, data, country, state, fips, is_display_label);
    },

    reset_and_make_fig: function() {
        $(this.dom_id).html('');
        $(this.dom_id + '_region').html(this.country);
        return this.make_fig(this.plot_id, this.data, 
            this.country, this.state, this.fips, this.is_display_label
        );
    },

    make_fig: function(plot_id, data, country, state, fips, is_display_label) {
        if ($('#' + plot_id).length>0) {
            // have already there
            $( "#" + plot_id ).effect( 'pulsate', {}, 200, null );
            return;
        }
        
        if (typeof(is_display_label) == 'undefined') {
            is_display_label = true;
        }

        var lv = null;
        var cal_lbl = null;
        var data_idx = null;
        var _data = null;

        if (country != null) {
            lv = 'country';
            cal_lbl = country;
            data_idx = country;
            _data = data.world_data;
        } else if (fips != null) {
            lv = 'county'
            cal_lbl = fips;
            data_idx = fips;
            _data = data.county_data;
        } else {
            lv = 'state';
            cal_lbl = state;
            data_idx = state;
            _data = data.state_data;
        }
        
        var html = [
            '<div id="'+plot_id+'" class="fig-crrw-calendar d-flex justify-content-start align-items-start">', 
            is_display_label?'<div class="crrw-day-label">'+cal_lbl+'</div>' : '', 
            '<div id="'+plot_id+'_chart" class="crrw-day-chart"></div>',
            '</div>'
        ].join('');

        $(this.dom_id).append(html);

        var fig = {
            plot_id: plot_id,
            color_range: figmker_crrw_calendar.colorscale,
            country: country,
            state: state,
            fips: fips,
            data: data,
            date_idx: data.dates.length - 1
        };

        fig.cal_data = _data[data_idx].crcs.map(function(v, i) {
            return [ data.dates[i], {R:2, Y:1, G:0}[v]];
        });

        fig.scatter_data = [{
            value: fig.cal_data[fig.cal_data.length - 1],
            visualMap: false
        }];
        
        // 2021-02-28: let the script decide the last date by itself
        var dt_end = dayjs()
            .set('month', (dayjs().month() + 2))
            .set('date', 1)
            .subtract(1, 'day')
            .format('YYYY-MM-DD');

        var dt_start = '2020-03-01';

        // 2021-06-24: let the script decide the width
        if (jarvis.is_mobile()) {
            dt_start = dayjs()
                .subtract(4, 'month')
                .set('date', 1)
                .format('YYYY-MM-DD');
        }

        // put the calendar
        fig.option = {
            tooltip: {
                formatter: function(params) {
                    // console.log(params);
                    // if params
                    var val = params.value[1];
                    return params.value[0] + "<br>" +
                        'CrRW Status: ' + '<span class="crrw-day-badge crrw-day-'+val+'">'+{2:"R", 1:'Y', 0:'G'}[val]+'</span>';
                }
            },
            visualMap: {
                min: 0,
                max: 2,
                // right: 0,
                // top: 0,
                // itemHeight: 80,
                // text: [this.num_max + ' days', '0'],
                inRange: {
                    color: fig.color_range
                },
                show: false
            },
            calendar: {
                top: 18,
                left: 50,
                cellSize: 10,
                range: [dt_start, dt_end],
                monthLabel: {
                    show: true,
                    fontSize: 10,
                    formatter: function(param) {
                        if (param.M == 1) {
                            return param.yyyy + ' ' + param.nameMap;
                        } else {
                            return param.nameMap;
                        }
                    }
                },
                yearLabel: {
                    fontSize: 12
                },
                itemStyle: {
                    borderWidth: 1
                }
            },
            series: [{
                type: 'heatmap',
                name: fig.plot_id + '-' + 'cal',
                coordinateSystem: 'calendar',
                data: fig.cal_data
            }, 
            {
                type: 'scatter',
                name: fig.plot_id + '-' + 'dot',
                coordinateSystem: 'calendar',
                data: fig.scatter_data,
                symbolSize: 9,
                itemStyle: {
                    color: 'black'
                }
            }]
        };
        fig.chart = echarts.init(document.getElementById(fig.plot_id + '_chart'));
        fig.chart.setOption(fig.option);

        fig.update_by_date = function(date) {
            this.date_idx = this.data.dates.indexOf(date);

            // udpate the scatter
            this.scatter_data = [{
                value: this.cal_data[this.date_idx],
                visualMap: false
            }];
            
            // update the echart
            this.option.series[1].data = this.scatter_data;
            this.chart.setOption(this.option, true);
        },

        // bind click event
        fig.chart.on('click', function(params) {
            console.log(params);

            // get the figure obj
            var fig_plot_id = params.seriesName.split('-')[0];
            var fig_obj = window[fig_plot_id];

            // get date
            var date_Ymd = params.value[0];
            // var date_mdy = d3.timeFormat('%-m/%-d/%y')(d3.timeParse('%Y-%m-%d')(date_Ymd));
            console.log('* clicked ' + date_Ymd);

            // update the map
            if (jarvis.hasOwnProperty('update_by_date')) {
                jarvis.update_by_date(date_Ymd);
            }
        });

        return fig;
    }
}