var figmker_testline_mayo6 = {
    data_file: 'mayo_regions_tests.json',
    make_fig: function(mayo_site, plot_id, data, tpr_refs) {
        console.log('* make_fig: ' + mayo_site + ' ' + plot_id);
        var fig = {
            plot_id: plot_id,
            data: data
        };
        fig.series = [];

        // add the cum tests
        fig.series.push({
            name: 'Total Tests',
            data: data.data[mayo_site].total_completed_tests,
            type: 'line',
            smooth: true,
            lineStyle: {
                width: 1.5,
                type: 'solid',
                color: 'darkblue'
            },
            itemStyle: {
                color: 'darkblue'
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

        // add tpr data
        var tpr = data.data[mayo_site].tpr_4dm;
        tpr = tpr.map(function(r){ return (r*100).toFixed(1); });
        fig.series.push({
            name: 'Pos. Rate',
            data: tpr,
            type: 'line',
            smooth: true,
            yAxisIndex: 1,
            symbol: 'rect',
            symbolSize: 4,
            lineStyle: {
                width: 1.5,
                type: 'dotted',
                color: 'firebrick'
            },
            itemStyle: {
                color: 'firebrick'
            },
            markPoint: {
                
                label: {
                    fontSize: 10,
                    color: 'white'
                },
                data: [
                    {
                        type: 'max', name: 'Max',
                        symbolSize: 45,
                    },
                    {
                        name: 'coordinate',
                        symbolSize: 35,
                        coord: [data.last_update, tpr[tpr.length-1]],
                        value: tpr[tpr.length-1]
                    }
                ]
            },
        });
        var legends = ['Total Tests', 'Pos. Rate'];
        // add refs if defined
        if (typeof(tpr_refs)!='undefined') {
            for (let i = 0; i < tpr_refs.length; i++) {
                const ref = tpr_refs[i];
                var ref_name = ref.name + ' Pos.Rate'
                fig.series.push({
                    name: ref_name,
                    data: ref.tpr_4dm.map((v)=> (v*100).toFixed(1)),
                    yAxisIndex: 1,
                    type: 'line',
                    smooth: true,
                    symbol: 'rect',
                    symbolSize: 2,
                    lineStyle: {
                        width: 1,
                        type: 'dotted',
                        color: 'grey'
                    },
                    itemStyle: {
                        color: 'grey'
                    },
                    markPoint: {
                
                        label: {
                            fontSize: 10,
                            color: 'white'
                        },
                        data: [
                            {
                                type: 'max', name: 'Max',
                                symbolSize: 45,
                            }
                        ]
                    },
                });
                legends.push(ref_name);
            }
        }
        // config the plots
        var f_get_y1_max = function(value) {
            if (value.max < 10000) {
                return 10000;
            } else if (value.max < 50000) {
                return 50000;
            } else if (value.max < 100000) {
                return 100000;
            } else {
                return 150000;
            }
        };
        
        fig.option = {
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    // console.log(params);
                    var str = 'Tests Trends on ' + params[0].name + ': <br>';

                    for (let i = 0; i < params.length; i++) {
                        const param = params[i];
                        if (param.seriesName.toUpperCase().includes('RATE')) {
                            str += param.seriesName + ' (4-day Smoothed)';
                            str += ': <b>' + (param.value) + '% </b><br>';
                        } else {
                            str += param.seriesName;
                            str += ': <b>' + (param.value) + '</b><br>';
                        }
                    }
                    return str;
                }
            },
            grid: {
                top: 30,
                right: 40,
                bottom: 20,
                left: 50
            },
            legend: {
                data: legends,
                symbolKeepAspect: false,
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
                name: 'Total Tests',
                type: 'value',
                max: f_get_y1_max
            }, {
                name: 'Pos.Rate(%)',
                type: 'value',
                splitLine: {
                    show: false
                },
                axisLabel: {
                    formatter: function (val) {
                        return val + '%';
                    }
                },
                max: 25
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