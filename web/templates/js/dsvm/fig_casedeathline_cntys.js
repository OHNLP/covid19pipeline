var fig_casedeathline_cntys = {
    plot_id: 'fig_casedeathline_cntys',
    plot_type: 'echarts',
    plot_chart: null,
    
    dates: [],
    items: [],
    series: [],

    colors: ['#c23531','#2f4554', '#61a0a8', '#d48265', '#91c7ae','#749f83',  '#ca8622', '#bda29a','#6e7074', '#546570', '#c4ccd3'],

    data_file: 'uscounty-data-latest.json',

    load: function() {
        
        $.get(
            './covid_data/dsvm/' + this.data_file,
            {ver: Math.random()},
            function(data) {
                fig_casedeathline_cntys.init(data);
                // use US as default
                fig_casedeathline_cntys.reset_series();
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
            data: cnty.nccs,
            itemStyle: {
                color: this.colors[Math.floor(this.series.length/2) % 10]
            },
            lineStyle: {
                width: 1,
                color: this.colors[Math.floor(this.series.length/2) % 10],
                type: 'solid'
            }
        };
        this.add_series(data);

        var cdrs = cnty.dths.map((v, i)=> (v/cnty.nccs[i] * 100).toFixed(1));
        var sdrs = cnty.sdrs.map((v)=>(v*100).toFixed(1));
        var data2 = {
            name: cnty.countyName + ',' + cnty.state + ' Death Rate',
            yAxisIndex: 1,
            data: cdrs,
            symbol: 'rect',
            itemStyle: {
                color: this.colors[Math.floor(this.series.length/2) % 10]
            },
            lineStyle: {
                width: 1,
                color: this.colors[Math.floor(this.series.length/2) % 10],
                type: 'dotted'
            }
        };
        this.add_series(data2);
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
                top: 40,
                right: 50,
                bottom: 20,
                left: 50
            },
            legend: {
                data: this.items,
                left: 85,
                right: 70,
                itemWidth: 20,
                textStyle: {
                    fontSize: 9
                }
            },
            xAxis: {
                type: 'category',
                data: this.dates
            },
            yAxis: [{
                name: 'Cum.Cases',
                type: 'log',
                min: 1
            }, {
                name: 'Cum. Death Rate',
                type: 'value',
                splitLine: {
                    show: false
                },
                axisLabel: {
                    formatter: function (val) {
                        return val + '%';
                    }
                },
                max: 20
            }],
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
    plots[fig_casedeathline_cntys.plot_id] = fig_casedeathline_cntys;
}