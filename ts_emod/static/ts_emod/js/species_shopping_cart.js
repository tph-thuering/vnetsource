/*######################################################################################################################
 # VECNet CI - Prototype
 # Date: 4/16/2014
 # Institution: University of Notre Dame
 # Primary Authors:
 #   Robert Jones <Robert.Jones.428@nd.edu>
 ######################################################################################################################*/
/* Javascript for ts_emod/views/BrowseView */

var idCounter = new Date().getTime();

/* Method to be executed when page has been loaded */

/* This function appends an li to the cart */
function li_append(liName) {
    if ( $(this).not('.ui-draggable-dragging') ) {
        $('ul.cart').append(li_get(liName));
        $('.btn-small').tooltip({container:'body', placement:'top'});
    }
}

/* This function is called each time a species is added to the cart,
 no matter how it was added. This keeps all formatting in one place.
 - idCounter unique id allows jQuery validation to know which species to display the validation error messages in.
 */
function li_get(liName) {
    var my_li = '<li data-name="' + liName + '">'
        + '<strong>' + liName + '</strong>'
        + '<em style="font-size:0.9em;">'
        + '<span class="btn-group pull-right">'
        //+ '<button disabled type="button" class="btn btn-small btn-preview" data-original-title="Preview"'
        //+ 'data-content=\'<table class="table-striped table-species">{{ species.json_as_table }}</table>\'>'
        //+ '<i class="icon-eye-open"></i></button>'
        + '<button class="btn btn-small tooltip_link accordion-toggle" data-toggle="collapse" data-parent="#accordion" '
        + 'href="#collapse' + liName.replace(/\./, '\\.') + '" title="Edit parameters"><i class="icon-spinner icon-spin"></i></button>'
        + '<button class="btn btn-small delete" title="Remove this Species"><i class="icon-remove"></i></button>'
        + '</span>'
        + '<input type="hidden" name="species-species" value="' + liName + '"/>';

        // set up accordion on display extra fields to edit
        my_li = my_li
            + ' <div id="collapse' + liName + '" class="accordion-body collapse"> '
            + '<div class="accordion-inner">'
            + '<div id="form-' + liName + '" style="display: block;"><i class="icon-spinner icon-spin icon-large"></i>&nbsp;&nbsp;Loading vector species parameters...</div>'
            + '</div></div></li>';
    return my_li;
}

