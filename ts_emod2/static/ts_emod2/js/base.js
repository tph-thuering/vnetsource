/* function to set the character-remaining counts at page load time */
$(window).ready(function()
{
    if ($("#id_start-description").length > 0)
    {
        $("#count").text((1000 - $("#id_start-description").val().length));
    }
});

/* function to set the character-remaining counts during typing events */
$("#id_start-description").keyup(function()
{
    $("#count").text((1000 - $(this).val().length));
});

/* function to cause page elements to pulse opacity */
// pulse($('.btn-target'), 1250, 'swing', {opacity:.5}, {opacity:1}, function() { return false; });
function pulse(elem, duration, easing, props_to, props_from, until)
{
    elem.animate( props_to, duration, easing, function()
    {
        if (until() == false)
        {
            pulse(elem, duration, easing, props_from, props_to, until);
        }
    });
}
