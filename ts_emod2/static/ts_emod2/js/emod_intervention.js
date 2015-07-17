function toggle_disabled_and_set_empty(id)
{
    var object = $('#' + id);

    object.attr('disabled', !object.attr('disabled'));
    object.val('');
}

function fill_item_with_form(new_item)
{
    var prefix = new_item.data('prefix');
    var intervention_total_forms_input = $('#id_' + prefix + '-TOTAL_FORMS');
    var new_intervention_index = intervention_total_forms_input.val();
    var edit_button;
    var remove_button;
    var start_day_input;
    var distributions_checkbox;
    var distributions_input;
    var repetitions_checkbox;
    var repetitions_input;
    var timesteps_input;
    var accordion;

    new_item.html($('#empty-form-' + prefix).html());

    // First change the li id to something real
    new_item.attr('id', 'id_' + prefix + '-' + new_intervention_index + '-li');

    // Set the variable that tells if this item was already in the cart or not. The user could just be sorting.
    new_item.attr('data-already-in-cart', 'true');

    // Rename id and name values from Intervention-__prefix__-field_name to Intervention-index-field_name for inputs
    new_item.find('input').each(function()
    {
        if ($(this).attr('id'))
        {
            update_form_input_attribute($(this), 'id', new_intervention_index);
        }

        if ($(this).attr('name'))
        {
            update_form_input_attribute($(this), 'name', new_intervention_index);
        }
    });

    // Rename id and name values from Intervention-__prefix__-field_name to Intervention-index-field_name for selects
    new_item.find('select').each(function()
    {
        if ($(this).attr('id'))
        {
            update_form_input_attribute($(this), 'id', new_intervention_index);
        }

        if ($(this).attr('name'))
        {
            update_form_input_attribute($(this), 'name', new_intervention_index);
        }
    });

    edit_button = new_item.find('#id_' + prefix + '-__prefix__-edit-button');
    edit_button.attr('data-target', '#id_' + prefix + '-' + new_intervention_index + '-accordion');

    remove_button = new_item.find('#id_' + prefix + '-__prefix__-remove-button');
    remove_button.attr('onclick', "remove_intervention('id_" + prefix + "-" + new_intervention_index + "-li');");

    distributions_checkbox = new_item.find('#id_' + prefix + '-' + new_intervention_index + '-distributions-checkbox');
    distributions_checkbox.attr('onclick', "toggle_disabled_and_set_empty('id_" + prefix + "-" + new_intervention_index + "-max_number_of_distributions');");

    repetitions_checkbox = new_item.find('#id_' + prefix + '-' + new_intervention_index + '-repetitions-checkbox');
    repetitions_checkbox.attr('onclick',
        "toggle_disabled_and_set_empty('id_" + prefix + "-" + new_intervention_index + "-number_of_repetitions');" +
        "toggle_disabled_and_set_empty('id_" + prefix + "-" + new_intervention_index + "-timesteps_between_repetitions');"
    );

    // The accordion is a div not an input, so we search using -__prefix__- instead of the intervention_index, since it
    // wasn't changed in the update_form_input_attribute calls.
    accordion = new_item.find('#id_' + prefix + '-__prefix__-accordion');
    accordion.attr('id', 'id_' + prefix + '-' + new_intervention_index + '-accordion');

    // This needs to be reapplied for the new one. Technically this will apply to all again, which is wasteful, but
    // no big deal for now.
    //enable_popovers_and_tooltips();

    intervention_total_forms_input.val(parseInt(intervention_total_forms_input.val()) + 1)
}