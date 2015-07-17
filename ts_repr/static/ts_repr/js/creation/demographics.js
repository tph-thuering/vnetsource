// demographics_data_url comes in via django and must be set before including this file

var is_first_load = true;

$(document).ready(function()
{
    // Save the scenario id
    data_to_save['scenario_id'] = $('#scenario_id').val();

    // Initializes description
    $('#demographics-select').change();
});

$('#demographics-select').change(function()
{
    var option_id = $('#demographics-select').val();
    var the_url = demographics_data_url + option_id + "/";
    var name = $('#demographics-select').find(":selected").text().trim();

    $.ajax(
    {
        type: "GET",
        url: the_url

    }).success(function(demographics_data)
    {
        var demographics_data_json = JSON.parse(demographics_data);
        var categories = demographics_data_json['categories'];
        var chart_data = demographics_data_json['chart_data'];
        var description = demographics_data_json['description'];

        $('#demographics-description').html(description);

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

        $('#form-is-valid').val('true');
    });

    data_to_save['demographics_id'] = option_id;

    if (!is_first_load)
    {
        $('.save-button').attr('style', '');
    }

    is_first_load = false;
});