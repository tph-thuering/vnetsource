$(document).ready(function()
{
    // Disable enter from triggering a form submission
    $(window).keydown(function(event)
    {
        if(event.keyCode == 13)
        {
            event.preventDefault();
            return false;
        }
    });
});