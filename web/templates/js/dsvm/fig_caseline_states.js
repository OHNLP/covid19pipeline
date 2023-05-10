var fig_caseline_states = {
    plot_id: 'fig_caseline_states',
    plot_type: 'echarts',
    plot_chart: null,
    data_file: 'usstate-data-dict-latest.json',
    
    dates: [],
    items: [],
    series: [],

    load: function() {
        $.get(
            './covid_data/dsvm/' + this.data_file,
            {ver: Math.random()},
            function(data) {
                fig_caseline_states.init(data);
            }, 'json'
        );
    },

    add_series_by_state: function(state) {
        // check if this exist
        for (let i = 0; i < this.series.length; i++) {
            const s = this.series[i];
            if (s.name == state) {
                // oh, this has been added!
                return -1;
            }
        }
        var data = {
            name: state,
            data: this.data.dates.map((v)=>(this.data.data[state][v].test_pos).toFixed(0))
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
        // update chart
        this.plot_chart.setOption(this.option, true);

        // var defaults = ['AZ', 'FL', 'MN'];
        // for (let i = 0; i < defaults.length; i++) {
        //     const state = defaults[i];
        //     this.add_series_by_state(state);
        // }
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
                trigger: 'axis'
            },
            grid: {
                top: 30,
                right: 20,
                bottom: 20,
                left: 50
            },
            legend: {
                data: this.items,
                left: 65,
                right: 5,
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
                name: 'Cum.Cases',
                type: 'log'
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
    plots[fig_caseline_states.plot_id] = fig_caseline_states;
}