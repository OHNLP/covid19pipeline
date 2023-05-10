var figmker_crrw_trend = {
    version: '1.2.0',

    crp_threshold_1: 15,
    crp_threshold_2: 30,
    crp_threshold_3: 10,

    colorscale: [
        'green',
        'gold',
        'red'
    ],

    // the y axis base min value for drawing figure, NOT the CR or RW
    y_base_min: 20,

    // for a range [20, 110], the 50 is the lower center line
    y_base_zero: 50,

    // the y axis base max value for drawing figure, NOT the CR or RW
    y_base_max: 110,

    // the y axis interval value
    y_base_interval: 10,

    // the Cr ymax ratio
    // we could use a ratio to calculate how much the real value is
    // the y axis is [50, 110], so the mapping range is [0, 60]
    // the ratio to the range would be:
    // 1 -> [0, 610]
    // 2 -> [0, 120]
    // 3 -> [0, 180]
    // 4 -> [0, 240]
    // 5 -> [0, 300]
    // 6 -> [0, 360]
    // 7 -> [0, 420]
    // 8 -> [0, 480]
    // 9 -> [0, 540]
    // 10-> [0, 600]
    // later we could use different value for different region maybe
    y_cr_ratio: 5,

    // the RW unit on y aixs
    y_rw_unit: 10,

    // for formatting the y label
    y_label_formatter: function (value, idx) {
        if (value <= figmker_crrw_trend.y_base_zero) {
            // the lower part, the convert rule is simple,
            // this is RW_Cr7d100k.
            // return (5 - Math.abs(value / 10)).toFixed(0);
            return figmker_crrw_trend.get_yv2rw(value).toFixed(0);
        } else {
            // the upper part
            // this is Cr7d100k.
            return (figmker_crrw_trend.get_yv2cr(value)).toFixed(0);
        }
    },

    get_yv2cr: function(value) {
        // from the y-axis value to the Cr value
        return (value - figmker_crrw_trend.y_base_zero) * figmker_crrw_trend.y_cr_ratio;
    },

    get_yv2rw: function(value) {
        // from the y-axis value to the RW value
        return (figmker_crrw_trend.y_base_zero - value) / figmker_crrw_trend.y_rw_unit;
    },

    get_cr2yv: function(cr) {
        // from the actual CR to the value on y-axis
        return cr / figmker_crrw_trend.y_cr_ratio + figmker_crrw_trend.y_base_zero;
    },

    get_rw2yv: function(rw) {
        // from the actual RW to the value on y-axis
        if (rw > 5) { rw = 5; }
        return figmker_crrw_trend.y_base_zero - rw * figmker_crrw_trend.y_rw_unit;
    },


    make_fig: function(plot_id, data, state, fips, prependTo_id) {
        if ($('#' + plot_id).length>0) {
            // have already there
            // $( "#" + plot_id ).effect( 'pulsate', {}, 200, null );
            // move to the first
            var parent_id = $( "#" + plot_id ).parent().attr('id');
            $( "#" + plot_id ).prependTo('#'+parent_id);
            return;
        }
        if (typeof(prependTo_id) == 'undefined') {
            prependTo_id = '#fig_crrw_trends';
        }
        var fig = {
            plot_id: plot_id,
            color_range: figmker_crrw_trend.colorscale,
            state: state,
            fips: fips,
            data: data,
            crp_threshold_1: figmker_crrw_trend.crp_threshold_1,
            crp_threshold_2: figmker_crrw_trend.crp_threshold_2,
            crp_threshold_3: figmker_crrw_trend.crp_threshold_3
        };
        var is_cnty = false;
        var datatmp = null;
        if (typeof(fips)=='undefined') {
            is_cnty = false;
            datatmp = data.state_data[state];
        } else if (fips == 'mchrr') {
            is_cnty = false;
            datatmp = data.mchrr_data[state];
        } else if (fips == 'world') {
            // the state is country code
            is_cnty = false;
            datatmp = data.world_data[state];
        } else {
            is_cnty = true;
            if (data.county_data.hasOwnProperty(fips)) {
                datatmp = data.county_data[fips];
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
        $(prependTo_id).prepend(
            '<div id="'+fig.plot_id+'" class="fig-crrw-trend d-flex justify-content-start align-items-start align-items-stretch">'+
            '<div class="crrw-trend-info">'+
            '<div class="crrw-trend-bar"><a href="javascript:void(0);" title="Remove this chart" onclick="jarvis.remove_trend(\''+fig.plot_id+'\')"><i class="fa fa-times"></i></a></div>'+
            '<div class="crrw-trend-label">'+cal_lbl+'</div>'+
            '</div>'+
            '<div id="'+fig.plot_id+'_chart" class="crrw-trend-chart"></div>' + 
            '</div>'
        );

        fig.cal_data = [];
        // var base_zero = 50;

        // convert the CR to y-aixs value
        fig.data_crps = datatmp.crps.map(function(v, i) {
            return figmker_crrw_trend.get_cr2yv(v);
        });

        // convert the RW to y-axis value
        fig.data_crts = datatmp.crts.map(function(v, i) {
            // if (v>5) v = 5;
            return figmker_crrw_trend.get_rw2yv(v);
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
                    for (var i = 0; i < 3; i++) {
                        var param = params[i];
                        var val = param.value;
                        if (i==0) {
                            // this is the Cr7d100k
                            // val = ((val - 50) * 2).toFixed(2);
                            val = figmker_crrw_trend.get_yv2cr(val).toFixed(2);
                        } else if (i==1) {
                            // this is the RW_Cr7d100k
                            // val = (- (val - 50) / 10).toFixed(2);
                            val = figmker_crrw_trend.get_yv2rw(val);

                            // because we cut off at 5
                            if (val >= 5) {
                                val = '5.00 or higher';
                            } else {
                                val = val.toFixed(2);
                            }
                            
                        } else {
                            // this is the CrRW status
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
                min: figmker_crrw_trend.y_base_min,
                max: figmker_crrw_trend.y_base_max,
                interval: figmker_crrw_trend.y_base_interval,
                axisLabel: {
                    formatter: figmker_crrw_trend.y_label_formatter
                },
            },
            grid: {
                top: 10,
                right: 5,
                bottom: 20,
                left: 40
            },
            graphic: [
            {
                type: 'group',
                left: '45',
                top: '0',
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
                        fill: 'rgba(0, 0, 0, 1)',
                        text: cal_lbl,
                        font: '11px'
                    }
                }]
            }, 
            // {
            //     type: 'group',
            //     left: '45',
            //     top: '55',
            //     children: [{
            //         type: 'rect',
            //         z: 90,
            //         left: 'left',
            //         top: 'middle',
            //         shape: {
            //             width: 80,
            //             height: 14
            //         },
            //         style: {
            //             fill: '#fff',
            //             lineWidth: 0
            //         }
            //     }, {
            //         type: 'text',
            //         z: 100,
            //         left: 'left',
            //         top: 'middle',
            //         style: {
            //             fill: 'rgba(255, 141, 4, 0.5)',
            //             text: 'Cr7d100k=' + figmker_crrw_trend.crp_threshold_2,
            //             font: '11px'
            //         }
            //     }]
            // }, 
            // {
            //     type: 'group',
            //     left: '45',
            //     top: '78',
            //     children: [{
            //         type: 'rect',
            //         z: 90,
            //         left: 'left',
            //         top: 'middle',
            //         shape: {
            //             width: 80,
            //             height: 10
            //         },
            //         style: {
            //             fill: '#fff',
            //             lineWidth: 0
            //         }
            //     }, {
            //         type: 'text',
            //         z: 100,
            //         left: 'left',
            //         top: 'middle',
            //         style: {
            //             fill: 'rgba(255, 141, 4, 0.5)',
            //             text: 'Cr7d100k=' + figmker_crrw_trend.crp_threshold_3,
            //             font: '9px'
            //         }
            //     }]
            // }, 
            // {
            //     type: 'group',
            //     left: '45',
            //     top: '105',
            //     children: [{
            //         type: 'rect',
            //         z: 90,
            //         left: 'left',
            //         top: 'middle',
            //         shape: {
            //             width: 80,
            //             height: 14
            //         },
            //         style: {
            //             fill: '#fff',
            //             lineWidth: 0
            //         }
            //     }, {
            //         type: 'text',
            //         z: 100,
            //         left: 'left',
            //         top: 'middle',
            //         style: {
            //             fill: 'rgba(255, 0, 0, 0.5)',
            //             text: 'RW_Cr7d100k=1',
            //             font: '11px'
            //         }
            //     }]
            // }
            ],
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
                    data: [
                    // { 
                    //     // 30
                    //     name: 'Cr7d100k=' + fig.crp_threshold_2, 
                    //     yAxis: figmker_crrw_trend.get_cr2yv(30)
                    // },
                    // { 
                    //     // 10
                    //     name: 'Cr7d100k=' + fig.crp_threshold_3, 
                    //     yAxis: figmker_crrw_trend.get_cr2yv(10)
                    // }
                    ]
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
                        yAxis: figmker_crrw_trend.get_rw2yv(1),
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
                    color: figmker_crrw_trend.colorscale[2]
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
                    color: figmker_crrw_trend.colorscale[1]
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
                    color: figmker_crrw_trend.colorscale[0]
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
            if (params.componentType == "markLine") {
                return;
            }
            var date_Ymd = params.name;
            console.log('* clicked ' + date_Ymd);
            // var date_mdy = d3.timeFormat('%-m/%-d/%y')(d3.timeParse('%Y-%m-%d')(date_Ymd));
        
            // update the maps by date
            if (jarvis.hasOwnProperty('update_maps_by_date')) {
                jarvis.update_maps_by_date(date_Ymd);
            }
        });

        fig.chart.group = 'trends';
        echarts.connect('trends');

        return fig;
    }
}