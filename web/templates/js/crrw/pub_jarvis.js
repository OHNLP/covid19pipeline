var jarvis = {
    plots: {},
    us_data: {},
    state_data: {},
    world_data: {},
    base_data_url: './covid_data/v2/',

    // for the auto play
    proc_play: null,
    date_idx: 0,
    frame_duration: 500,
    enabled_color_filter: false,

    // all of the indicators
    indicators: {
        tcps: { name: 'Total Cases / Population', fmt: function(v) { return (v*100).toFixed(2) + '%'; } },
        nccs: { name: 'Total Cases', fmt: function(v) { return v; } },
        dncs: { name: 'Daily Cases', fmt: function(v) { return v; } },
        d7vs: { name: '7-day Average Cases', fmt: function(v) { return v; } },
        npps: { name: 'Total Cases per 100k', fmt: function(v) { return v; } },
        dpps: { name: 'Daily Cases per 100k', fmt: function(v) { return v; } },
        d7ps: { name: '7-day Average Cases per 100k', fmt: function(v) { return v; } },
        tprs: { name: 'Test Positive Rate', fmt: function(v) { return v; } },
        ttrs: { name: 'Total Tests', fmt: function(v) { return v; } },
        tpts: { name: 'Total Positive Tests', fmt: function(v) { return v; } },
        t7rs: { name: '7-day Average Test Positive Rate', fmt: function(v) { return v; } },
        dths: { name: 'Deaths', fmt: function(v) { return v; } },
        dtrs: { name: 'Death Rate', fmt: function(v) { return v==0? 'NA' : (v*100).toFixed(2) + '%'; } },
        cdts: { name: '4-day Smoothed Case Doubling Time', fmt: function(v) { return v.toFixed(0) + ' days'; } },

        crps: { name: 'Cr7d100k Case Rate', fmt: function(v) { return v; } },
        crts: { name: 'RW_Cr7d100k Case Ratio', fmt: function(v) { return v; } },
        crcs: { name: 'CrRW Status', fmt: function(v) { return {2:"R", 1:'Y', 0:'G'}[v]; } },

        pvis: { name: 'Pandemic Vulnerability Index', fmt: function(v) { return v; } },
        fvcs: { name: 'Fully Vaccinated People', fmt: function(v) { return v==0? 'NA' : jarvis.fmt_comma(v); } },
        fvps: { name: 'Fully Vaccinated Percentage', fmt: function(v) { return v==0? 'NA' : (v*100).toFixed(2) + '%'; } },
        vacs: { name: 'Vaccinated Administered', fmt: function(v) { return v==0? 'NA' : jarvis.fmt_comma(v); } },
        vaps: { name: 'Vaccinated Administered Percentage', fmt: function(v) { return v==0? 'NA' : (v*100).toFixed(2) + '%'; } },
    },

    get_state_data_file_url: function (state) {
        return this.base_data_url + state + '-history.json';
    },

    toggle_cbs_color: function() {
        this.enabled_color_filter = !this.enabled_color_filter;

        if (this.enabled_color_filter) {
            var green_alt = '#4575b4';
            var yellow_alt = '#fee090';
            var red_alt = '#d73027';
            var crc_schema_alt_ployly = [ [0, green_alt], [0.5, yellow_alt], [1, red_alt] ];
            var crc_schema_alt_echart = [ green_alt, yellow_alt, red_alt];
            $('#ico_color_filter').html('<i class="fa fa-toggle-on"></i>');
        } else {
            var green_alt = 'green';
            var yellow_alt = 'gold';
            var red_alt = 'red';
            var crc_schema_alt_ployly = [ [0, green_alt], [0.5, yellow_alt], [1, red_alt] ];
            var crc_schema_alt_echart = [ green_alt, yellow_alt, red_alt];
            $('#ico_color_filter').html('<i class="fa fa-toggle-off"></i>');
        }

        // update world map
        fig_crrw_worldmap.colorscale.crcs.schema = crc_schema_alt_ployly;
        fig_crrw_worldmap.update(fig_crrw_worldmap.data);

        // update us map
        fig_crrw_usmap.colorscale.crcs.schema = crc_schema_alt_ployly;
        fig_crrw_usmap.update(fig_crrw_usmap.data);
        
        // update county map
        fig_crrw_stmap.colorscale.crcs.schema = crc_schema_alt_ployly;
        fig_crrw_stmap.update(fig_crrw_stmap.data);

        // update the calendar
        figmker_crrw_calendar.colorscale = crc_schema_alt_echart;
        window.fig_crrw_calendar = figmker_crrw_calendar.reset_and_make_fig();  

        // update the trend
        figmker_crrw_trend.colorscale = crc_schema_alt_echart;
        this.reset_fig_crrw_trends();
    },

    init: function() {
        // init the toast
        $('.toast').toast({
            delay: 10000
        });

        // bind the fips to states
        for (var a in this.states) {
            var fips = this.states[a].fips;
            this.states[fips] = this.states[a];
        }

        // bind enter
        $('#input_fips').on('keypress', function(event) {
            if (event.which == 13) {
                jarvis.add_trend();
            }
        });

        // sortable
        $('#fig_crrw_trends').sortable({
            handle: '.crrw-trend-label',
            placeholder: "ui-state-highlight"
        });
        $('#fig_crrw_trends').disableSelection();

        // init the components
        fig_crrw_worldmap.init();
        fig_crrw_usmap.init();
        fig_crrw_stmap.init();

        // bind resize event
        $(window).resize(function() {
            jarvis.resize();
        });

        $.get(
            this.base_data_url + 'WORLD-history.json',
            { ver: Math.random() },
            function(data) {
                jarvis.world_data = data;
                // update the date_idx
                jarvis.date_idx = data.dates.length - 1;

                // update the map
                fig_crrw_worldmap.update(data);

                // init the calendar by USA cases
                jarvis.init_calendar('USA');
                // jarvis.show_country('USA');
                // fig_crrw_worldmap.show_detail('USA');

                jarvis.ssmsg('Finished initialization.')
                setTimeout('jarvis.ssclose();', 500);
            }, 'json'
        );

        $.get(
            this.get_state_data_file_url('US'),
            { ver: Math.random() },
            function(data) {
                jarvis.us_data = data;
                fig_crrw_usmap.update(data);

                jarvis.show_state('MN');
                // fig_crrw_usmap.show_detail('MN');
                
                jarvis.ssmsg('Finished initialization.')
                setTimeout('jarvis.ssclose();', 500);
            }, 'json'
        );
    },

    init_calendar: function(country) {
        if (typeof(country) == 'undefined') {
            country = 'USA';
        }
        // then make a figure
        if (!window.hasOwnProperty('figmker_crrw_calendar')) {
            return;
        }
        window.fig_crrw_calendar = figmker_crrw_calendar.clear_and_make_fig(
            'fig_crrw_calendar',
            jarvis.world_data,
            country,
            null,
            null,
            false
        );
    },

    resize: function() {

        for (const plot_name in jarvis.plots) {
            if (Object.hasOwnProperty.call(jarvis.plots, plot_name)) {
                var plot = jarvis.plots[plot_name];
                
                // resize
                plot.chart.resize();
            }
        }
    },

    show_country: function(country) {
        this.show_country_trend(country);
    },

    show_country_trend: function(country) {
        console.log('* show country trend: ' + country);
        var plot_id = 'fig_crrw_trend_' + country;
        var fig = figmker_crrw_trend.make_fig(
            plot_id, 
            this.world_data, 
            country,
            'world'
        );
        if (fig == null) {
            return;
        } else {
            this.plots[plot_id] = fig;
        }

    },

    show_state: function(state) {
        console.log('* show state: ' + state);
        if (this.state_data.hasOwnProperty(state)) {
            fig_crrw_stmap.update(this.state_data[state]);
            this.show_state_map(state);
            this.show_state_trend(state);
            return;
        }
        // get data if not exists
        $.get(
            this.get_state_data_file_url(state),
            { ver: Math.random() },
            function(data) {
                jarvis.state_data[data.state] = data;
                jarvis.show_state(data.state);
            }, 'json'
        );

    },

    show_state_map: function(state) {
        console.log('* show state map: ' + state);
        fig_crrw_stmap.update(jarvis.state_data[state]);
    },

    show_state_trend: function(state) {
        console.log('* show state trend: ' + state);
        var plot_id = 'fig_crrw_trend_' + state;
        var fig = figmker_crrw_trend.make_fig(
            plot_id, 
            this.us_data, 
            state
        );
        if (fig == null) {
            return;
        } else {
            this.plots[plot_id] = fig;
        }
    },

    show_county: function(fips) {
        this.show_county_trend(fips);
    },

    show_county_trend: function(fips) {
        console.log('* show county trend: ' + fips);
        var state_fips = fips.substring(0, 2);
        var state_abbr = this.states[state_fips].abbr;

        if (this.state_data.hasOwnProperty(state_abbr)) {
            this._show_county_trend(state_abbr, fips);
        } else {
            this.show_state_map(state_abbr);
        }
    },

    _show_county_trend: function(state_abbr, fips) {
        var plot_id = '';
        var fig = null;

        // plot_id = 'fig_crrw_calendar_' + fips;
        // fig = figmker_crrw_calendar.make_fig(
        //     plot_id, this.state_data, this.state_data.state, fips);
        // this.plots[plot_id] = fig;

        // plot_id = 'fig_crrw_calendar_' + fips;
        // fig = figmker_crrw_1dcal.make_fig(
        //     plot_id, this.state_data, this.state_data.state, fips);
        // this.plots[plot_id] = fig;
        
        plot_id = 'fig_crrw_trend_' + fips;
        fig = figmker_crrw_trend.make_fig(
            plot_id, 
            this.state_data[state_abbr], 
            this.state_data[state_abbr].state, 
            fips);
        if (fig == null) {
            return;
        } else {
            this.plots[plot_id] = fig;
        }
    },

    add_trend: function() {
        var fips = $('#input_fips').val();
        fips = fips.trim();
        fips = fips.toUpperCase();
        if (fips.length < 2 || fips.length > 5) {
            jarvis.msg('The input must be state abbr or FIPS code.', 'gold');
            return;
        }
        if (this.states.hasOwnProperty(fips)) {
            // ok, I guess it's a state abbr
            var state = fips;
            this.show_state_map(state);
            this.show_state_trend(state);
        } else {
            if (fips.length == 4) {
                fips = '0' + fips;
            }
            $('#input_fips').val(fips);
            this.show_county_trend(fips);
        }
    },

    remove_trend: function(plot_id) {
        $('#' + plot_id).remove();
    },

    update_by_date: function(date) {
        console.log('* jarvis update by date ' + date);

        // update the index first
        this.date_idx = this.world_data.dates.indexOf(date);

        // then update the calendar
        if (window.hasOwnProperty('fig_crrw_calendar')) {
            window.fig_crrw_calendar.update_by_date(date);
        }

        // last, update the map
        this.update_maps_by_date(date);
    },

    update_maps_by_date: function(date) {
        fig_crrw_worldmap.update_by_date(date);
        fig_crrw_usmap.update_by_date(date);
        fig_crrw_stmap.update_by_date(date);
    },

    auto_play: function() {
        if (this.date_idx >= this.world_data.dates.length - 1) {
            this.date_idx = 0;
            this.stop();
        } else {
            this.date_idx += 1;
            var next_date = this.world_data.dates[this.date_idx];
            this.update_by_date(next_date);
        }
    },

    stop: function() {
        if (this.proc_play == null) {
    
        } else {
            clearInterval(this.proc_play);
            this.proc_play = null;
        }
    },

    play: function() {
        if (this.proc_play == null) {
            if (this.date_idx == this.world_data.dates.length - 1) {
                this.date_idx = -1;
            }
            this.proc_play = setInterval('jarvis.auto_play();', this.frame_duration);
        } else {
    
        } 
    },

    reset_fig_crrw_trends: function() {
        $('#fig_crrw_trends').html('');
    },

    ssmsg: function(msg) {
        $('#ss-msg').html(msg);
    },

    ssclose: function() {
        $('#start-screen').hide();
    },

    make_screenshot: function() {
        html2canvas(document.body).then(function(canvas) {
            document.body.appendChild(canvas);
        });
    },

    states: {
        AL: { fips: '01', abbr: 'AL', name: 'Alabama' }, 
        AK: { fips: '02', abbr: 'AK', name: 'Alaska' }, 
        AS: { fips: '60', abbr: 'AS', name: 'American Samoa' },
        AZ: { fips: '04', abbr: 'AZ', name: 'Arizona' }, 
        AR: { fips: '05', abbr: 'AR', name: 'Arkansas' }, 
        CA: { fips: '06', abbr: 'CA', name: 'California' }, 
        CO: { fips: '08', abbr: 'CO', name: 'Colorado' }, 
        CT: { fips: '09', abbr: 'CT', name: 'Connecticut' }, 
        DE: { fips: '08', abbr: 'DE', name: 'Delaware' }, 
        FL: { fips: '12', abbr: 'FL', name: 'Florida' }, 
        GA: { fips: '13', abbr: 'GA', name: 'Georgia' }, 
        GU: { fips: '66', abbr: 'GU', name: 'Guam' },
        HI: { fips: '15', abbr: 'HI', name: 'Hawaii' }, 
        ID: { fips: '16', abbr: 'ID', name: 'Idaho' }, 
        IL: { fips: '17', abbr: 'IL', name: 'Illinois' }, 
        IN: { fips: '18', abbr: 'IN', name: 'Indiana' }, 
        IA: { fips: '19', abbr: 'IA', name: 'Iowa' }, 
        KS: { fips: '20', abbr: 'KS', name: 'Kansas' }, 
        KY: { fips: '21', abbr: 'KY', name: 'Kentucky' }, 
        LA: { fips: '22', abbr: 'LA', name: 'Louisiana' }, 
        ME: { fips: '23', abbr: 'ME', name: 'Maine' }, 
        MD: { fips: '24', abbr: 'MD', name: 'Maryland' }, 
        MA: { fips: '25', abbr: 'MA', name: 'Massachusetts' }, 
        MI: { fips: '26', abbr: 'MI', name: 'Michigan' }, 
        MN: { fips: '27', abbr: 'MN', name: 'Minnesota' }, 
        MS: { fips: '28', abbr: 'MS', name: 'Mississippi' }, 
        MO: { fips: '29', abbr: 'MO', name: 'Missouri' }, 
        MT: { fips: '39', abbr: 'MT', name: 'Montana' }, 
        NE: { fips: '31', abbr: 'NE', name: 'Nebraska' }, 
        NV: { fips: '32', abbr: 'NV', name: 'Nevada' }, 
        NH: { fips: '33', abbr: 'NH', name: 'New Hampshire' }, 
        NJ: { fips: '34', abbr: 'NJ', name: 'New Jersey' }, 
        NM: { fips: '35', abbr: 'NM', name: 'New Mexico' }, 
        NY: { fips: '36', abbr: 'NY', name: 'New York' }, 
        NC: { fips: '37', abbr: 'NC', name: 'North Carolina' }, 
        ND: { fips: '38', abbr: 'ND', name: 'North Dakota' }, 
        MP: { fips: '69', abbr: 'MP', name: 'Northern Mariana Islands' }, 
        OH: { fips: '39', abbr: 'OH', name: 'Ohio' }, 
        OK: { fips: '40', abbr: 'OK', name: 'Oklahoma' }, 
        OR: { fips: '41', abbr: 'OR', name: 'Oregon' }, 
        PA: { fips: '42', abbr: 'PA', name: 'Pennsylvania' }, 
        PR: { fips: '72', abbr: 'PR', name: 'Puerto Rico' }, 
        RI: { fips: '44', abbr: 'RI', name: 'Rhode Island' }, 
        SC: { fips: '45', abbr: 'SC', name: 'South Carolina' }, 
        SD: { fips: '46', abbr: 'SD', name: 'South Dakota' }, 
        TN: { fips: '47', abbr: 'TN', name: 'Tennessee' }, 
        TX: { fips: '48', abbr: 'TX', name: 'Texas' }, 
        VI: { fips: '78', abbr: 'VI', name: 'U.S. Virgin Islands' },
        UT: { fips: '49', abbr: 'UT', name: 'Utah' }, 
        VT: { fips: '50', abbr: 'VT', name: 'Vermont' }, 
        VA: { fips: '51', abbr: 'VA', name: 'Virginia' }, 
        WA: { fips: '53', abbr: 'WA', name: 'Washington' }, 
        DC: { fips: '11', abbr: 'DC', name: 'Washington, D.C.' }, 
        WV: { fips: '54', abbr: 'WV', name: 'West Virginia' }, 
        WI: { fips: '55', abbr: 'WI', name: 'Wisconsin' }, 
        WY: { fips: '56', abbr: 'WY', name: 'Wyoming' }
    },

    msg: function(s, color) {
        if (typeof(color)=='undefined') {
            color = 'blue';
        }
        $('#toast_rect').attr('fill', color);
        $('#toast_body').html(s);
        $('#toast').toast('show')
    },

    modal: function(ti, ct) {
        $('#modal-title').html(ti);
        $('#modal-body').html(ct);
        $('#modal').modal('show');
    },

    modal_dncs: function() {
        this.modal(
            'Daily New Cases',
            "<p>When the data source doesn't report latest new cases in a region, or the latest data are not updated, it will show <b>NA</b>.</p>"
        );
    },

    ind2txt: function(ind) {
        return this.indicators[ind];
    },

    val2txt: function(ind, val) {
        if (ind == 'dncs') {
            if (val == 0) {
                return 'NA <a href="javascript:void(0);" onclick="jarvis.modal_dncs()" title="No new cases reported or the latest data not available" class="q-circle"><i class="far fa-question-circle"></i></a>';
            }
            return this.fmt_comma(val);

        } if (ind == 'tprs' || ind == 't7rs') {
            return (val*100).toFixed(2) + '%';

        } else {
            return val;
        }
    },

    is_mobile: function() {
        var w = $(window).width();
        if (w < 800) {
            return true;
        } else {
            return false;
        }

    },

    fmt_comma: d3.format(",")
};