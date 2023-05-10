var fig_deathline_nations = {
    plot_id: 'fig_deathline_nations',
    plot_type: 'echarts',
    plot_chart: null,
    data_file: 'world-data-latest.json',

    fmt_comma: d3.format(","),
    
    dates: [],
    items: [],
    series: [],

    load: function() {
        $.get(
            './covid_data/dsvm/' + this.data_file,
            {ver: Math.random()},
            function(data) {
                fig_deathline_nations.init(data);

                // use US as default
                fig_deathline_nations.add_series_by_nation('US')

            }, 'json'
        );
    },

    add_series_by_nation: function(nation) {
        // check if this exist
        for (let i = 0; i < this.series.length; i++) {
            const s = this.series[i];
            if (s.name == nation) {
                // oh, this has been added!
                return -1;
            }
        }
        var data = {
            name: nation,
            data: this.data.data[nation].nccs.map(function(v, idx) {
                // return [idx+1, v];
                return [
                    v, 
                    fig_deathline_nations.data.data[nation].dths[idx], 
                    fig_deathline_nations.data.data[nation].dates[idx]
                ];
            })
        };
        this.add_series(data);
    },

    /*
     data is {
         name: 'xxx',
         data: [1,2,3]
     }
     */
    add_series: function(data) {
        data.symbolSize = 2;
        data['type'] = 'line';
        data['smooth'] = true;
        data['lineStyle'] = {
            width: 1,
            type: 'solid'
        };
        // update option
        this.series.push(data);
        this.option.series = this.series;
        this.items.push(data.name);
        this.option.legend.data = this.items;

        // update chart
        this.plot_chart.setOption(this.option, true);
    },

    reset_series: function() {
        // update option
        this.series = [];
        this.items = [];
        this.option.series = this.series;
        this.option.legend.data = this.items;

        // leave only us
        this.add_series_by_nation('US');
    },

    clear_all_series: function() {
        // update option
        this.series = [];
        this.items = [];
        this.option.series = this.series;
        this.option.legend.data = this.items;

        // update chart
        this.plot_chart.setOption(this.option, true);
    },

    init: function(data) {
        this.data = data;
        this.dates = data.dates;
        this.items = [];
        this.series = [];

        this.option = {
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    // console.log(params);
                    var str = '';
                    for (let i = 0; i < params.length; i++) {
                        const param = params[i];
                        str += param.seriesName + ' on ' + param.value[2] + '<br>' +
                            'Total cases: ' + fig_deathline_nations.fmt_comma(param.value[0]) + '<br>' + 
                            'Deaths: ' + fig_deathline_nations.fmt_comma(param.value[1]) + '<br>';
                    }
                    return str;
                }
            },
            grid: {
                top: 30,
                right: 25,
                bottom: 33,
                left: 60
            },
            legend: {
                data: this.items,
                left: 95,
                right: 5,
                itemWidth: 20,
                textStyle: {
                    fontSize: 9
                }
            },
            xAxis: {
                name: 'Total cases',
                type: 'log',
                nameGap: 20,
                nameLocation: 'center'
            },
            yAxis: {
                name: 'Cum.Deaths',
                type: 'log',
                min: 1
            },
            series: this.series
        };

        this.plot_chart = echarts.init(document.getElementById(this.plot_id));
        this.plot_chart.setOption(this.option);
        
        // update the date
        $('#' + this.plot_id + '_last_update').html(data.date);
    },

    resize: function() {
        if (this.plot_chart == null) {

        } else {
            this.plot_chart.resize();
        }
    }
};

// bind this to the global plots object
if (typeof(plots) == 'undefined') {

} else {
    plots[fig_deathline_nations.plot_id] = fig_deathline_nations;
}