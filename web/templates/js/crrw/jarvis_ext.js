Object.assign(jarvis, {

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
});