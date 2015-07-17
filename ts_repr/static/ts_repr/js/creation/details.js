// weather_base_url, demographics_base_url, and  details_save_url come in via django and must be set before including this file

$(document).ready(function()
{
    updateWeatherCharts(weather_base_url + $('#weather-id').val() + "/");
    updateDemographicsChart(demographics_base_url + $('#demographics-id').val() + "/", $('#demographics-name').val());

    // Save the initial data (this variable is only for save_scenario_name())
    data_to_save['scenario_id'] = $('#scenario_id').val();
    data_to_save['scenario_name'] = $('#scenario_name').val();

    $('form').submit(function()
    {
        $('#scenario_name').appendTo(this);
    });
});

$('#scenario-name-input').change(function()
{
    var scenario_name = $(this).val();

    data_to_save['scenario_name'] = scenario_name;
    $('#scenario_name').val(scenario_name);
});

function save_scenario_name()
{
    $.ajax(
    {
        data: JSON.stringify(data_to_save),
        type: "POST",
        url: details_save_url
    }).success(function()
    {
        location.reload();
    });
}

function copy()
{
    alert("This has not been implemented yet.")
}