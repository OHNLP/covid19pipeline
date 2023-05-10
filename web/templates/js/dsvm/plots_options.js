var plots_options = {
    selected: 'doubling_analysis_result',
    filetypes: {
        'doubling_analysis_result': {
            type: 'doubling_analysis_result',
            desc: '<b>Doubling Time Analysis</b> (e.g., doubling_xxxx_3_30.xlsx, for plotting the animation lines)',
            tags: [{
                tag: 'countylevel',
                desc: '<b>County Level</b> (e.g., doubling_counties_3_30.xlsx, for plotting the heatmap of doubling time of counties)'
            }, {
                tag: 'mayosys',
                desc: '<b>Mayo Related</b> (e.g., doubling_mayosys_03_31.xls'
            }, {
                tag: 'word',
                desc: '<b>World Countries</b> (e.g., doubling_world_03_31.xls'
            }]
        },
        'trendline_past7d': {
            type: 'trendline_past7d',
            desc: '<b>Trends lines of cases vs past7day cases</b> (e.g., trpast7d_xxxx_3_30.xlsx, for plotting the heatmaps)',
            tags: [{
                tag: 'countylevel',
                desc: '<b>County Level</b> Trend Lines of Total vs Past 7 days</b>'
            }]
        }
    }
};