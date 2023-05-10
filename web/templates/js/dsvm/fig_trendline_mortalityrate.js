var fig_trendline_mortalityrate = {
    plot_id: 'fig_trendline_mortalityrate',
    plot_type: 'echarts',
    plot_chart: null,

    dates: [],
    items: [],
    series: [],


    load: function(data) {
        this.dates = data.dates;
        this.items = data.items;
        this.series = data.series;
        for (let i = 0; i < this.series.length; i++) {
            const series = this.series[i];
            for (let j = 0; j < series.data.length; j++) {
                series.data[j] = series.data[j].toFixed(3);
            }
        }
        fig_trendline_mortalityrate.init();
    },

    init: function() {
        this.option = {
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    // console.log(params);
                    var str = 'Mortality Rate on ' + params[0].name + ': <br>';
                    for (let i = 0; i < params.length; i++) {
                        const param = params[i];
                        str += param.seriesName + ': ' +
                            (param.value * 100).toFixed(1) + '% <br>';
                    }
                    // return '' + params.name + ', ' + params.seriesName + '<br>' +
                        // 'Mortality Rate: ' + (params.value * 100).toFixed(1) + '%';
                    // return '' + params.seriesName + '<br>' + 
                    //     'Mortality Rate: ' +  params.value.y * 100 + '%';
                    return str;
                },
                // axisPointer: {
                //     type: 'cross',
                //     label: {
                //         backgroundColor: '#6a7985'
                //     }
                // }
            },
            legend: {
                data: this.items,
                right: 0,
                itemWidth: 20,
                textStyle: {
                    fontSize: 9
                }
            },
            grid: {
                top: 10,
                right: 10,
                bottom: 20,
                left: 40
            },
            xAxis: {
                type: 'category',
                data: this.dates
            },
            yAxis: {
                type: 'value',
                max: 0.08,
                axisLabel: {
                    formatter: function (val) {
                        return val * 100 + '%';
                    }
                },
            },
            series: this.series
        };

        this.plot_chart = echarts.init(document.getElementById(this.plot_id));
        this.plot_chart.setOption(this.option);
    },

    resize: function() {
        this.plot_chart.resize();
    }
};

// bind this to the global plots object
if (typeof(plots) == 'undefined') {

} else {
    plots[fig_trendline_mortalityrate.plot_id] = fig_trendline_mortalityrate;
}