/*######################################################################################################################
 # VECNet CI - Prototype
 # Date: 4/5/2013
 # Institution: University of Notre Dame
 # Primary Authors:
 #   Robert Jones <Robert.Jones.428@nd.edu>
 ######################################################################################################################*/
/* Javascript for ts_emod/views/ScenarioWizard Intervention Step */
var InterventionShoppingCart = InterventionShoppingCart || {};
InterventionShoppingCart.start_day_max = "";
InterventionShoppingCart.intervention_selected = "";
InterventionShoppingCart.my_form_url = "";
InterventionShoppingCart.my_campaign = {};
InterventionShoppingCart.my_step = "";
/* unique ID for selected Intervention rows' settings validation */
var idCounter = new Date().getTime();

/* Method to be executed when page has been loaded */
$(function () {
  var cartDiv = $(".cart");
  var interventionDiv = $("#intervention");

    // jQuery UI Draggable
    interventionDiv.find("ul li").draggable({
        connectToSortable: ".cart",
        // clone available intervention entry so users can reuse.
        helper:"clone",
        // brings the item back to its place when dragging is over
        //revert:true,

        // once the dragging starts, we decrease the opactiy of other items
        // Appending a class as we do that with CSS
        drag:function () {
            $(this).addClass("active");
            $(this).closest("#intervention").addClass("active");
        },

        // removing the CSS classes once dragging is over.
        stop:function () {
            $(this).removeClass("active").closest("#intervention").removeClass("active");
        }
    });


    // jQuery Ui Droppable
    cartDiv.sortable({

        // The sensitivity of acceptance of the item once it touches the to-be-dropped-element cart
        tolerance:"touch",

        // The class that will be appended once we are hovering the to-be-dropped-element (cart)
        //hoverClass :"hover",  hoverClass works for droppable but not sortable
        over:function () {
            $(this).addClass("hover");
            //$(this).closest("#intervention").addClass("active");
        },

        // Remove the class when hovering stops
        out:function () {
            $(this).removeClass("hover");
            //$(this).closest("#intervention").addClass("active");
        },

        /* This function runs when an item is dropped in the cart
         - change the dragged item to match the format for inputting the fields.
         - this would be better done in receive:(), but doesn't work there, see jQuery bug #4303 */
        update:function (event, ui) {
            if ( ui.item.attr("class").match(/ui-draggable/g)) {
                var liID = ui.item.attr("data-id");
                // create unique id, so multiple interventions made from same source li don't have duplicate id's
                var liID_old = liID;
                liID = liID + '_' + idCounter;
                var liName = ui.item.attr("data-name");
                ui.item[0].outerHTML = li_get(liID, liName, 0, -1, -1, -1, 1);
                build_form_from_source(liID_old, liID);

                $('.btn-small').tooltip({container:'body', placement:'top'});
            }
        }

    });

    // This function runs when add button is clicked
    interventionDiv.find("ul li .add_button").click(function (mouseEvent) {
        if ( $(this).not('.ui-draggable-dragging') ) {
            var liID = $(this).closest('li').attr('data-id');
            // create unique id, so multiple interventions made from same source li don't have duplicate id's
            var liID_old = liID;
            liID = liID + '_' + idCounter;
            var liName = $(this).closest('li').attr('data-name');
            li_append(liID, liName, 0, -1, -1, -1, 1);

            build_form_from_source(liID_old, liID);
            return false;
        }
    });

    // This function runs when delete button is pressed
    cartDiv.on("click", "li button.delete_entry", function () {
        $('.tooltip').remove();  //remove the tool tip element
        $(this).closest("li").remove();
    });

    // This function loads the cart with previously selected interventions (from step storage - collected in view)
    if (InterventionShoppingCart.my_campaign != '' && JSON.stringify(InterventionShoppingCart.my_campaign, null, 4) != '{}'){
        camp = JSON.parse(JSON.stringify(InterventionShoppingCart.my_campaign['Events'], null, 4)); //;

        for (var interv in camp) {
          if (camp.hasOwnProperty(interv)) {
            var obj = {};
            walk_intervention(obj, camp[interv]);
            var liID = idCounter;
            var liName = obj['my_name'] || obj['class'];
            var liStart_day = obj['Start_Day'] || 0;
            var liNum_rep = obj['Number_Repetitions'] || -1;
            var liDays_between = obj['Timesteps_Between_Repetitions'] || -1;
            var liNumber_Distributions = obj['Number_Distributions'] || -1;
            var liDemog_coverage = obj['Demographic_Coverage'] || 1;
            li_append(liID, liName, liStart_day, liNum_rep, liDays_between, liNumber_Distributions, liDemog_coverage);
            // add form inputs for all the intervention parameters
            // and populate with corresponding values
            build_form_from_view(obj, liID);

            // close "continue without" accordion and open selector accordion
            $('#collapse_with').collapse('hide');
            $('#collapse_without').collapse('show');
          }
        }
    }

  $("#info").attr("data-content", $.trim($(".popover-content").html()));
});


