// previous_page_number, next_page_number, and type_currently_shown come in via django and must be set before including this file

$(document).ready(function()
{
    set_page_buttons();
});

function set_page_buttons()
{
    var pager_size = $('#pager_size').val();
    var previous_button_href;
    var next_button_href;

    if (previous_page_number == -1)
    {
        $('#previous-button-li').addClass('disabled');
    }
    else
    {
        previous_button_href = '?page=' + previous_page_number + '&pager_size=' + pager_size +
            '&type=' + type_currently_shown;
        $('#previous-button').attr('href', previous_button_href);
    }

    if (next_button_href == -1)
    {
        $('#next-button-li').addClass('disabled');
    }
    else
    {
        next_button_href = '?page=' + next_page_number + '&pager_size=' + pager_size +
            '&type=' + type_currently_shown;
        $('#next-button').attr('href', next_button_href);
    }
}