// species_data_url, previously_selected_species_ids, and species_options come in via django and must be set before including this file

var species_counter = 0;  // This is the counter to make new species elements so that we don't have to worry about array splicing when we remove a species.
var species_on_page = [];  // This is just a list of the on-page species ids so that ids can be added and removed without having to worry about array splicing.
var species_already_used = [];  // This is a list of the actual species ids so that we can remove (or add) species from other lists so that we don't have duplicates.
var on_page_species_to_saved_species_map = {};  // This is used to have an easy way to add/remove/update species that will be saved. Example: {27: 1} where 27 would be the on-page species id and the 1 is the in-database species id
var species_to_load = previously_selected_species_ids.length;

$(document).ready(function()
{
    var i;

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

    // Initialize the species list
    data_to_save['species'] = [];

    if (previously_selected_species_ids.length == 0)
    {
        add_species(-1);
    }
    else
    {
        for (i = 0; i < previously_selected_species_ids.length; i++)
        {
            add_species(i);
        }
    }

    // This reenables the second set of save buttons. Just a visual thing. Initially the second set is hidden because
    // it looks tacky if they are showing, but after everything is loaded, then the buttons are displayed again.
    $('#save_buttons_2').show();

    $('#form-is-valid').val(true);
});




// If previously_selected_species_ids_index is -1, then this is a brand new species, as opposed to one from a previous
// visit to this page.
function add_species(previously_selected_species_ids_index)
{
    var new_species_html = $('#species-template').html();
    var new_species_wrapper;
    var new_species_remove_button;
    var new_species_description;
    var new_species_parameters;
    var new_species_id;

    if (species_already_used.length == species_options.length)
    {
        alert("All species already added.");
        return;
    }

    $('#species-section').append(new_species_html);

    new_species_wrapper = $('.species-wrapper').last();
    new_species_wrapper.attr('id', 'species' + species_counter + '-wrapper');  // Example: id="species1-wrapper"

    new_species_remove_button = new_species_wrapper.find('.species-remove-button');
    new_species_remove_button.attr('onclick', 'remove_species(' + species_counter + ')');  // Example: onclick="remove_species(1)"

    add_species_select(new_species_wrapper, species_counter, previously_selected_species_ids_index);

    new_species_description = new_species_wrapper.find('.species-description');
    new_species_description.attr('id', 'species' + species_counter + '-description');  // Example: id="species1-description"

    new_species_parameters = new_species_wrapper.find('.species-parameters');
    new_species_parameters.attr('id', 'species' + species_counter + '-parameters');  // Example: id="species1-parameters"

    species_on_page.push(species_counter);

    new_species_id = $('#species' + species_counter + '-select').val();
    species_already_used.push(new_species_id);
    remove_species_from_select_lists(species_counter, new_species_id);

    on_page_species_to_saved_species_map[species_counter] = data_to_save['species'].length;

    // Store the species data to be saved
    data_to_save['species'].push({});
    update_species(species_counter);  // This handles adding everything about the species

    species_counter++;
}

function add_species_select(new_species_wrapper, on_page_species_id, previously_selected_species_ids_index)
{
    var new_species_select;
    var i;
    var j;
    var id_should_be_skipped;
    var species_option_html;
    var default_species = -1;

    new_species_select = new_species_wrapper.find('.species-select');
    new_species_select.attr('id', 'species' + on_page_species_id + '-select');  // Example: id="species1-select"

    // Example: <option value="1" selected>Farauti</option>
    //          <option value="2">Dirus</option>
    for (i = 0; i < species_options.length; i++)
    {
        id_should_be_skipped = false;

        for (j = 0; j < species_already_used.length; j++)
        {
            if (species_options[i]['id'] == species_already_used[j])
            {
                id_should_be_skipped = true;
            }
        }

        if (id_should_be_skipped)
        {
            continue;
        }

        species_option_html = '<option value="' + species_options[i]['id'] + '"';

        if (previously_selected_species_ids_index != -1)
        {
            if (species_options[i]['id'] == previously_selected_species_ids[previously_selected_species_ids_index])
            {
                species_option_html += ' selected';
                default_species = species_options[i]['id'];
            }
        }

        species_option_html += '>' + species_options[i]['name'] + '</option>';

        new_species_select.append(species_option_html);
    }

    new_species_select.change({select_id: on_page_species_id}, function(event)
    {
        update_species(event.data.select_id);
        remove_species_from_select_lists(event.data.select_id, default_species);
    });

    // Save the currently selected value and name so we can use it later when it is changed
    new_species_select.data("previous_id", new_species_select.val());
    new_species_select.data("previous_name", new_species_select.find(":selected").text().trim());
}

