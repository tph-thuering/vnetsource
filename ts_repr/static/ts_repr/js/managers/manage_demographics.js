// demographics_data_url comes in via django and must be set before including this file

var chartInfo = {
    disable:
    {
        enabled: false
    },

    xAxis:
    {
        dateTimeLabelFormats:
        {
            month: '%b'
        },
        // 30 days * 24 hours in a day * 60 minutes in an hour * 60 seconds in a minute * 1000 milliseconds in a second
        tickInterval: 30 * 24 * 60 * 60 * 1000
    }
};

$(document).ready(function()
{
    $('#demographics-select').change();
});

$('#demographics-select').change(function()
{
    var option_id = $(this).val();
    var the_url = demographics_data_url + option_id + "/";
    var i;

    $.ajax(
    {
        type: "GET",
        url: the_url

    }).success(function(demographics_data)
    {
        var demographics_data_json = JSON.parse(demographics_data);
        var types = demographics_data_json['types'];
        var i;
        var type_select_option;
        var type_select_html = "";

        $('#name').val(demographics_data_json['name']);

        // If there was stuff actually sent back this will not be -1
        if (demographics_data_json != -1)
        {
            for (i = 0; i < types.length; i++)
            {
                type_select_option = "<option value='" + types[i] + "'";

                if (types[i] === demographics_data_json['type'])
                {
                    type_select_option += " selected";
                }

                type_select_option += ">" + types[i] + "</option>";

                type_select_html += type_select_option;
            }

             $('#type').html(type_select_html);
        }

        $('#description').html(demographics_data_json['description']);

        if (demographics_data_json == -1)
        {
            $('#is_active').prop("checked", true);
        }
        else
        {

            if (demographics_data_json['is_active'] == true)
            {
                $('#is_active').prop("checked", true);
            }
            else
            {
                $('#is_active').prop("checked", false);
            }
        }

        $('#demographics_file_location').val(demographics_data_json['file_location']);

        updateCharts(demographics_data_json);
    });

    $('#form-is-valid').val('true');
    $('#demographics_id').val(option_id).change();
});

function updateCharts(demographics_data_json)
{
    var name = $('#demographics-select').find(":selected").text().trim();
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
}