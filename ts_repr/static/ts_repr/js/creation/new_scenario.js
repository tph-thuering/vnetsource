$(document).ready(function()
{
    // Save the representative id
    data_to_save['representative_id'] = $('#representative_id').val();

    // Initializes description
    $('#model-select').change();

    $('#form-is-valid').val('true');
});

$('#model-select').change(function()
{
    var option_id = $(this).val();

    $('#model-select').val(option_id);
    data_to_save['model_choice'] = option_id;
});