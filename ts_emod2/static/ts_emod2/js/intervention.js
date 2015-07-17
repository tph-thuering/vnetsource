var draggable_div = $("#intervention-templates");
var droppable_div = $(".cart");
var should_clone_cart_elements = true;
var should_revert_cart_elements = false;

$(document).ready(function()
{
    add_draggability(draggable_div, should_clone_cart_elements, should_revert_cart_elements);
    add_droppability(droppable_div);
    enable_popovers_and_tooltips();
});

function add_intervention(prefix)
{
    // Take the template and put it into li tags and you have a new item to add to the cart. Also need a data-prefix
    // for the fill_item_with_form function and an id to find it easily.
    var new_item_html = '<li id="new-item" data-prefix="' + prefix + '">' + $('#empty-form-' + prefix).html() + '</li>';
    var new_item;

    // Add the new item and put it into a reference to it in a variable
    $('.cart').append(new_item_html);
    new_item = $('#new-item');

    // Fill the item with the form associated with it.
    fill_item_with_form(new_item);
}

function remove_intervention(li_id)
{
    var item_to_remove = $('#' + li_id);

    item_to_remove.remove();
}

function update_form_input_attribute(html_element, attribute_name, index)
{
    //alert(html_element.attr(attribute_name));
    var attribute_split = html_element.attr(attribute_name).split('__prefix__');
    var new_attribute_value = attribute_split[0] + index + attribute_split[1];

    html_element.attr(attribute_name, new_attribute_value);
}