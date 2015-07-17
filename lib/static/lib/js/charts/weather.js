// To use this please look below for the required element ids and add them to your page

var chartInfo = {
    disable:
    {
        enabled: false
    },

    chart:
    {
        type: 'column'
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

function updateWeatherCharts(weather_data_url)
{
    $.ajax(
    {
        type: "GET",
        url: weather_data_url

    }).success(function(chart_data)
    {
        var chart_data_json = JSON.parse(chart_data);
        var rainfall_data = chart_data_json['rainfall'];
        var humidity_data = chart_data_json['humidity'];
        var temperature_data = chart_data_json['temperature'];
        var bins = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December' ];
        var monthly_rainfall_data = [];
        var monthly_humidity_data = [];
        var monthly_temperature_data = [];
        var rainfall_totals;
        var humidity_averages;
        var temperature_averages;

        // Some pages make use of descriptions and this will accommodate those pages
        if ('description' in chart_data_json)
        {
            $('#weather-description').text(chart_data_json['description']);
        }

        // Fill rainfall yearly total
        $('#rainfall-yearly-total').html("Total rainfall for year: "
                                         + Math.round(getYearlyTotal(rainfall_data) * 100) / 100 + " mm");

        // Fill humidity yearly average
        $('#humidity-yearly-average').html("Average humidity for year: "
                                           + Math.round(getYearlyAverage(humidity_data) * 100) / 100);

        // Fill temperature yearly average
        $('#temperature-yearly-average').html("Average temperature for year: "
                                              + Math.round(getYearlyAverage(temperature_data) * 100) / 100 + " C");

        // Create the rainfall daily chart
        $('#rainfall-daily-chart').highcharts('StockChart',
        {
            title:
            {
                text: 'Rainfall Daily (mm)'
            },

            rangeSelector: chartInfo['disable'],
            navigator: chartInfo['disable'],
            scrollbar: chartInfo['disable'],
            xAxis: chartInfo['xAxis'],

            tooltip:
            {
                formatter: function()
                {
                    return '<b>' + Highcharts.dateFormat('%B %d', new Date(this.x))
                        + '</b><br/>' + '● ' + Math.round(this.y * 100) / 100 + ' mm';
                }
            },

            yAxis:
            {
                min: 0.0
            },

            series:
            [{
                name: 'Rainfall Daily (mm)',
                data: rainfall_data
            }]
        });

        // Create the humidity daily chart
        $('#humidity-daily-chart').highcharts('StockChart',
        {
            title:
            {
                text: 'Humidity Daily'
            },

            rangeSelector: chartInfo['disable'],
            navigator: chartInfo['disable'],
            scrollbar: chartInfo['disable'],
            xAxis: chartInfo['xAxis'],

            tooltip:
            {
                formatter: function()
                {
                    return '<b>' + Highcharts.dateFormat('%B %d', new Date(this.x))
                        + '</b><br/>' + '● ' + Math.round(this.y * 100) / 100;
                }
            },

            yAxis:
            {
                min: 0.0,
                max: 1.0
            },

            series:
            [{
                name: 'Humidity Daily',
                data: humidity_data
            }]
        });

        // Create the temperature daily chart
        $('#temperature-daily-chart').highcharts('StockChart',
        {
            title:
            {
                text: 'Temperature Daily (C)'
            },

            rangeSelector: chartInfo['disable'],
            navigator: chartInfo['disable'],
            scrollbar: chartInfo['disable'],
            xAxis: chartInfo['xAxis'],

            tooltip:
            {
                formatter: function()
                {
                    return '<b>' + Highcharts.dateFormat('%B %d', new Date(this.x))
                        + '</b><br/>' + '● ' + Math.round(this.y * 100) / 100 + ' C';
                }
            },

            series:
            [{
                name: 'Temperature Daily (C)',
                data: temperature_data
            }]
        });






        rainfall_totals = getMonthlyTotals(rainfall_data);

        for (var i = 0; i < rainfall_totals.length; i++)
        {
            monthly_rainfall_data.push([i, rainfall_totals[i]])
        }

        // Create the rainfall monthly chart
        $('#rainfall-monthly-chart').highcharts('Chart',
        {
            chart: chartInfo['chart'],
            legend: chartInfo['disable'],

            title:
            {
                text: 'Rainfall Monthly Totals (mm)'
            },

            xAxis:
            {
                categories: bins
            },

            yAxis:
            {
                title:
                {
                    text: 'Total Rainfall'
                }
            },

            series:
            [{
                name: 'Rainfall Monthly Totals',
                data: monthly_rainfall_data,
                tooltip:
                {
                    valueDecimals: 2,
                    valueSuffix: ' mm'
                }
            }]
        });


        humidity_averages = getMonthlyAverages(humidity_data);

        for (var j = 0; j < humidity_averages.length; j++)
        {
            monthly_humidity_data.push([j, humidity_averages[j]])
        }

        // Create the humidity monthly chart
        $('#humidity-monthly-chart').highcharts('Chart',
        {
            chart: chartInfo['chart'],
            legend: chartInfo['disable'],

            title:
            {
                text: 'Humidity Monthly Averages'
            },

            xAxis:
            {
                categories: bins
            },

            yAxis:
            {
                title:
                {
                    text: 'Average Humidity'
                }
            },

            series:
            [{
                name: 'Humidity Monthly Averages',
                data: monthly_humidity_data,
                tooltip:
                {
                    valueDecimals: 2,
                    valueSuffix: ''
                }
            }]
        });


        temperature_averages = getMonthlyAverages(temperature_data);

        for (var k = 0; k < temperature_averages.length; k++)
        {
            monthly_temperature_data.push([k, temperature_averages[k]])
        }

        // Create the temperature monthly chart
        $('#temperature-monthly-chart').highcharts('Chart',
        {
            chart: chartInfo['chart'],
            legend: chartInfo['disable'],

            title:
            {
                text: 'Temperature Monthly Averages (C)'
            },

            xAxis:
            {
                categories: bins
            },

            yAxis:
            {
                title:
                {
                    text: 'Average Temperature'
                }
            },

            series:
            [{
                name: 'Temperature Monthly Averages',
                data: monthly_temperature_data,
                tooltip:
                {
                    valueDecimals: 2,
                    valueSuffix: ' C'
                }
            }]
        });
    });
}

function daysInMonth(month)
{
    return new Date(2015, month, 0).getDate();
}

function getMonthlyTotals(data)
{
    var totals = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    var month = 0;
    var count = 0;
    var VALUE = 1;

    for (var i = 0; i < data.length; i++)
    {
        totals[month] += data[i][VALUE];
        count++;

        if (count == daysInMonth(month + 1))
        {
            count = 0;
            month++;
        }
    }

    return totals;
}

function getMonthlyAverages(data)
{
    var averages = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    var month = 0;
    var count = 0;
    var VALUE = 1;
    var sum = 0;

    for (var i = 0; i < data.length; i++)
    {
        sum += data[i][VALUE];
        count++;

        if (count == daysInMonth(month + 1))
        {
            averages[month] = sum / count;
            count = 0;
            sum = 0;
            month++;
        }
    }

    return averages;
}

function getYearlyTotal(data)
{
    var VALUE = 1;
    var sum = 0;

    for (var i = 0; i < data.length; i++)
    {
        sum += data[i][VALUE];
    }

    return sum;
}

function getYearlyAverage(data)
{
    return getYearlyTotal(data) / 365;
}