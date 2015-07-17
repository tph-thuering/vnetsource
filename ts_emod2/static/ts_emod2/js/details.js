// weather_data_url, demographics_data_url, and copy_scenario_url come in via django and must be set before including this file

$(document).ready(function()
{
    updateWeatherCharts(weather_data_url);
    //updateDemographicsChart(demographics_data_url);
});

function copy()
{
    var data = {};

    data['include_output'] = false;
    data['should_link_experiment'] = false;
    data['should_link_simulation'] = false;
    data['should_link_simulation_files'] = false;

    $.ajax(
    {
        data: data,
        type: "POST",
        url: copy_scenario_url,

        success: function(goto_url)
        {
            window.location = goto_url;
        }
    });
}