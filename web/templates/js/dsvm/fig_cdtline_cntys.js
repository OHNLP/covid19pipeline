var fig_cdtline_cntys = {
    plot_id: 'fig_cdtline_cntys',
    plot_type: 'echarts',
    plot_chart: null,
    
    dates: [],
    items: [],
    series: [],

    data_file: 'uscounty-data-latest.json',

    load: function() {
        
        $.get(
            './covid_data/dsvm/' + this.data_file,
            {ver: Math.random()},
            function(data) {
                fig_cdtline_cntys.init(data);
                // use US as default
                fig_cdtline_cntys.reset_series();
            }, 'json'
        );
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

    add_series_by_FIPS: function(FIPS) {
        var cnty = this.data_dict.get(FIPS);
        var series_name = cnty.countyName + ',' + cnty.state;
        // check if this exist
        for (let i = 0; i < this.series.length; i++) {
            const s = this.series[i];
            if (s.name == series_name) {
                // oh, this has been added!
                return -1;
            }
        }
        var data = {
            name: series_name,
            data: cnty.cdts.map((v)=>v.toFixed(1))
        };
        this.add_series(data);
    },

    reset_series: function() {
        // update option
        this.series = [];
        this.items = [];
        this.option.series = this.series;
        this.option.legend.data = this.items;
        this.plot_chart.setOption(this.option, true);
        
        // var defaults = [
        //     ['Maricopa,AZ', '04013'],
        //     ['Duval,FL', '12031'],
        //     ['Olmsted,MN', '27109'],
        // ];
        // for (let i = 0; i < defaults.length; i++) {
        //     const c = defaults[i];
        //     this.add_series_by_FIPS(c[1]);
        // }
    },

    convert_data_to_dict: function() {
        this.data_dict = d3.map();
        for (const FIPS in this.data.data) {
            if (this.data.data.hasOwnProperty(FIPS)) {
                const cnty = this.data.data[FIPS];
                this.data_dict.set(FIPS, cnty);
            }
        }
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
        this.convert_data_to_dict();

        this.dates = data.dates;
        this.items = [];
        this.series = [];

        this.option = {
            tooltip: {
                trigger: 'axis'
            },
            grid: {
                top: 35,
                right: 10,
                bottom: 20,
                left: 50
            },
            legend: {
                data: this.items,
                left: 75,
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
                max: 110
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
    plots[fig_cdtline_cntys.plot_id] = fig_cdtline_cntys;
}