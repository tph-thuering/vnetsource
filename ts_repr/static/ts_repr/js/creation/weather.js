// weather_base_url comes in via django and must be set before including this file

$(document).ready(function()
{
    // Save the representative id
    data_to_save['scenario_id'] = $('#scenario_id').val();

    // Initializes description
    $('#weather-select').change();
});

$('#weather-select').change(function()
{
    var option_id = $('#weather-select').val();
    var weather_data_url = weather_base_url + option_id + "/";

    data_to_save['weather_id'] = option_id;

    updateWeatherCharts(weather_data_url);
});

function change_climate(type)
{
    // IDs of each climate type
    var tropical_rainforest = 1;
    var tropical_monsoonal = 2;
    var wet_savannah = 3;
    var dry_savannah = 9;
    var arid = 8;

    switch (type)
    {
        case 'Humid':
            $('#weather-select').val(tropical_rainforest).change();
            break;
        case 'Moist Subhumid':
            $('#weather-select').val(tropical_monsoonal).change();
            break;
        case 'Dry Subhumid':
            $('#weather-select').val(wet_savannah).change();
            break;
        case 'Semi Arid':
            $('#weather-select').val(dry_savannah).change();
            break;
        case 'Arid':
            $('#weather-select').val(arid).change();
            break;
        default:
            alert('Zone ' + type + ' is not valid.');
    }
}