function walk_intervention(obj, p){
    for (var key in p) {
        if (!p.hasOwnProperty(key)) { continue; }
        if (typeof p[key] == "object") { walk_intervention(obj, p[key])}
        else {
            if (key in obj) {
                obj[key + '_' + p[key]] = p[key];
            } else if ('StandardInterventionDistributionEventCoordinator' != p[key]) {
                obj[key] = p[key];
            }
        }
    }
}


/* This function appends an li to the cart */
function li_append(liID, liName, liStart_day, liNum_rep, liDays_between, liNumber_Distributions, liDemog_coverage) {
    if ( $(this).not('.ui-draggable-dragging') ) {
        $('ul.cart').append(li_get(liID, liName, liStart_day, liNum_rep, liDays_between, liNumber_Distributions, liDemog_coverage));
        $('.btn-small').tooltip({container:'body', placement:'top'});
    }
}


/* This function is called each time a intervention is added to the cart,
 no matter how it was added. This keeps all formatting in one place.
 - idCounter unique id allows jQuery validation to know which intervention to display the validation error messages in.
 */
function li_get(liID, liName, liStart_day, liNum_rep, liDays_between, liNumber_Distributions, liDemog_coverage) {
    box_style = ' style="width: 45px; height:11px;" ';
    box_style_readonly = ' style="width: 30px; height:11px; color:#EEE;" readonly ';
    box_style_narrow = ' style="width: 21px; height:11px;" ';
    if ('uupload_0' == liID) {
        var my_li = '<li data-id="'+liID+ '">'
            + '<strong>' + liName + '</strong><br/>'
            + '<em style="font-size:0.8em;">Uploaded file.'
            + '<span class="btn-group pull-right" display="inline">'
            + '<a class="tooltip_link accordion-toggle" data-toggle="collapse" data-parent="#accordion" '
            + 'href="#collapse' + liID + '" title="Edit intervention values"><i class="icon-edit"></i> Edit</a>'
            + '<button class="btn-small delete" title="Remove this Intervention Event"><i class="icon-remove"></i> Remove</button>'
            + '</span>'
            + '<input type="hidden" name="intervention-interventions" value="' + liID + ':' + liName + '"/></li>';
    } else {
        my_li = '<li data-id="'+liID+ '">'
            + '<strong>' + liName + '</strong>';

        // button group, including Remove-intervention button
        my_li = my_li + '<span class="btn-group pull-right" display="inline" style="margin-top: 5px; margin-right: 10px;">'
            + '<button class="tooltip_link accordion-toggle btn btn-small btn-left" data-toggle="collapse" data-parent="#accordion" '
            + 'href="#collapse' + liID + '" title="Edit intervention values" style="color: black;"><i class="icon-edit"></i> Edit</button>'
            + '<button class="btn btn-small btn-right delete_entry" title="Remove this Intervention Event"><i class="icon-remove"></i> Remove</button>'
            + '</span>';

        my_li = my_li + '<br/><em style="font-size:0.8em;"><span style="white-space:nowrap">'
            + 'Start Day: '
            + '<input value="'+ liStart_day +'" type="text" name="intervention-start_day" data-id="'+ liID +'"' + box_style + 'id=' + idCounter++ + '></span>';

        // Number Distributions
        my_li = my_li + '<span style="white-space:nowrap">';
        if (typeof InterventionShoppingCart.my_step !== 'undefined' && InterventionShoppingCart.my_step == 'intervention_tool') {  /* change formatting based on new vs old workflows - my_step set in template */
            my_li = my_li + '&nbsp;&nbsp;&nbsp;&nbsp;<input type="checkbox" style="margin-top:0;" onClick="enable_field(this)"';

            if (liNumber_Distributions > 0) {
                my_li = my_li + ' checked ';
            }
            my_li = my_li + '>&nbsp;Max Number to Distribute: ';

        } else {
            my_li = my_li + '<br/><input type="checkbox" style="margin-top:0;" onClick="enable_field(this)">Max Number to Distribute: ';
        }
        my_li = my_li + '<input value="'+ liNumber_Distributions +'" type="text" name="intervention-Number_Distributions" data-id="'+ liID +'"';
        if (liNumber_Distributions == -1) {
            my_li = my_li + box_style_readonly;  // readonly, not disabled because we need '-1' to be passed back in form
        } else {
            my_li = my_li + box_style;
        }
        my_li = my_li + 'id=' + idCounter++ + '>';
        my_li = my_li + '</span>';

        // Demog_coverage
        my_li = my_li + '<span style="white-space:nowrap">';
        var test = liName.toUpperCase();
        if (test.indexOf("OUTBREAK") == -1 && test.indexOf("FENCE") == -1)  {
            my_li = my_li + '&nbsp;&nbsp;&nbsp;Demographic Usage: '
            + '<input value="'+ liDemog_coverage * 100 +'" type="text" name="intervention-demographic_coverage" data-id="'+ liID +'"' + box_style_narrow + 'id=' + idCounter++ + '>%'
        } else {
            my_li = my_li + '<input value="'+ liDemog_coverage +'" type="hidden" name="intervention-demographic_coverage" data-id="'+ liID +'" id=' + idCounter++ + '>'
        }
        my_li = my_li + '</span>';

        // Number Reps, Time Between Reps
        my_li = my_li + '<br/><span style="white-space:nowrap"><input type="checkbox" style="margin-top:0;" onClick="enable_field(this)"';
        if (liNum_rep > 0) {
                my_li = my_li + ' checked ';
        }
        var my_style = '';
        if (liNum_rep > 0) {
            my_style = box_style;
        } else {
            my_style = box_style_readonly;  // readonly, not disabled because we need '-1' to be passed back in form
        }
        my_li = my_li + '>'+ '&nbsp;Number Repetitions: '
            + '<input value="'+ liNum_rep +'" type="text" name="intervention-num_repetitions" data-id="'+ liID +'"' + my_style + 'id=' + idCounter++ + '>'
            + '&nbsp;&nbsp;&nbsp;Time Between Reps: '
            + '<input value="'+ liDays_between +'" type="text" name="intervention-Timesteps_Between_Repetitions" data-id="'+ liID +'"' + my_style + 'id=' + idCounter++ + '>';
        my_li = my_li + '</span>';

        my_li = my_li + '<input type="hidden" name="intervention-interventions" value="' + liID + ':' + liName + '"/>';

        // set up accordion on display extra fields to edit
        my_li = my_li + ' <div id="collapse' + liID + '" class="accordion-body collapse"> '
            + '<div class="accordion-inner">'
            + '<div id="form-' + liID + '" style="display: block;"><i class="icon-spinner icon-spin icon-large"></i>&nbsp;&nbsp;Loading intervention fields...</div>'
            + '</div></div></li>';
    }
    return my_li;
}

