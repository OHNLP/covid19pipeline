var fig_trendarealine_cases = {
    plot_id: 'fig_trendarealine_cases',
    plot_type: 'echarts',
    plot_chart: null,

    dates: [],
    items: [],
    series: [],

    load: function(data) {
        this.dates = data.dates;
        this.items = data.items;
        this.series = data.series;

        fig_trendarealine_cases.init();
    },

    init: function() {
        this.option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross',
                    label: {
                        backgroundColor: '#6a7985'
                    }
                }
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
                left: 50
            },
            xAxis: {
                type: 'category',
                data: this.dates
            },
            yAxis: {
                type: 'value'
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
    plots[fig_trendarealine_cases.plot_id] = fig_trendarealine_cases;
}