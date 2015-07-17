function add_draggability(draggable_div, should_clone, should_revert)
{
    var helper_setting;

    if (should_clone)
    {
        helper_setting = "clone";
    }
    else
    {
        helper_setting = "original";
    }

    // jQuery UI Draggable
    draggable_div.find("ul li").draggable(
    {
        connectToSortable: ".cart",

        // clone available entry so users can reuse.
        helper: helper_setting,

        // brings the item back to its place when dragging is over
        revert: should_revert,

        // once the dragging starts, we decrease the opacity of other items
        // Appending a class as we do that with CSS
        drag: function ()
        {
            $(this).addClass("active");
            $(this).closest("#draggable_div").addClass("active");
        }, // Need to check on this drag function

        // removing the CSS classes once dragging is over.
        stop:function ()
        {
            $(this).removeClass("active").closest("#draggable_div").removeClass("active");
        } // Need to check on this stop function
    });
}

function add_droppability(shopping_cart_div)
{
    shopping_cart_div.sortable(
    {
        // The sensitivity of acceptance of the item once it touches the to-be-dropped-element cart
        tolerance: "touch",

        // This highlights the cart when you are dragging items into it or within it to sort.
        over:function ()
        {
            $(this).addClass("hover");
        },

        // This stops the highlighting of the cart when you stop dragging items.
        out:function ()
        {
            $(this).removeClass("hover");
        },

        // This function runs when an item is dropped in the cart
        // change the dragged item to match the format for inputting the fields.
        // this would be better done in receive:(), but doesn't work there, see jQuery bug #4303
        update:function (event, ui)
        {
            // This is the only way I could think of to figure out if this is already a part of the list, or something
            // new. When an item is added for the first time, this is undefined. Afterwards, it will be true. This is
            // set in the fill_item_with_form function.
            if (ui.item.attr('data-already-in-cart') != 'true')
            {
                fill_item_with_form(ui.item);
            }
        }
    });
}