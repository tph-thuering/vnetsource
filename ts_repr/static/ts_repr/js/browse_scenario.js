// previous_page_number, next_page_number, and type_currently_shown come in via django and must be set before including this file

/* Method to be executed when page has been loaded */
$(document).ready(function()
{
    set_page_buttons();

    $('a[data-confirm]').click(function (event)
    {
        var href = $(this).attr('href');

        if (!$('#delete-modal').length)
        {
            $('body').append(
                '<div id="delete-modal" class="modal fade" role="dialog" aria-labelledby="delete-modal-label" aria-hidden="true">' +
                    '<div class="modal-header">' +
                        '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">' +
                            '×' +
                        '</button>' +

                        '<h3 id="delete-modal-label">' +
                            '<i class="icon-warning-sign"></i>&nbsp;&nbsp;&nbsp;Please Confirm' +
                        '</h3>' +
                    '</div>' +

                    '<div class="modal-body">' +
                    '</div>' +

                    '<div class="modal-footer">' +
                        '<button class="btn pull-left" data-dismiss="modal" aria-hidden="true">' +
                            'Cancel' +
                        '</button>' +

                        '<a class="btn btn-danger" id="delete-modal-confirm">' +
                            'Delete' +
                        '</a>' +
                    '</div>' +
                '</div>'
            );
        }

        $('#delete-modal').find('.modal-body').text($(this).attr('data-confirm'));
        $('#delete-modal-confirm').attr('href', href);
        $('#delete-modal').modal({show: true});

        return false;
    });
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