function update_species(on_page_species_id)
{
    var species_select = $('#species' + on_page_species_id + '-select');
    var new_species_id = species_select.val();
    var the_url = species_data_url + new_species_id + "/";
    var species_list_position;
    var species_parameters_section = $('#species' + on_page_species_id + '-parameters');
    var species_parameters_html = "";
    var i;
    var j;
    var horizontal_line = '<hr size="1" style="margin: 1px; background-color: black; border:none">';
    var parameter_name;
    var parameter_value;

    $.ajax(
    {
        type: "GET",
        url: the_url
    }).success(function(species_data)
    {
        $('#species' + on_page_species_id + '-description').html(species_data['description'] + '<br><br>');

        for (i = 0; i < species_data['parameters'].length; i++)
        {
            parameter_name = species_data['parameters'][i]['name'];

            // This is to make sure we display the values correctly if there is more than 1 (ie larval habitat).
            if (typeof species_data['parameters'][i]['value'] === 'object')
            {
                parameter_value = '';

                for (j = 0; j < species_data['parameters'][i]['value'].length; j++)
                {
                    parameter_value += species_data['parameters'][i]['value'][j] + '<br>';
                }
            }
            else  // Else must be a number
            {
                parameter_value = parseFloat(species_data['parameters'][i]['value']).toFixed(3);
            }

            species_parameters_html +=
                '<div class="row">' +
                    '<div class="span8">' +
                        horizontal_line +
                    '</div>' +

                    '<div class="span3">' +
                        parameter_name + ':' +
                    '</div>' +

                    '<div class="span2">' +
                        parameter_value +
                    '</div>' +
                '</div>';
        }

        species_parameters_section.html(species_parameters_html);

        // This if statement reads as "if we aren't updating the choice to the same value", however, this isn't
        // really possible because if you select the currently selected option, it will not trigger a change(). Instead,
        // this check is here to skip this section if we are adding the species for the first time.
        if (species_select.data("previous_id") != species_select.val())
        {
            // Add the old value to the other select lists
            add_species_to_lists(on_page_species_id, species_select.data("previous_id"), species_select.data("previous_name"));

            // Remove the old value from the used list
            for (i = 0; i < species_already_used.length; i++)
            {
                if (species_already_used[i] == species_select.data("previous_id"))
                {
                    species_already_used.splice(i, 1);
                    break;
                }
            }

            // Add the new value to the used list
            species_already_used.push(new_species_id);

            // Remove the new value from the other lists
            remove_species_from_select_lists(on_page_species_id, new_species_id);
        }

        // Update the stored data (Doesn't save until the save button is pressed)
        species_list_position = on_page_species_to_saved_species_map[on_page_species_id];  // Check the map to find the correct species data to update
        data_to_save['species'][species_list_position]['species_id'] = new_species_id;

        // Update the select previous data to the new selection
        species_select.data("previous_value", species_select.val());
        species_select.data("previous_name", species_select.find(":selected").text().trim());
    });

    if (species_to_load > 0)
    {
        species_to_load -= 1;
    }
    else
    {
        $('.save-button').attr('style', '');
    }
}

function add_species_to_lists(list_that_species_was_chosen_from, id_to_add, name_to_add)
{
    var i;
    var species_select;

    for (i = 0; i < species_on_page.length; i++)
    {
        if (list_that_species_was_chosen_from != i)
        {
            species_select = $('#species' + i + '-select');

            species_option_html = '<option value="' + id_to_add + '"';
            species_option_html += '>' + name_to_add + '</option>';

            species_select.append(species_option_html);
        }
    }
}

function remove_species(on_page_species_id)
{
    var species_select = species_select = $('#species' + on_page_species_id + '-select');
    var species_id = species_select.val();
    var species_name = species_select.find(":selected").text().trim();

    if (species_already_used.length == 1)
    {
        alert('You cannot remove the last species.');
        return;
    }

    remove_species_from_data_to_save(on_page_species_id);
    add_species_to_lists(species_id, species_name);
    remove_from_species_already_used_list(species_id);

    $('#species' + on_page_species_id + '-wrapper').remove();
}

function remove_species_from_select_lists(list_that_species_was_chosen_from, value_to_remove)
{
    var i;

    for (i = 0; i < species_on_page.length; i++)
    {
        if (list_that_species_was_chosen_from != i)
        {
            $('#species' + i + '-select option').each(function()
            {
                if ($(this).val() == value_to_remove)
                {
                    $(this).remove();
                }
            });
        }
    }
}

function remove_species_from_data_to_save(on_page_species_id)
{
    var species_list_position = on_page_species_to_saved_species_map[on_page_species_id];  // Check the map to find the correct species data to update

    data_to_save['species'].splice(species_list_position, 1);
}

function remove_from_species_already_used_list(species_id)
{
    var index = -1;
    var i;

    for (i = 0; i < species_already_used.length; i++)
    {
        if (species_already_used[i] == species_id)
        {
            index = i;
            break;
        }
    }

    if (index != -1)
    {
        species_already_used.splice(index, 1);
    }
    else
    {
        alert("Species is not in species_already_used_list.");
    }
}