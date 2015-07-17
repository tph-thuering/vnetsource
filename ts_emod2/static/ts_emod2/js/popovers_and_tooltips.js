function enable_popovers_and_tooltips()
{
    // Ensure that all tooltips are enabled (For backwards compatibility, include for: <a class="btn-small"> elements)
    $('.tooltip_link').tooltip(
    {
        container: 'body',
        placement: 'top',
        'delay':
        {
            show: 500,
            hide: 500
        }
    });

    $('.tooltip_button').tooltip(
    {
        container: 'body',
        placement: 'top',
        'delay':
        {
            show: 500,
            hide: 500
        }
    });

    $('input').tooltip(
    {
        container: 'body',
        'delay':
        {
            show: 500,
            hide: 500
        }
    });  /* took out of browser.js - not sure where it's used, maybe could be removed */

    // enable popovers - used on info button
    $('.info').popover(
    {
        placement: 'left',
        html: 'true',
        container: 'body'
    });

    $('.btn-preview').popover(
    {
        placement: 'top',
        html: 'true',
        container: 'body',
        template:
            '<div class="popover">' +
                '<div class="arrow"></div>' +
                '<div class="popover-inner">' +
                    '<div class="popover-content">' +
                        '<p></p>' +
                    '</div>' +
                '</div>' +
            '</div>'
    });

    // This closes a popover if you click anywhere not on the popover
    // todo: turn button icon into red circle X close button
    $('html').on('click', function(event)
    {
        $('.info').each(function ()
        {
            // 'is' for buttons that trigger popups
            // 'has' for icons within a button that triggers a popup
            if (!$(this).is(event.target) && $('.popover').has(event.target).length === 0)
            {
                $(this).popover('hide');
            }
        });

        $('.btn-preview').each(function ()
        {
            // 'is' for buttons that trigger popups
            // 'has' for icons within a button that triggers a popup
            if (!$(this).is(event.target) && $('.popover').has(event.target).length === 0)
            {
                $(this).popover('hide');
            }
        });
    });
}

function hide_info()
{
    $('.info').each(function ()
    {
        $(this).popover('hide');
    });

    $('.btn-preview').each(function ()
    {
        $(this).popover('hide');
    });
}