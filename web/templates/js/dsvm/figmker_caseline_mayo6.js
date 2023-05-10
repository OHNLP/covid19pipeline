var figmker_caseline_mayo6 = {
    data_file: 'mayo_regions_new_cum_cases.json',
    make_fig: function(mayo_site, plot_id, data) {
        var fig = {
            plot_id: plot_id,
            data: data
        };
        fig.series = [];
        // add the cum cases
        fig.series.push({
            name: 'Cumulative Cases',
            data: data.values.cum_cases,
            type: 'line',
            smooth: true,
            lineStyle: {
                width: 1.5,
                type: 'solid',
                color: 'darkred'
            },
            itemStyle: {
                color: 'darkred'
            },
            markPoint: {
                symbolSize: 50,
                label: {
                    fontSize: 10,
                    color: 'white'
                },
                data: [
                    {type: 'max', name: 'Max'}
                ]
            },
        });
        // add the new cases
        var value_last = data.values.new_cases[data.values.new_cases.length-1];
        fig.series.push({
            name: 'New Cases',
            data: data.values.new_cases,
            type: 'line',
            smooth: true,
            yAxisIndex: 1,
            symbol: 'rect',
            symbolSize: 4,
            lineStyle: {
                width: 1.5,
                type: 'dotted',
                color: 'darkorange'
            },
            itemStyle: {
                color: 'darkorange'
            },
            markPoint: {
                symbolSize: 30,
                label: {
                    fontSize: 10,
                    color: 'white'
                },
                data: [
                    {type: 'max', name: 'Max'},
                    {
                        name: 'coordinate',
                        symbolSize: 35,
                        coord: [data.last_update, value_last],
                        value: value_last
                    }
                ]
            },
        });
        // config the plots
        var max_new_cases = Math.max.apply(null, data.values.new_cases);
        var f_get_y1_max = function(value) {
            if (value.max < 500) {
                return 500;
            } else if (value.max < 1000) {
                return 1000;
            } else if (value.max < 5000) {
                return 5000;
            } else if (value.max < 10000) {
                return 10000;
            } else if (value.max < 20000) {
                return 20000;
            } else if (value.max < 50000) {
                return 50000;
            } else if (value.max < 100000) {
                return 100000;
            } else if (value.max < 150000) {
                return 150000;
            } else if (value.max < 200000) {
                return 200000;
            } else if (value.max < 250000) {
                return 250000;
            } else if (value.max < 300000) {
                return 300000;
            } else {
                return 500000;
            }
        };
        var f_get_y2_max = function(value) {
            if (value.max < 50) {
                return 50;
            } else if (value.max < 100) {
                return 100;
            } else if (value.max < 500) {
                return 500;
            } else if (value.max < 1000) {
                return 1000;
            } else if (value.max < 5000) {
                return 5000;
            } else if (value.max < 10000) {
                return 10000;
            }
        };
        fig.option = {
            tooltip: {
                trigger: 'axis'
            },
            grid: {
                top: 30,
                right: 40,
                bottom: 20,
                left: 50
            },
            legend: {
                data: ['New Cases', 'Cumulative Cases'],
                symbolKeepAspect: false,
                // left: 30,
                // right: 0,
                // itemWidth: 20,
                textStyle: {
                    fontSize: 10
                }
            },
            xAxis: {
                type: 'category',
                name: '',
                data: data.dates
            },
            yAxis: [{
                name: 'Cum. Cases',
                type: 'value',
                max: f_get_y1_max
            }, {
                name: 'New Cases',
                type: 'value',
                splitLine: {
                    show: false
                },
                max: f_get_y2_max
            }],
            series: fig.series
        };

        fig.plot_chart = echarts.init(document.getElementById(fig.plot_id));
        fig.plot_chart.setOption(fig.option);

        // resize!
        fig.resize = function() {
            if (this.plot_chart == null) {
    
            } else {
                this.plot_chart.resize();
            }
        }

        // update the last update
        $('#' + plot_id + '_last_update').html(data.last_update);

        return fig;
    }
};