// To use this please look below for the required element ids and add them to your page

function updateDemographicsChart(demographics_data_url, name)
{
    $.ajax(
    {
        type: "GET",
        url: demographics_data_url

    }).success(function(demographics_data)
    {
        var demographics_data_json = JSON.parse(demographics_data);
        var categories = demographics_data_json['categories'];
        var chart_data = demographics_data_json['chart_data'];

        // Create the demographics chart
        $('#demographics-chart').highcharts('Chart',
        {
            chart:
            {
                type: 'column'
            },

            title:
            {
                text: 'Age Distribution'
            },

            xAxis:
            {
                title:
                {
                    text: 'Age - Upperbound'
                },
                categories: categories
            },

            yAxis:
            {
                title:
                {
                    text: 'Percentage of Population'
                }
            },

            series:
            [{
                name: name,
                data: chart_data,
                tooltip:
                {
                    valueDecimals: 2,
                    valueSuffix: ''
                }
            }]
        });
    });
}