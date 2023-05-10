
var vue_mayomort = {
    plot_id: 'vue_mayomort',
    plot_type: 'vue',
    vpp_id: '#vue_mayomort',
    vpp: null,
    data: null,
    data_file: 'mayo_regions_mort.json',

    load: function() {
        $.get(
            './covid_data/dsvm/' + this.data_file,
            {ver: Math.random()},
            function(data) {
                vue_mayomort.data = data;
                vue_mayomort.init();
            }, 'json'
        );
    },

    init: function() {
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
                    if (v<0) { return 'green'; }
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
        fig_trendline_mortalityrate.load({
            dates: this.data.dates,
            items: items,
            series: series
        });
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
    plots[vue_mayomort.plot_id] = vue_mayomort;
}
