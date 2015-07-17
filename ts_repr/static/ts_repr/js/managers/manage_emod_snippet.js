// emod_snippet_data_url comes in via django and must be set before including this file

$(document).ready(function()
{
    $('#emod-snippet-select').change();
});

$('#emod-snippet-select').change(function()
{
    var option_id = $(this).val();
    var the_url = emod_snippet_data_url + option_id + "/";

    $.ajax(
    {
        type: "GET",
        url: the_url

    }).success(function(emod_snippet_data)
    {
        $('#name').val(emod_snippet_data['name_for_config_file']);
        $('#description').val(emod_snippet_data['description']);
        $('#emod_snippet').val(emod_snippet_data['emod_snippet']);
    });

    $('#form-is-valid').val('true');
    $('#emod_snippet_id').val(option_id);
});