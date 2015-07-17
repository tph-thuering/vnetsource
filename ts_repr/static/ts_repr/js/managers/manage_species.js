// species_data_url, emod_snippet_data_url, and om_snippet_data_url come in via django and must be set before including this file

$(document).ready(function()
{
    $('#species-select').change();
});

$('#species-select').change(function()
{
    var option_id = $(this).val();
    var the_url = species_data_url + option_id + "/";

    $.ajax(
    {
        type: "GET",
        url: the_url

    }).success(function(species_data)
    {
        $('#name').val(species_data['name_for_users']);
        $('#description').html(species_data['description']);

        if (species_data == -1)
        {
            $('#is_active').prop("checked", true);
        }
        else
        {

            if (species_data['is_active'] == true)
            {
                $('#is_active').prop("checked", true);
            }
            else
            {
                $('#is_active').prop("checked", false);
            }

            $('#emod-snippet-select').val(species_data['emod_snippet_id']);
            $('#emod-snippet-textarea').val(species_data['emod_snippet']);
            $('#emod_snippet_id').val(species_data['emod_snippet_id']);  // Backend version

            $('#om-snippet-select').val(species_data['om_snippet_id']);
            $('#om-snippet-textarea').val(species_data['om_snippet']);
            $('#om_snippet_id').val(species_data['om_snippet_id']);  // Backend version
        }
    });

    $('#form-is-valid').val('true');
    $('#species_id').val(option_id);
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
        $('#emod-snippet-textarea').val(emod_snippet_data['emod_snippet']);
    });

    $('#emod_snippet_id').val(option_id);
});

$('#om-snippet-select').change(function()
{
    var option_id = $(this).val();
    var the_url = om_snippet_data_url + option_id + "/";

    $.ajax(
    {
        type: "GET",
        url: the_url

    }).success(function(om_snippet_data)
    {
        $('#om-snippet-textarea').val(om_snippet_data['om_snippet']);
    });

    $('#om_snippet_id').val(option_id);
});