//Provide validation for the fields
//var start_day_max = {{ start_day_max }} // set in template
$(document).ready(function(){
      $("#interventionForm").validate({
          rules: {
              "intervention-start_day": {
                  required: true,
                  range: [0, InterventionShoppingCart.start_day_max]
                  /* digits: true,
                  min: 0,
                  max: start_day_max */
              },
              "intervention-num_repetitions": {
                  required: true,
                  range: [-1, 1000]
              },
              "intervention-Timesteps_Between_Repetitions": {
                  required: true,
                  range: [-1, 10000]
              },
              "intervention-Number_Distributions": {
                  required: true,
                  range: [-1, 2.14748e+009]
              },
              "intervention-demographic_coverage": {
                  required: true,
                  range: [0, 100]
              }
          }
      });
      $("#save").validate({
          rules: {
              "data-my_name": {
                  required: true
              },
              "type_select": {
                  required: true     /* should not = Please select an intervention type <option value="">-Select-</option> */
              }
          }
      });
});


// Return the intervention edit form
function build_form_from_view(obj, id){
    if ( ! id ) {
        return false;
    }

    // get class to choose which config to use
    var data = "";
    var storage = {};
    var my_class = "";

    for (var key in obj) {
        if (!obj.hasOwnProperty(key)) { continue; }

        my_class = obj['class'];
        // Store Set form field input value
        storage[id+'__json_' + key.replace(/ /g, '_')] = obj[key];
    }
    $.ajax({
        async: false,
        type: "GET",
        url: InterventionShoppingCart.my_form_url + my_class //,
        }).done(function( data ) {
            data = data.replace(/json_/g, id + "__json_");
        $("#form-"+id).html(data);
        /* Enable tooltips for the newly loaded fields */
        $('.tooltip_link').tooltip({container: 'body', placement: 'top'});
    });

    for(var key in storage) {
      if (storage.hasOwnProperty(key)) {
        var my_li = $("ul.cart");
        my_li = my_li.find("li[data-id=" + id + "]");
        var my_field = my_li.find("[name=" + key + "]");

        // was input/selector found with this name?
        if (typeof my_field.val() != 'undefined') {
          my_field.val(storage[key]);
        }
        else {
          my_field.val(storage[key]);
        }
      }
    }
}


