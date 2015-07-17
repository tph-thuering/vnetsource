// delete_scenarios_url comes in via django and must be set before including this file

function toggle_select_all()
{
    var last_state = 0;  // States are true and false. 0 means no state set yet.
    var all_states_are_the_same = true;
    var select_checkboxes = $('.select-checkbox');

    // Check if everything is either on or everything is off
    select_checkboxes.each(function ()
    {
        if (!all_states_are_the_same)
        {
            return;
        }

        if (last_state != 0 && $(this).prop('checked') != last_state)
        {
            all_states_are_the_same = false;
        }
        else
        {
            last_state = $(this).is(':checked');
        }
    });

    if (all_states_are_the_same)  // Then toggle them
    {
        select_checkboxes.each(function ()
        {
           $(this).prop('checked', !last_state);
        });
    }
    else  // Turn on everything
    {
        select_checkboxes.each(function ()
        {
            $(this).prop('checked', true);
        });
    }
}

function fill_delete_modal()
{
    var select_checkboxes = $('.select-checkbox');
    var simulations_selected_count = 0;
    var scenario_name = 'testing modal';

    // Check how many are on
    select_checkboxes.each(function ()
    {
        if ($(this).is(':checked'))
        {
            simulations_selected_count += 1;
        }
    });

    if (simulations_selected_count == 0)
    {
        $('#delete-button').attr('data-toggle', '');
        alert('No simulations selected for deletion.')
    }
    else
    {
        $('#delete-button').attr('data-toggle', 'modal');
    }

    if (simulations_selected_count == 1)
    {
        $('#delete-modal-label').text('Delete Simulation');
        $('#delete-modal-body-text').text('Are you sure you want to delete simulation ' + scenario_name + ' and all related data?');
    }
    else
    {
        $('#delete-modal-label').text('Delete Simulations');
        $('#delete-modal-body-text').text('Are you sure you want to delete these ' + simulations_selected_count + ' simulations and all related data?');
    }
}

function delete_scenarios()
{
    var select_checkboxes = $('.select-checkbox');
    var scenarios = [];

    // Add each checked box to a list
    select_checkboxes.each(function ()
    {
        if ($(this).is(':checked'))
        {
            scenarios.push($(this).val());
        }
    });

    $.ajax(
    {
        data: {'scenarios': JSON.stringify(scenarios)},
        type: "POST",
        url: delete_scenarios_url,

        success: function()
        {
            location.reload();
        }
    });
}