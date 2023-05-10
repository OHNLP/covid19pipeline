var figmker_crrw_trend = {
    version: '1.0.0',

    colorscale: [
        'green',
        'gold',
        'red'
    ],
    
    make_fig: function(plot_id, data, state, fips) {
        if ($('#' + plot_id).length>0) {
            // have already there
            // $( "#" + plot_id ).effect( 'pulsate', {}, 200, null );
            // move to the first
            var parent_id = $( "#" + plot_id ).parent().attr('id');
            $( "#" + plot_id ).prependTo('#'+parent_id);
            return;
        }
        var fig = {
            plot_id: plot_id,
            color_range: figmker_crrw_trend.colorscale,
            state: state,
            fips: fips,
            data: data,
            crp_threshold_1: 15,
            crp_threshold_2: 30,
            crp_threshold_3: 10
        };
        var is_cnty = false;
        var datatmp = null;
        if (typeof(fips)=='undefined') {
            is_cnty = false;
            datatmp = data.state_data[state];
        } else if (fips == 'mchrr') {
            is_cnty = false;
            datatmp = data.mc_data[state];
        } else if (fips == 'world') {
            // the state is country code
            is_cnty = false;
            datatmp = data.world_data[state];
        } else {
            is_cnty = true;
            if (data.data.hasOwnProperty(fips)) {
                datatmp = data.data[fips];
            }
        }
        if (datatmp == null) {
            return null;
        }
        fig.is_cnty = is_cnty;
        
        // create the DOM obj for this figure
        var cal_lbl = is_cnty? 
            datatmp.name + ', ' + datatmp.state : 
            datatmp.name;
        $('#fig_crrw_trends').prepend(
            '<div id="'+fig.plot_id+'" class="fig-crrw-trend d-flex justify-content-start align-items-start align-items-stretch">'+
            '<div class="crrw-trend-info">'+
            '<div class="crrw-trend-bar"><a href="javascript:void(0);" title="Remove this chart" onclick="jarvis.remove_trend(\''+fig.plot_id+'\')"><i class="fa fa-times"></i></a></div>'+
            '<div class="crrw-trend-label">'+cal_lbl+'</div>'+
            '</div>'+
            '<div id="'+fig.plot_id+'_chart" class="crrw-trend-chart"></div>' + 
            '</div>'
        );

        fig.cal_data = [];
        var base_zero = 50;
        fig.data_crps = datatmp.crps.map(function(v, i) {
            return v + base_zero;
        });
        fig.data_crts = datatmp.crts.map(function(v, i) {
            if (v>5) v = 5;
            return -v * 10 + base_zero;
        });
        // get the area fill of CrRW status
        fig.data_crrw_y = datatmp.crcs.map(function(v, i) {
            if (v == 'Y') {
                return fig.data_crps[i] - fig.data_crts[i];
            } else {
                return null;
            }
        });
        fig.data_crrw_r = datatmp.crcs.map(function(v, i) {
            if (v == 'R') {
                return fig.data_crps[i] - fig.data_crts[i];
            } else {
                return null;
            }
        });
        fig.data_crrw_g = datatmp.crcs.map(function(v, i) {
            if (v == 'G') {
                return fig.data_crps[i] - fig.data_crts[i];
            } else {
                return null;
            }
        });
        // get the CrRW status bars
        fig.data_crrw_bar = datatmp.crcs.map(function(v, i) {
            var c = {G:'green', Y:'gold', R:'red'}[v];
            var v2 = {G:0, Y:1, R:2}[v];
            return { value: v, itemStyle: {color: c} };
        });
        
        // put the calendar
        fig.option = {
            legend: {
                data: [
                    'Cr7d100k',
                    'RW_Cr7d100k'
                ],
                top: 10,
                left: 50,
                backgroundColor: 'rgba(255,255,255,.5)'
            },
            axisPointer: {
                type: 'line',
                link: {xAxisIndex: 'all'}
            },
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    // console.log(params);
                    // if params
                    var tip = [params[0].axisValue + '<br>'];
                    for (let i = 0; i < 3; i++) {
                        var param = params[i];
                        var val = param.value;
                        if (i==0) {
                            val = (val - 50).toFixed(2);
                        } else if (i==1) {
                            val = (- (val - 50) / 10).toFixed(2);
                        } else {
                            val = '<span class="crrw-day-badge crrw-day-'+val+'">'+val+'</span>';
                        }
                        tip.push(param.marker + ' ' + param.seriesName + ': ' + val + '<br>');
                    }
                    return tip.join('');
                }
            },
            xAxis: {
                type: 'category',
                data: data.dates,
                axisLabel: {
                    formatter: function (value, idx) {
                        var date = new Date(value);
                        return [date.getMonth() + 1, date.getDate()].join('-');
                    }
                },
                splitLine: {
                    show: true
                }
            },
            yAxis: {
                type: 'value',
                min: 20,
                max: 110,
                interval: 10,
                axisLabel: {
                    formatter: function (value, idx) {
                        if (value <= 50) {
                            return (5 - Math.abs(value / 10)).toFixed(0);
                        } else {
                            return (value - 50).toFixed(0);
                        }
                    }
                },
            },
            grid: {
                top: 10,
                right: 5,
                bottom: 20,
                left: 40
            },
            graphic: [{
                type: 'group',
                left: '45',
                top: '35',
                children: [{
                    type: 'rect',
                    z: 90,
                    left: 'left',
                    top: 'middle',
                    shape: {
                        width: 80,
                        height: 14
                    },
                    style: {
                        fill: '#fff',
                        lineWidth: 0
                    }
                }, {
                    type: 'text',
                    z: 100,
                    left: 'left',
                    top: 'middle',
                    style: {
                        fill: 'rgba(255, 141, 4, 0.5)',
                        text: 'Cr7d100k=30',
                        font: '11px'
                    }
                }]
            }, {
                type: 'group',
                left: '45',
                top: '55',
                children: [{
                    type: 'rect',
                    z: 90,
                    left: 'left',
                    top: 'middle',
                    shape: {
                        width: 80,
                        height: 14
                    },
                    style: {
                        fill: '#fff',
                        lineWidth: 0
                    }
                }, {
                    type: 'text',
                    z: 100,
                    left: 'left',
                    top: 'middle',
                    style: {
                        fill: 'rgba(255, 141, 4, 0.5)',
                        text: 'Cr7d100k=15',
                        font: '11px'
                    }
                }]
            }, {
                type: 'group',
                left: '45',
                top: '78',
                children: [{
                    type: 'rect',
                    z: 90,
                    left: 'left',
                    top: 'middle',
                    shape: {
                        width: 80,
                        height: 10
                    },
                    style: {
                        fill: '#fff',
                        lineWidth: 0
                    }
                }, {
                    type: 'text',
                    z: 100,
                    left: 'left',
                    top: 'middle',
                    style: {
                        fill: 'rgba(255, 141, 4, 0.5)',
                        text: 'Cr7d100k=10',
                        font: '9px'
                    }
                }]
            }, {
                type: 'group',
                left: '45',
                top: '105',
                children: [{
                    type: 'rect',
                    z: 90,
                    left: 'left',
                    top: 'middle',
                    shape: {
                        width: 80,
                        height: 14
                    },
                    style: {
                        fill: '#fff',
                        lineWidth: 0
                    }
                }, {
                    type: 'text',
                    z: 100,
                    left: 'left',
                    top: 'middle',
                    style: {
                        fill: 'rgba(255, 0, 0, 0.5)',
                        text: 'RW_Cr7d100k=1',
                        font: '11px'
                    }
                }]
            }],
            series: [
            {
                type: 'line',
                name: 'Cr7d100k',
                data: fig.data_crps,
                symbolSize: 1,
                itemStyle: {
                    color: 'blue'
                },
                lineStyle: {
                    color: 'blue'
                },
                markLine: {
                    symbol: 'none',
                    lineStyle: {
                        color: 'orange'
                    },
                    data: [{ 
                        name: 'Cr7d100k=' + fig.crp_threshold_1, 
                        yAxis: base_zero + fig.crp_threshold_1
                    }, 
                    { 
                        name: 'Cr7d100k=' + fig.crp_threshold_2, 
                        yAxis: base_zero + fig.crp_threshold_2
                    },
                    { 
                        name: 'Cr7d100k=' + fig.crp_threshold_3, 
                        yAxis: base_zero + fig.crp_threshold_3
                    }]
                }
            },
            {
                type: 'line',
                name: 'RW_Cr7d100k',
                data: fig.data_crts,
                symbolSize: 1,
                itemStyle: {
                    color: 'purple'
                },
                lineStyle: {
                    color: 'purple'
                },
                markLine: {
                    symbol: 'none',
                    lineStyle: {
                        color: 'red'
                    },
                    data: [{ 
                        name: 'RW_Cr7d100k=1', 
                        yAxis: base_zero - 10,
                        // label: {
                        //     formatter: '{b}',
                        //     position: 'insideStartBottom'
                        // }
                    }]
                },
                stack: 'crrw'
            },
            {
                type: 'bar',
                name: 'CrRW Status',
                show: false,
                data: fig.data_crrw_bar,
            },
            // for the area
            {
                type: 'line',
                data: fig.data_crrw_r,
                symbolSize: 0,
                areaStyle: {
                    color: 'red'
                },
                lineStyle: {
                    width: 0
                },
                stack: 'crrw'
            },
            {
                type: 'line',
                data: fig.data_crrw_y,
                symbolSize: 0,
                areaStyle: {
                    color: 'gold'
                },
                lineStyle: {
                    width: 0
                },
                stack: 'crrw'
            },
            {
                type: 'line',
                data: fig.data_crrw_g,
                symbolSize: 0,
                areaStyle: {
                    color: 'green'
                },
                lineStyle: {
                    width: 0
                },
                stack: 'crrw'
            }
            ]
        };
        fig.chart = echarts.init(document.getElementById(fig.plot_id + '_chart'));
        fig.chart.setOption(fig.option);

        // bind click event
        fig.chart.on('click', function(params) {
            // console.log(params);
            var date_Ymd = params.data[0];
            var date_mdy = d3.timeFormat('%-m/%-d/%y')(d3.timeParse('%Y-%m-%d')(date_Ymd));
            
            console.log('* clicked ' + date_mdy);
        });

        fig.chart.group = 'trends';
        echarts.connect('trends');

        return fig;
    }
}