// Return the intervention edit form
function build_form_from_source(id_source, id){
    if ( ! id ) {
        return false;
    }

    // get li for the id
    var my_text = $("ul.source");
    my_text = my_text.find("li[data-id="+ id_source + "]")
    // get the data-content for button of class btn-preview
    my_text = my_text.find(".btn-preview").attr("data-content").replace(/\//g, '');

    // get class to choose which config to use
    var rows = my_text.replace(/<\/tr>/g, '').split('<tr>');
    // loop through tr's in content (key, value in td's)
    var data = "";
    var storage = {};
    var my_class = "";
    for (var i=1; i < rows.length; i++) {
        columns = rows[i].replace(/<\/td>/g, '').split('<td>')
        if (columns.length < 2) { continue; }
        if (columns[1] == 'Type') { my_class = columns[3]; }
        // Store Set form field input value
        if (columns[1].length > 0) { storage[id+'__json_' + columns[1].replace(/ /g, '_')] = columns[3]; }
    }

    $.ajax({
        async: false,
        type: "GET",
        url: InterventionShoppingCart.my_form_url + my_class //,
        }).done(function( data ) {
            data = data.replace(/json_/g, id + "__json_");
        $("#form-"+id).html(data);
        /* Enable tooltips for the newly loaded fields */
        $('.tooltip_link').tooltip({container: 'body', placement: 'top'});
    });

    for(var key in storage) {
      if (storage.hasOwnProperty(key)) {
        var my_li = $("ul.cart");
        my_li = my_li.find("li[data-id=" + id + "]");
        var my_field = my_li.find("[name=" + key + "]");

        // was input/selector found with this name?
        if (typeof my_field.val() != 'undefined') {
          my_field.val(storage[key]);
        }
        else {
          my_field.val(storage[key]);
        }
      }
    }
}


function enable_field(the_checkbox) {
    if ($(the_checkbox).prop('checked') == true) {
        $(the_checkbox).next("input:text").prop('readonly', false);
        $(the_checkbox).next("input:text").val(1);
        $(the_checkbox).next("input:text").css("color","black");
        $(the_checkbox).next("input:text").css("width","45px");
        if ($(the_checkbox).next("input:text").attr('name') == 'intervention-num_repetitions') {
            $(the_checkbox).next("input:text").next("input:text").prop('readonly', false);
            $(the_checkbox).next("input:text").next("input:text").val(1);
            $(the_checkbox).next("input:text").next("input:text").css("color","black");
            $(the_checkbox).next("input:text").next("input:text").css("width","45px");
        }
    } else {
        // set value back to -1, and change color to default disabled background so it doesn't show
        $(the_checkbox).next("input:text").prop('readonly', true);
        $(the_checkbox).next("input:text").val(-1);
        $(the_checkbox).next("input:text").css("color","#EEE");
        $(the_checkbox).next("input:text").css("width","30px");
        if ($(the_checkbox).next("input:text").attr('name') == 'intervention-num_repetitions') {
            $(the_checkbox).next("input:text").next("input:text").prop('readonly', true);
            $(the_checkbox).next("input:text").next("input:text").val(-1);
            $(the_checkbox).next("input:text").next("input:text").css("color","#EEE");
            $(the_checkbox).next("input:text").next("input:text").css("width","30px");
        }
    }
}