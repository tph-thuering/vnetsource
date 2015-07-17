// weather_data_url comes in via django and must be set before including this file

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
    $('#weather-select').change();
});

$('#weather-select').change(function()
{
    var option_id = $(this).val();
    var the_url = weather_data_url + option_id + "/";

    $.ajax(
    {
        type: "GET",
        url: the_url

    }).success(function(weather_data)
    {
        var weather_data_json = JSON.parse(weather_data);

        $('#name').val(weather_data_json['name']);
        $('#description').html(weather_data_json['description']);

        if (weather_data_json == -1)
        {
            $('#is_active').prop("checked", true);
        }
        else
        {

            if (weather_data_json['is_active'] == true)
            {
                $('#is_active').prop("checked", true);
            }
            else
            {
                $('#is_active').prop("checked", false);
            }
        }

        $('#rainfall_file_location').val(weather_data_json['file_locations']['rainfall']);
        $('#humidity_file_location').val(weather_data_json['file_locations']['humidity']);
        $('#temperature_file_location').val(weather_data_json['file_locations']['temperature']);

        updateCharts(weather_data_json);
    });

    $('#form-is-valid').val('true');
    $('#weather_id').val(option_id);
});

function updateCharts(weather_data_json)
{
    var rainfall_data = weather_data_json['rainfall'];
    var humidity_data = weather_data_json['humidity'];
    var temperature_data = weather_data_json['temperature'];

    // Create the rainfall chart
    $('#rainfall-chart').highcharts('StockChart',
    {
        title:
        {
            text: 'Rainfall (mm)'
        },

        rangeSelector: chartInfo['disable'],
        navigator: chartInfo['disable'],
        scrollbar: chartInfo['disable'],
        xAxis: chartInfo['xAxis'],

        yAxis:
        {
            min: 0.0
        },

        series:
        [{
            name: 'Rainfall',
            data: rainfall_data,
            tooltip:
            {
                valueDecimals: 2,
                valueSuffix: 'mm'
            }
        }]
    });

    // Create the rainfall chart
    $('#humidity-chart').highcharts('StockChart',
    {
        title:
        {
            text: 'Humidity'
        },

        rangeSelector: chartInfo['disable'],
        navigator: chartInfo['disable'],
        scrollbar: chartInfo['disable'],
        xAxis: chartInfo['xAxis'],

        yAxis:
        {
            min: 0.0,
            max: 1.0
        },

        series:
        [{
            name: 'Humidity',
            data: humidity_data,
            tooltip:
            {
                valueDecimals: 2,
                valueSuffix: ''
            }
        }]
    });

    // Create the rainfall chart
    $('#temperature-chart').highcharts('StockChart',
    {
        title:
        {
            text: 'Temperature (C)'
        },

        rangeSelector: chartInfo['disable'],
        navigator: chartInfo['disable'],
        scrollbar: chartInfo['disable'],
        xAxis: chartInfo['xAxis'],

        series:
        [{
            name: 'Temperature',
            data: temperature_data,
            tooltip:
            {
                valueDecimals: 2,
                valueSuffix: 'C'
            }
        }]
    });
}