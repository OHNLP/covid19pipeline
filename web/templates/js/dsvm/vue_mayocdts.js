var vue_mayocdts = {
    plot_id: 'vue_mayocdts',
    plot_type: 'vue',
    vpp_id: '#vue_mayocdts',
    vpp: null,
    data: null,
    data_file: 'mayo_regions_cdts.json',

    load: function() {
        $.get(
            './covid_data/dsvm/' + this.data_file,
            {ver: Math.random()},
            function(data) {
                vue_mayocdts.init(data);
            }, 'json'
        );
    },

    init: function(data) {
        this.data = data;
        // init the vue
        this.vpp = new Vue({
            el: this.vpp_id,
            data: this.data,
            methods: {
                get_sign: function(v) {
                    if (v>0) {
                        return '+';
                    } else if (v<0) {
                        return ''
                    } else {
                        return '';
                    }
                },

                get_color: function(v) {
                    if (v>=0) { return 'green'; }
                    else { return 'red'; }
                },

                reg2disp: function(reg) {
                    if (reg == 'RST') {
                        return 'RST/SEMN';
                    }
                    return reg;
                }
            }
        });
        // init the chart
        var series = [];
        var items = [];
        for (let i = 0; i < this.data.regions.length; i++) {
            const region = this.data.regions[i];
            series.push({
                name: this.reg2disp(region),
                data: this.data.values[region].history,
                type: 'line',
                smooth: true
            });
            items.push(this.reg2disp(region));
        }
        fig_trendline_cdt.init({
            dates: this.data.dates,
            items: items,
            series: series
        })
    },

    reg2disp: function(reg) {
        if (reg == 'RST') {
            return 'RST/SEMN';
        }
        return reg;
    }
};
// bind this to the global plots object
if (typeof(plots) == 'undefined') {

} else {
    plots[vue_mayocdts.plot_id] = vue_mayocdts;
}