var fig_trendline_cdt = {
    plot_id: 'fig_trendline_cdt',
    plot_type: 'echarts',
    plot_chart: null,
    max_cdt: 100,
    
    dates: [],
    items: [],
    series: [],

    load: function(data) {
        this.init(data);
    },

    init: function(data) {
        this.dates = data.dates;
        this.items = data.items;
        this.series = data.series;

        for (let i = 0; i < this.series.length; i++) {
            const s = this.series[i];
            for (let j = 0; j < s.data.length; j++) {
                s.data[j] = s.data[j].toFixed(1);
            }
        }

        this.option = {
            tooltip: {
                trigger: 'axis',
                // axisPointer: {
                //     type: 'cross',
                //     label: {
                //         backgroundColor: '#6a7985'
                //     }
                // }
            },
            grid: {
                top: 30,
                right: 10,
                bottom: 20,
                left: 30
            },
            legend: {
                data: this.items,
                right: 0,
                itemWidth: 20,
                textStyle: {
                    fontSize: 9
                }
            },
            xAxis: {
                type: 'category',
                data: this.dates
            },
            yAxis: {
                name: 'Days',
                type: 'value',
                max: this.max_cdt + 10
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
    plots[fig_trendline_cdt.plot_id] = fig_trendline_cdt;
}