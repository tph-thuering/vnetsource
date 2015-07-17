$(document).ready(function()
{
    var species;

    // Disable enter from triggering a form submission
    $(window).keydown(function(event)
    {
        if(event.keyCode == 13)
        {
            event.preventDefault();
            return false;
        }
    });

    // Save the scenario id
    data_to_save['scenario_id'] = $('#scenario_id').val();

    // Get the default values to save
    data_to_save['parasite_parameters'] = {};
    data_to_save['parasite_parameters']['species'] = {};

    for (species in parasite_parameters.species)
    {
        data_to_save['parasite_parameters']['species'][species] = {};
        data_to_save['parasite_parameters']['species'][species]['EIR'] = $('input[name=' + species + "-EIR" + ']:checked').val(); // Looks for the input named "EIR" that is checked and gets its value

        // Save new EIR choice
        $('#' + species + '-EIR-fieldset').change({the_species: species}, function(event)
        {
            // Get the EIR to save
            data_to_save['parasite_parameters']['species'][event.data.the_species]['EIR'] = $('input[name=' + event.data.the_species + "-EIR" + ']:checked').val(); // Looks for the input named "EIR" that is checked and gets its value

//            // Enable Save button
//            $('.save-button').attr('style', '');
        });
    }
//    data_to_save['parasite_parameters']['new_diagnostic_sensitivity'] = parseFloat($('#new_diagnostic_sensitivity').val());
//    data_to_save['parasite_parameters']['parasite_smear_sensitivity'] = parseFloat($('#parasite_smear_sensitivity').val());

    $('#form-is-valid').val(true);
});

//// Save new new_diagnostic_sensitivity choice
//$('#new_diagnostic_sensitivity').keyup(function()
//{
//    // Get the new_diagnostic_sensitivity to save
//    data_to_save['parasite_parameters']['new_diagnostic_sensitivity'] = parseFloat($('#new_diagnostic_sensitivity').val());
//
//    // Remove Save button
//    $('.save-button').attr('style', '');
//});
//
//// Save new parasite_smear_sensitivity choice
//$('#parasite_smear_sensitivity').keyup(function()
//{
//    // Get the parasite_smear_sensitivity to save
//    data_to_save['parasite_parameters']['parasite_smear_sensitivity'] = parseFloat($('#parasite_smear_sensitivity').val());
//
//    // Remove Save button
//    $('.save-button').attr('style', '');
//});