var figmker_crrw_1dcal = {
    make_fig: function(plot_id, data, state, fips) { 
        if ($('#' + plot_id).length>0) {
            // have already there
            $( "#" + plot_id ).effect( 'pulsate', {}, 200, null );
            return;
        }
        var fig = {
            plot_id: plot_id,
            color_range: [
                'green',
                'gold',
                'red'
            ],
            state: state,
            fips: fips,
            data: data
        };
        var is_cnty = false;
        if (typeof(fips)=='undefined') {
            is_cnty = false;
        } else {
            is_cnty = true;
        }
        // create the DOM obj for this figure
        var cal_lbl = is_cnty? 
            data.data[fips].name + ', ' + data.data[fips].state : 
            data.state_data.name;
        $('#fig_crrw_calendars').append(
            '<div id="'+fig.plot_id+'" class="fig-crrw-1dcal d-flex justify-content-start align-items-center">'+
            '<div class="crrw-day-label">'+cal_lbl+'</div>' + 
            '</div>'
        );
       
        fig.html = [];
        if (is_cnty) {
            // create county calendar by XX-latest data
            fig.html = data.data[fips].crcs.map(function(v, i) {
                return '<div class="crrw-day crrw-day-'+v+'"></div>';
            });
        } else {
            // create state calendar by US-latest data
            fig.html = data.state_data[state].crcs.map(function(v, i) {
                return '<div class="crrw-day crrw-day-'+v+'"></div>';
            });
        }

        // create this figure
        $('#' + fig.plot_id).append(fig.html.join(''));

        return fig;
    }
};