$(document).ready(function() {

    // jQuery UI Draggable for all items
    $("#species ul li").draggable({
        connectToSortable: ".cart",
        // clone available species entry so users can reuse.
        helper:"clone",

        // once the dragging starts, we decrease the opactiy of other items
        // Appending a class as we do that with CSS
        drag:function () {
            $(this).addClass("active");
            $(this).closest("#species").addClass("active");
        },

        // removing the CSS classes once dragging is over.
        stop:function () {
            $(this).removeClass("active").closest("#species").removeClass("active");
        }
    });

    // jQuery UI Draggable for .ui-draggable-disabled items
    // #3562 - items already in the cart should be disabled
    $("#species ul li.ui-draggable-disabled").draggable({
        disabled: true
    });

    // jQuery Ui Droppable
    $(".cart").sortable({

        // The sensitivity of acceptance of the item once it touches the to-be-dropped-element cart
        tolerance:"touch",

        // The class that will be appended once we are hovering the to-be-dropped-element (cart)
        //hoverClass :"hover",  hoverClass works for droppable but not sortable
        over:function () {
            $(this).addClass("hover");
            //$(this).closest("#species").addClass("active");
        },

        // Remove the class when hovering stops
        out:function () {
            $(this).removeClass("hover");
            //$(this).closest("#species").addClass("active");
        },

        /* This function runs when an item is dropped in the cart
         - change the dragged item to match the format for inputting the fields.
         - this would be better done in receive:(), but doesn't work there, see jQuery bug #4303 */
        update:function (event, ui) {
            if ( ui.item.attr("class").match(/ui-draggable/g)) {
                var liName = ui.item.attr("data-name");
                ui.item[0].outerHTML = li_get(liName);
                $('.btn-small').tooltip({container:'body', placement:'top'});
                /* #3562 - make unselectable when selected */
                var source = $("#shelf_list").find("[data-name='" + liName + "']");
                source.draggable( 'disable' );
                source.find(".add_button").prop("disabled", true);
                $('.tooltip').remove();  //remove the tool tip element
                // add form fields for the selected species' parameters
                add_form(liName);
            }
        }

    });


    // This function runs when add button is clicked
    $("#species ul li button.add_button").click(function () {
        if ( $(this).not('.ui-draggable-dragging') ) {
            var liName = $(this).closest('li').attr('data-name');
            li_append(liName);
            /* #3562 - make unselectable when selected */
            $(this).closest('li').draggable( 'disable' );
            $(this).prop("disabled", true);
            $('.tooltip').remove();  //remove the tool tip element
            // add form fields for the selected species' parameters
            add_form(liName);
            return false;
        }
    });


    // This function runs when delete button is pressed
    $(".cart li button.delete").live("click", function () {
        var liName = $(this).closest('li').attr('data-name');
        $('.tooltip').remove();  //remove the tool tip element
        $(this).closest("li").remove();
        /* #3562 - make unselectable when selected: put back on shelf when deleted */
        var source = $("#shelf_list").find("[data-name='" + liName + "']");
        if (! source.length) {  /* try the custom shelf list */
            source = $("#shelf_list_custom").find("[data-name='" + liName + "']");
        }
        source.draggable( 'enable' );
        source.find(".add_button").prop("disabled", false);
    });


    // This function gets called when the Next button is clicked
    $('#speciesForm').submit(function() {
        if ( $('.cart li').length > 0 ) {
            return true;
        } else {
            alert("Please select at least one Vector Species.");
            return false;
        }
    });

    jQuery.validator.addMethod("notEqualTo",
        function(value, element, param) {
            var notEqual = true;
            value = $.trim(value).replace(" ", "_");
            for (var i = 0; i < param.length; i++) {
                if (value == param[i]) { notEqual = false; }
            }
            return notEqual;
        },
        "A vector species with this name already exists. Please enter a different name."
    );

});

// Return the species edit form
function add_form(name){
    if ( ! name ) { return false; }
    $.ajax({
        //async: false,
        type: "GET",
        url: my_form_url + name
        }).done(function( data ) {
            data = data.replace(/json_/g, name + "__json_");
        $("#form-"+name.replace(/\./, '\\.')).html(data);
        /* Enable tooltips for the newly loaded fields */
        $('.tooltip_link').tooltip({container: 'body', placement: 'top'})
    }).always(function() {
            var test = $("li[data-name=" + name.replace(/\./, '\\.') + "]").find('i.icon-spinner');
            if (test.hasClass('icon-spinner')) {
                test.removeClass('icon-spinner').removeClass('icon-spin').addClass('icon-edit');
            }
        });
}

// Return the species edit form with user's values included
function add_form_values(name){
    if ( ! name ) { return false; }

    $.ajax({
        async: false,
        type: "GET",
        url: my_form_url + name
        }).done(function( data ) {
            data = data.replace(/json_/g, name + "__json_");
        $("#form-"+name).html(data);
        /* Enable tooltips for the newly loaded fields */
        $('.tooltip_link').tooltip({container: 'body', placement: 'top'});
    }).always(function() {
            var test = $("li[data-name=" + name.replace(/\./, '\\.') + "]").find('i.icon-spinner');
            if (test.hasClass('icon-spinner')) {
                test.removeClass('icon-spinner').removeClass('icon-spin').addClass('icon-edit');
            }
    });
    // replace default values with what the user entered
    var my_li = $("ul.cart");
    my_li = my_li.find("li[data-name="+ name + "]");
    for(var key in species_chosen_values) {
        if (key.indexOf(name + "__json") > -1) {
            var my_field = my_li.find("input[name="+ key + "]");
            if (my_field.val() != species_chosen_values[key]) {
                my_field.val(species_chosen_values[key]);
            }
        }
    }
}
